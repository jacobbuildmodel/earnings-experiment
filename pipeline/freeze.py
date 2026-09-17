"""Freeze one event before its entry open: hash every file, commit, push, prove the commit came first.

    python pipeline/freeze.py <season> <TICKER> <YYYY-MM-DD>

Rule 1 (CLAUDE.md): the snapshot, theses and all three decisions are hashed and committed BEFORE the entry
open. An eligible event cannot be frozen without decision.json; an ineligible one is frozen without it.
"""
import datetime
import hashlib
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ET, ROOT, now_et, write_once  # noqa: E402

REQUIRED = ["confirm.json", "gate.json", "option_chain.json", "factors.json"]


def git(*args):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def check_decision(d):
    assert d["t0"]["decision"] == "BUY", "T0 buys every eligible name"
    assert d["t1"]["decision"] in ("BUY", "NO_BUY", None), "T1 is BUY, NO_BUY or null (no frozen rule)"
    if d["t1"]["decision"] is None:
        assert d["t1"].get("note"), "a null T1 needs a note saying why"
    else:
        assert d["t1"].get("rule_version"), "T1 names its frozen rule version"
    t2 = d["t2"]
    assert t2["decision"] in ("BUY", "NO_BUY"), "T2 is BUY or NO_BUY"
    assert 0 <= float(t2["confidence"]) <= 1, "T2 confidence in [0, 1]"
    assert t2.get("thesis") and t2.get("reasons") and t2.get("inputs_read"), "T2 needs thesis, reasons, inputs_read"


def run(season, ticker, report_date):
    ticker = ticker.upper()
    rel = os.path.join("events", season, f"{ticker}_{report_date}")
    edir = os.path.join(ROOT, rel)
    for f in REQUIRED:
        if not os.path.exists(os.path.join(edir, f)):
            raise SystemExit(f"missing {f} - nothing is frozen")
    gate = json.load(open(os.path.join(edir, "gate.json"), encoding="utf-8"))
    if gate.get("dry"):
        raise SystemExit("a dry-run gate can never be frozen")
    files = list(REQUIRED)
    if gate["status"] == "PASS":
        if not os.path.exists(os.path.join(edir, "decision.json")):
            raise SystemExit("eligible event without decision.json - write T0/T1/T2 first")
        check_decision(json.load(open(os.path.join(edir, "decision.json"), encoding="utf-8")))
        files.append("decision.json")
    for extra in ("thesis.md",):
        if os.path.exists(os.path.join(edir, extra)):
            files.append(extra)

    entry = gate["timing"]["entry"]["session"]
    entry_open = datetime.datetime.combine(datetime.date.fromisoformat(entry), datetime.time(9, 30), ET)
    now = now_et()
    if now >= entry_open:
        raise SystemExit(f"ET {now:%Y-%m-%d %H:%M} is at or after the entry open {entry_open} - VOID, not late")

    manifest = {"event": f"{ticker}_{report_date}", "season": season, "status": gate["status"],
                "reason": gate.get("reason"), "frozen_et": now.isoformat(), "entry_open_et": entry_open.isoformat(),
                "sha256": {}}
    for f in files:
        data = open(os.path.join(edir, f), "rb").read().replace(b"\r\n", b"\n")
        manifest["sha256"][f] = hashlib.sha256(data).hexdigest()
    write_once(os.path.join(edir, "manifest.json"), manifest)

    git("add", *[f"{rel}/{f}".replace("\\", "/") for f in files + ["manifest.json"]])
    git("commit", "-q", "-m", f"Freeze {ticker} {report_date} ({gate['status']}) before entry open {entry}\n\n"
        "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>")
    commit_time = datetime.datetime.fromisoformat(git("log", "-1", "--format=%cI"))
    sha = git("rev-parse", "--short", "HEAD")
    pushed = subprocess.run(["git", "push", "-q", "local", "main"], cwd=ROOT).returncode == 0
    ok = commit_time < entry_open
    print(f"{ticker} {report_date}: {gate['status']} frozen in {sha} at {commit_time.astimezone(ET):%Y-%m-%d %H:%M:%S} ET"
          f" - entry open {entry_open:%Y-%m-%d %H:%M} ET - {'BLIND (before open)' if ok else 'VOID (after open)'}"
          f" - backup {'pushed' if pushed else 'PUSH FAILED'}")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2], sys.argv[3])
