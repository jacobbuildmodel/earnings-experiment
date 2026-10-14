"""Daily health check - code only, no AI, no rule. Writes ops/health/latest.md and ops/health/<date>.md (one per
day, overwritten by later runs that day) with one status: GREEN, AMBER (look at it) or RED (an event or a decision
is being lost, or is about to be). The workflow opens or comments on one "Health RED" GitHub issue on RED, and
closes it on GREEN.

    python pipeline/health.py [--write] [--commit]

Checks, each mechanical (reviewed by Opus 5.5, 2026-10-13, fixes applied):
  check.py           not exit 0 or last line not PASS                                             -> RED
  snapshot windows   a CONFIRMED event whose snapshot session ended (16:00 ET) with no gate.json in its own
                     folder (<T>_<calendar_date>) -> RED; a missed_window record within 24 h -> RED, older -> info
  stage 1            a PASS gate with no manifest.json after its entry open -> RED (T0, T1 and T2 are lost);
                     a gate of any other status with no manifest after its entry open -> AMBER
  T2 (D004 v4)       PASS event, no manifest_t2.json: past the deadline -> RED "T2 MISSING";
                     less than 14 h to the deadline -> RED "T2 AT RISK"          (deadline from the frozen rule)
  D013 shadows       T2R / T2O missing after the deadline, events entering after 2026-10-13 with a dossier -> AMBER
  Actions            failed / timed-out / startup-failure runs in the last 24 h; S2 window or T2 queue -> RED, else AMBER
  paper ledgers      a halt -> RED; alerts or errors on the last run -> AMBER
  paper exits        a filled position still open on its reaction session 15:15-15:55 ET -> RED (still savable);
                     still open after that -> AMBER (added after the DPZ incident)
  SH-M capture       no shadow/calendar/<today>.json after 12:00 ET on a session -> AMBER
Information: upcoming snapshots, PENDING date confirmations, open paper positions.
"""
import datetime
import glob
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ET, ROOT, now_et  # noqa: E402
from sessions import is_session, shift  # noqa: E402

D = datetime.date.fromisoformat
REPO = os.environ.get("GITHUB_REPOSITORY", "jacobbuildmodel/earnings-experiment")
CRITICAL_WORKFLOWS = ("Earnings experiment - S2 window", "Earnings experiment - T2 queue (D004 v4)")
D013_START = datetime.date(2026, 10, 14)
AT_RISK = datetime.timedelta(hours=14)
LOOKBACK = datetime.timedelta(days=5)


def load(p):
    return json.load(open(p, encoding="utf-8"))


def check_py():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "check.py")], cwd=ROOT, capture_output=True, text=True)
    lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    last = lines[-1] if lines else f"no output (rc {r.returncode}) {r.stderr[-200:]}"
    fails = [ln.strip() for ln in lines if ln.strip().startswith("[FAIL]")]
    return last, fails, r.returncode


def seasons():
    return [os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(ROOT, "universe", "*", "event_status.json"))
            if os.path.basename(os.path.dirname(p)) != "pilot"]


def v4_rule(season):
    """The frozen D004 v4 rule, None if no version covers the season. A damaged rule raises (-> RED)."""
    import t2_stage2
    return t2_stage2.v4(season)


def windows(now):
    red, info = [], []
    for s in seasons():
        st = load(os.path.join(ROOT, "universe", s, "event_status.json")).get("events", {})
        for t, ev in st.items():
            snap = ev.get("snapshot_session")
            if not snap:
                continue
            ended = datetime.datetime.combine(D(snap), datetime.time(16, 0), ET)
            if now < ended or now - ended > LOOKBACK:
                continue
            reason = ev.get("reason") or ev.get("gate_reason") or ""
            if "missed_window" in (reason, ev.get("status")):
                (red if now - ended < datetime.timedelta(hours=24) else info).append(
                    f"MISSED SNAPSHOT WINDOW (recorded): {s} {t} (snapshot {snap})")
                continue
            if ev.get("status") != "CONFIRMED":
                continue
            folder = os.path.join(ROOT, "events", s, f"{t}_{ev.get('calendar_date')}")
            if not os.path.exists(os.path.join(folder, "gate.json")):
                red.append(f"MISSED SNAPSHOT WINDOW: {s} {t} (report {ev.get('calendar_date')}, snapshot {snap}) - no gate.json")
    return red, info


def decisions(now):
    """Every gate of a live season with an entry open within LOOKBACK or still ahead."""
    import t2_stage2
    red, amber, info = [], [], []
    for g in glob.glob(os.path.join(ROOT, "events", "*", "*", "gate.json")):
        edir = os.path.dirname(g)
        season = os.path.basename(os.path.dirname(edir))
        if season == "pilot":
            continue
        gate = load(g)
        try:
            eo = datetime.datetime.combine(D(gate["timing"]["entry"]["session"]), datetime.time(9, 30), ET)
        except (KeyError, TypeError, ValueError):
            amber.append(f"{os.path.basename(edir)}: gate.json without an entry session")
            continue
        if now - eo > LOOKBACK:
            continue
        ev = os.path.basename(edir)
        mp = os.path.join(edir, "manifest.json")
        if not os.path.exists(mp):
            if now >= eo:
                (red if gate.get("status") == "PASS" else amber).append(
                    f"STAGE 1 NOT FROZEN before the entry open: {ev} (gate {gate.get('status')})")
            continue
        man = load(mp)
        if man.get("status") != "PASS":
            continue
        try:
            rule = v4_rule(season)
        except SystemExit as exc:
            red.append(f"D004 rule unreadable for {season}: {exc} - T2 cannot be checked")
            continue
        if not rule:
            continue
        dl = t2_stage2.deadline(rule, gate)
        have = {k: os.path.exists(os.path.join(edir, f)) for k, f in
                (("T2", "manifest_t2.json"), ("T2G", "manifest_t2g.json"), ("T2R", "manifest_t2r.json"),
                 ("T2O", "manifest_t2o.json"))}
        if not have["T2"]:
            if now >= dl:
                red.append(f"T2 MISSING: {ev} (deadline {dl:%a %d %b %H:%M} ET)")
            elif dl - now < AT_RISK:
                red.append(f"T2 AT RISK: {ev} - not frozen, deadline {dl:%a %d %b %H:%M} ET")
        if now >= dl and eo.date() >= D013_START and os.path.exists(os.path.join(edir, "dossier.json")):
            for k in ("T2R", "T2O"):
                if not have[k]:
                    amber.append(f"{k} missing: {ev} (D013 shadow; the budget may have skipped it)")
        if now < dl:
            info.append(f"{ev}: T2 deadline {dl:%a %d %b %H:%M} ET - frozen so far: "
                        + (", ".join(k for k, v in have.items() if v) or "none"))
    return red, amber, info


def actions_failures(now):
    """Runs in the last 24 h that failed, timed out or failed to start. None if the API cannot be read."""
    import requests
    since = (now - datetime.timedelta(hours=24)).astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    h = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        h["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    out = []
    try:
        for page in range(1, 11):
            r = requests.get(f"https://api.github.com/repos/{REPO}/actions/runs",
                             params={"created": f">={since}", "per_page": 100, "page": page}, headers=h, timeout=30)
            if r.status_code != 200:
                return None
            runs = r.json().get("workflow_runs", [])
            out += [(x["name"], x["created_at"], x["html_url"], x.get("conclusion")) for x in runs
                    if x.get("conclusion") in ("failure", "timed_out", "startup_failure")]
            if len(runs) < 100:
                break
    except Exception:
        return None
    return out


def exits(name, led, now):
    """D011 exits (added 2026-10-14 after the DPZ incident). A filled position still open on its reaction session
    between 15:15 and 15:55 ET is RED, while it can still be saved. One still open later is AMBER: the primary exit
    is already lost, and the frozen code keeps retrying until expiry."""
    red, amber = [], []
    today = now.date().isoformat()
    for k, t in led.get("trades", {}).items():
        if "result" in t or t.get("skipped") or not t.get("reaction_session"):
            continue
        o = (t.get("orders") or {}).get("open", [])
        c = (t.get("orders") or {}).get("close", [])
        if not sum(r.get("filled_qty") or 0 for r in o) or sum(r.get("filled_qty") or 0 for r in c):
            continue
        tries = f"{len(c)} close order(s) sent, none filled"
        same_day = t["reaction_session"] == today
        if same_day and datetime.time(15, 15) <= now.time() < datetime.time(15, 55):
            red.append(f"EXIT NOT FILLED: paper/{name} {k} - {tries}; the window closes 15:55 ET")
        elif t["reaction_session"] < today or (same_day and now.time() >= datetime.time(15, 55)):
            amber.append(f"EXIT MISSED: paper/{name} {k} still open after its reaction session "
                         f"{t['reaction_session']} - {tries}; expiry {t.get('expiry')}")
    return red, amber


def ledgers(now):
    red, amber, info = [], [], []
    for name in ("options_ledger.json", "long_ledger.json"):
        p = os.path.join(ROOT, "paper", name)
        if not os.path.exists(p):
            continue
        led = load(p)
        r, a = exits(name, led, now)
        red, amber = red + r, amber + a
        if led.get("halt"):
            red.append(f"paper/{name}: HALT - {led['halt'].get('why')}")
        if led.get("alerts"):
            amber.append(f"paper/{name}: alerts {led['alerts']}")
        if led.get("errors_last_run"):
            amber.append(f"paper/{name}: errors on its last run {led['errors_last_run']}")
        open_ = [k for k, t in led.get("trades", {}).items() if (t.get("orders") or {}).get("open") and "result" not in t
                 and not t.get("skipped") and not t.get("open_failed")]
        if open_:
            info.append(f"paper/{name}: open {open_}")
    return red, amber, info


def capture_check(now):
    d = now.date()
    if not is_session(d) or now.time() < datetime.time(12, 0):
        return None
    return None if os.path.exists(os.path.join(ROOT, "shadow", "calendar", f"{d.isoformat()}.json")) else \
        f"no SH-M calendar capture for {d} yet"


def upcoming(now, n=5):
    out = []
    d = now.date()
    days = [d if is_session(d) else shift(d, 1)]
    for _ in range(n - 1):
        days.append(shift(days[-1], 1))
    for s in seasons():
        st = load(os.path.join(ROOT, "universe", s, "event_status.json")).get("events", {})
        for day in days:
            names = sorted(t for t, ev in st.items() if ev.get("snapshot_session") == day.isoformat())
            if names:
                out.append(f"{day:%a %d %b}: {len(names)} snapshot(s) - {', '.join(names)}")
        out.append(f"{s}: {sum(1 for ev in st.values() if ev.get('status') == 'PENDING')} name(s) still PENDING a confirmed date")
    return out


def run(write=False, commit=False, now=None):
    now = now or now_et()
    red, amber, info = [], [], []
    last, fails, rc = check_py()
    if rc != 0 or not last.startswith("PASS"):
        red.append(f"check.py: {last} {fails}")
    r, i = windows(now)
    red, info = red + r, info + i
    r, a, i = decisions(now)
    red, amber, info = red + r, amber + a, info + i
    fl = actions_failures(now)
    if fl is None:
        amber.append("GitHub Actions status unreadable (API)")
    else:
        for name, when, url, st in fl:
            (red if name in CRITICAL_WORKFLOWS else amber).append(f"Actions {st}: {name} at {when} {url}")
    r, a, i = ledgers(now)
    red, amber, info = red + r, amber + a, info + i
    c = capture_check(now)
    if c:
        amber.append(c)
    info += upcoming(now)
    status = "RED" if red else "AMBER" if amber else "GREEN"
    md = [f"# Health {now:%Y-%m-%d %H:%M} ET - **{status}**", "", f"check.py: {last}", ""]
    for title, xs in (("RED - events or decisions being lost, or about to be", red), ("AMBER - look at", amber),
                      ("Information", info)):
        md.append(f"## {title}")
        md += [f"- {x}" for x in xs] or ["- none"]
        md.append("")
    text = "\n".join(md)
    print(text)
    if write:
        d = os.path.join(ROOT, "ops", "health")
        os.makedirs(d, exist_ok=True)
        for f in ("latest.md", f"{now:%Y-%m-%d}.md"):
            open(os.path.join(d, f), "w", encoding="utf-8", newline="\n").write(text + "\n")
        open(os.path.join(d, "status.txt"), "w", encoding="utf-8", newline="\n").write(status + "\n")
    if commit:
        from freeze import git, push_all
        git("add", "ops/health")
        if git("diff", "--cached", "--name-only"):
            git("commit", "-q", "-m", f"Health {now:%Y-%m-%d %H:%M} ET: {status} (code)\n\n"
                "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
            print(f"pushed: {push_all()}")
    return status, red, amber, info


if __name__ == "__main__":
    a = sys.argv[1:]
    run("--write" in a, "--commit" in a)
