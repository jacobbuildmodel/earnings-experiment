"""Freeze one event before its entry open: hash every file, timestamp, commit, push, prove it came first.

    python pipeline/freeze.py <season> <TICKER> <YYYY-MM-DD>
    python pipeline/freeze.py <season> <TICKER> <YYYY-MM-DD> --t2-missing "<why>"

Rule 1 (CLAUDE.md): the snapshot, theses and all three decisions are hashed and committed BEFORE the entry
open. An eligible event cannot be frozen without decision.json; an ineligible one is frozen without it.

--t2-missing is the fallback when the AI step failed or wrote an invalid decision: T0 (always BUY) and
T1 are still frozen, so the event is not lost to the T0 track; T2 is recorded as missing with the reason,
never guessed. An invalid decision.json is kept as decision_rejected.json, so the failure is on the record.

Proof of time, strongest first:
  1. manifest.tsr_* - RFC 3161 tokens from independent timestamp authorities over the manifest's SHA-256.
     A git commit date is written by the committer and can be set to anything; these cannot.
  2. the push to GitHub, logged by GitHub (the Actions run log records it).
  3. the git commit timestamp.
"""
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ET, ROOT, now_et, rule_for, write_json, write_once  # noqa: E402
from sessions import close_time  # noqa: E402

REQUIRED = ["confirm.json", "gate.json", "option_chain.json", "factors.json"]
# Independent RFC 3161 authorities, all free, all tested 2026-09-21. Two are requested; one is enough.
TSAS = [("digicert", "http://timestamp.digicert.com"), ("freetsa", "https://freetsa.org/tsr"),
        ("sectigo", "http://timestamp.sectigo.com")]
TSA_WANTED = 2


def git(*args, check=True):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if check and r.returncode:
        raise SystemExit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def parse_et(s):
    """An ISO timestamp (with offset) or a bare YYYY-MM-DD, as an aware ET datetime; None if unreadable."""
    if not s:
        return None
    s = str(s).strip()
    try:
        d = datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d.astimezone(ET) if d.tzinfo else d.replace(tzinfo=ET)
    except ValueError:
        pass
    try:
        return datetime.datetime.combine(datetime.date.fromisoformat(s[:10]), datetime.time(0, 0), ET)
    except ValueError:
        return None


def t2_deadline(season, gate):
    """When T2 must have decided. D004 v1 (pilot): before the entry open. D004 v2+: by the close of the
    snapshot session, so T2 cannot see after-hours prints and trading that T1's snapshot never had."""
    entry = datetime.date.fromisoformat(gate["timing"]["entry"]["session"])
    entry_open = datetime.datetime.combine(entry, datetime.time(9, 30), ET)
    try:
        rule = rule_for("D004_decision_protocol", season)
    except SystemExit:  # no JSON twin covers this season -> D004 v1
        return entry_open
    if rule.get("t2_deadline") == "snapshot_session_close":
        snap = datetime.date.fromisoformat(gate["snapshot_session"])
        return datetime.datetime.combine(snap, close_time(snap), ET)
    return entry_open


def decision_problems(d, gate, entry_open):
    """Everything D004 §3 requires of decision.json that code can check. Empty list = valid."""
    p = []
    try:
        if d["t0"]["decision"] != "BUY":
            p.append("T0 must be BUY (it buys every eligible name)")
        t1 = d["t1"]
        if t1["decision"] not in ("BUY", "NO_BUY", None):
            p.append("T1 must be BUY, NO_BUY or null")
        elif t1["decision"] is None and not t1.get("note"):
            p.append("a null T1 needs a note saying why")
        elif t1["decision"] is not None and not t1.get("rule_version"):
            p.append("T1 must name its frozen rule version")
        t2 = d["t2"]
        if t2.get("decision") is None:
            if not t2.get("missing_reason"):
                p.append("a null T2 needs missing_reason")
            return p
        if t2["decision"] not in ("BUY", "NO_BUY"):
            p.append("T2 must be BUY or NO_BUY")
        conf = float(t2["confidence"])
        if not 0 <= conf <= 1:
            p.append("T2 confidence must be in [0, 1]")
        elif t2["decision"] != ("BUY" if conf > 0.5 else "NO_BUY"):
            p.append(f"T2 says {t2['decision']} at confidence {conf}: D004 requires BUY if and only if > 0.5")
        for k in ("thesis", "reasons", "inputs_read", "deciding_variable", "decided_et"):
            if not t2.get(k):
                p.append(f"T2 is missing {k}")
        try:  # D004 v3+: the outside-view prior and the leak probe are required
            required = rule_for("D004_decision_protocol", gate.get("season", "")).get("t2_requires") or []
        except SystemExit:
            required = []
        for k in required:
            if t2.get(k) in (None, "", [], {}):
                p.append(f"T2 is missing {k} (D004 v3)")
        decided = parse_et(t2.get("decided_et"))
        captured = parse_et(gate.get("captured_et"))
        if t2.get("decided_et") and decided is None:
            p.append(f"T2 decided_et is not a timestamp: {t2.get('decided_et')!r}")
        elif decided and captured and decided < captured:
            p.append("T2 decided_et is before the snapshot was captured")
        elif decided and decided >= entry_open:
            p.append(f"T2 decided_et is at or after its deadline {entry_open.isoformat()}")
        # D004: T2 may read nothing published after the snapshot time. An item dated before the snapshot
        # day may give a date only; an item from the snapshot day itself must give its time, and that
        # time must precede captured_et (external review 2026-09-21: a day-level check let same-day,
        # post-snapshot news through).
        for item in t2.get("inputs_read") or []:
            if not isinstance(item, dict) or not item.get("published"):
                p.append(f"input without a published date: {item}")
                continue
            raw = str(item["published"]).strip()
            pub = parse_et(raw)
            if pub is None:
                p.append(f"input published date is unreadable: {item}")
            elif captured and pub.date() > captured.date():
                p.append(f"input published after the snapshot: {item}")
            elif captured and pub.date() == captured.date():
                if len(raw) <= 10:
                    p.append(f"input from the snapshot day needs a time, not just a date: {item}")
                elif pub >= captured:
                    p.append(f"input published after the snapshot time: {item}")
    except (KeyError, TypeError, ValueError) as exc:
        p.append(f"decision.json is malformed: {type(exc).__name__}: {exc}")
    return p


def timestamp(digest_hex, edir):
    """RFC 3161 tokens over the manifest digest. Best effort: a failed authority is reported, never fatal."""
    got, errors = [], []
    q = os.path.join(edir, "manifest.tsq")
    r = subprocess.run(["openssl", "ts", "-query", "-digest", digest_hex, "-sha256", "-cert", "-out", q],
                       capture_output=True, text=True)
    if r.returncode:
        return [], [f"openssl: {r.stderr.strip() or 'not available'}"]
    body = open(q, "rb").read()
    os.remove(q)
    for name, url in TSAS:
        if len(got) == TSA_WANTED:
            break
        try:
            resp = requests.post(url, data=body, timeout=20,
                                 headers={"Content-Type": "application/timestamp-query"})
            if resp.status_code != 200 or len(resp.content) < 100:
                errors.append(f"{name}: HTTP {resp.status_code}")
                continue
            fname = f"manifest.tsr_{name}"
            open(os.path.join(edir, fname), "wb").write(resp.content)
            got.append(fname)
        except requests.RequestException as exc:
            errors.append(f"{name}: {type(exc).__name__}")
    return got, errors


def push_all():
    """Push HEAD to every remote. On a non-fast-forward, MERGE the remote in and push again. Never rebase:
    a rebase rewrites the freeze commit and its timestamp, which is the thing being proven."""
    results = {}
    for remote in git("remote").split():
        ok = subprocess.run(["git", "push", "-q", remote, "HEAD:main"], cwd=ROOT).returncode == 0
        if not ok:
            merged = subprocess.run(["git", "pull", "-q", "--no-rebase", "--no-edit", remote, "main"],
                                    cwd=ROOT).returncode == 0
            ok = merged and subprocess.run(["git", "push", "-q", remote, "HEAD:main"], cwd=ROOT).returncode == 0
        results[remote] = ok
    return results


def t1_by_code(season, edir):
    """T1 from the frozen rule for this season, computed from the event's own factors.json; None where no
    rule applies (the pilot), so pilot decisions are untouched."""
    from t1_rule import FACTORS, decide
    probe = decide({}, season)
    if probe.get("decision") is None and "rule_version" not in probe:
        return None  # no frozen rule covers this season
    f = json.load(open(os.path.join(edir, "factors.json"), encoding="utf-8"))
    sheet = f.get("factors") or {}
    return decide({k: (sheet.get(k) or {}).get("value") for k in FACTORS}, season)


def run(season, ticker, report_date, t2_missing=None):
    ticker = ticker.upper()
    rel = os.path.join("events", season, f"{ticker}_{report_date}").replace("\\", "/")
    edir = os.path.join(ROOT, rel)
    if os.path.exists(os.path.join(edir, "manifest.json")):
        raise SystemExit(f"{rel} is already frozen - a frozen event is never re-frozen")
    for f in REQUIRED:
        if not os.path.exists(os.path.join(edir, f)):
            raise SystemExit(f"missing {f} - nothing is frozen")
    gate = json.load(open(os.path.join(edir, "gate.json"), encoding="utf-8"))
    if gate.get("dry"):
        raise SystemExit("a dry-run gate can never be frozen")

    entry = gate["timing"]["entry"]["session"]
    entry_open = datetime.datetime.combine(datetime.date.fromisoformat(entry), datetime.time(9, 30), ET)
    if now_et() >= entry_open:
        raise SystemExit(f"ET {now_et():%Y-%m-%d %H:%M} is at or after the entry open {entry_open} - VOID, not late")

    files = list(REQUIRED)
    dpath = os.path.join(edir, "decision.json")
    rejected = os.path.join(edir, "decision_rejected.json")
    notes = []
    t1_code = t1_by_code(season, edir)
    if gate["status"] != "PASS":
        if os.path.exists(dpath):  # D004: never a decision for an event that failed the gate
            shutil.move(dpath, rejected)
            notes.append("decision.json written for an INELIGIBLE event - kept as decision_rejected.json")
    else:
        deadline = min(entry_open, t2_deadline(season, gate))
        if t1_code and os.path.exists(dpath):
            # D004 v3: T1 is code's, never the AI's. Whatever the AI wrote for t1 is replaced, and noted.
            d = json.load(open(dpath, encoding="utf-8"))
            if d.get("t1") != t1_code:
                notes.append(f"t1 set by code (t1_rule.py); the AI's t1 was {d.get('t1')!r}")
                d["t1"] = t1_code
                write_json(dpath, d)
        problems = decision_problems(json.load(open(dpath, encoding="utf-8")), gate, deadline) \
            if os.path.exists(dpath) else ["no decision.json"]
        if problems and not t2_missing:
            raise SystemExit("decision.json is not valid - fix it, or freeze with --t2-missing \"<why>\":\n  - "
                             + "\n  - ".join(problems))
        if problems or t2_missing:
            if os.path.exists(dpath):
                shutil.move(dpath, rejected)
            reason = t2_missing or "; ".join(problems)
            write_json(dpath, {"t0": {"decision": "BUY"},
                               "t1": t1_code or {"decision": None, "note": "rule v0 not frozen - pilot"},
                               "t2": {"decision": None, "missing_reason": reason, "recorded_et": now_et().isoformat()}})
            notes.append(f"T2 frozen as MISSING: {reason}")
        files.append("decision.json")
    for extra in ("thesis.md", "decision_rejected.json"):
        if os.path.exists(os.path.join(edir, extra)):
            files.append(extra)

    now = now_et()
    manifest = {"event": f"{ticker}_{report_date}", "season": season, "status": gate["status"],
                "reason": gate.get("reason"), "frozen_et": now.isoformat(), "entry_open_et": entry_open.isoformat(),
                "notes": notes, "sha256": {}}
    for f in files:
        data = open(os.path.join(edir, f), "rb").read().replace(b"\r\n", b"\n")
        manifest["sha256"][f] = hashlib.sha256(data).hexdigest()
    write_once(os.path.join(edir, "manifest.json"), manifest)
    mdigest = hashlib.sha256(open(os.path.join(edir, "manifest.json"), "rb").read().replace(b"\r\n", b"\n")).hexdigest()
    tokens, tsa_errors = timestamp(mdigest, edir)

    git("add", *[f"{rel}/{f}" for f in files + ["manifest.json"] + tokens])
    git("commit", "-q", "-m", f"Freeze {ticker} {report_date} ({gate['status']}) before entry open {entry}\n\n"
        f"manifest sha256 {mdigest}\n\nCo-Authored-By: Claude Opus 5 <noreply@anthropic.com>")
    commit_time = datetime.datetime.fromisoformat(git("log", "-1", "--format=%cI"))
    sha = git("rev-parse", "--short", "HEAD")
    pushes = push_all()
    ok = commit_time < entry_open
    for n in notes:
        print(f"NOTE: {n}")
    print(f"{ticker} {report_date}: {gate['status']} frozen in {sha} at {commit_time.astimezone(ET):%Y-%m-%d %H:%M:%S} ET"
          f" - entry open {entry_open:%Y-%m-%d %H:%M} ET - {'BLIND (before open)' if ok else 'VOID (after open)'}"
          f" - timestamps: {', '.join(tokens) or 'NONE'}"
          f" - push: {', '.join(f'{r} ' + ('ok' if v else 'FAILED') for r, v in pushes.items()) or 'NO REMOTE'}")
    if tsa_errors:
        print(f"WARNING: timestamp authority errors: {tsa_errors}")
    if not any(pushes.values()):
        print("WARNING: the freeze exists only in this checkout - push it before the entry open")
    if not ok or not any(pushes.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    a = sys.argv[1:]
    why = a[a.index("--t2-missing") + 1] if "--t2-missing" in a else None
    run(a[0], a[1], a[2], t2_missing=why)
