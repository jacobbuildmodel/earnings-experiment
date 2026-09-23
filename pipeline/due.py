"""The deterministic half of every S2 run. No AI here: gating is time-critical and must not depend on
an agent following a prompt.

    python pipeline/due.py gate                 # gate + factor snapshot for every event due now
    python pipeline/due.py plan [--schedule S]  # prints GitHub step outputs: claude=, housekeeping=, last_chance=
    python pipeline/due.py t2-list              # events awaiting a T2 decision, one "<season> <TICKER> <date>" per line
    python pipeline/due.py finalize [--last-chance]
    python pipeline/due.py midseason            # Fridays: D003 §7 mid-season screen, committed
    python pipeline/due.py init-status <season> # after a season screen: every candidate PENDING

gate      For each CONFIRMED event whose snapshot session is today (ET) and has no gate.json:
          inside 14:30-15:50 ET, run s2_gate.py and factors.py. An INELIGIBLE event is frozen at once
          (it needs no decision). A PASS event's capture is committed and pushed straight away, so a later
          run can finish it if this one dies. After 15:50 with no gate.json the event is marked
          INELIGIBLE missed_window. Never back-dated, never faked.
finalize  Freezes every PASS event that has a valid decision.json but no freeze (an AI run that wrote
          its decision and then failed). With --last-chance (the day's final run), a PASS event still
          without a valid decision is frozen with T2 MISSING, so T0 keeps the event. Then the status file
          is brought in line with the frozen record, committed and pushed.

The freeze deadline is the entry open (the next morning), not the end of the S2 window, which is why the
day's last run can still finish an event.
"""
import datetime
import glob
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ET, ROOT, now_et, rule_for, write_json  # noqa: E402
from sessions import s2_window  # noqa: E402
from freeze import decision_problems, git, push_all, t2_deadline  # noqa: E402

PY = sys.executable
# UTC cron of the day's housekeeping + last-chance run (see .github/workflows/s2-window.yml).
HOUSEKEEPING_CRON = "0 23 * * 1-5"


def status_files():
    return sorted(glob.glob(os.path.join(ROOT, "universe", "*", "event_status.json")))


def load(path):
    return json.load(open(path, encoding="utf-8"))


def edir(season, key, ev):
    date = ev.get("calendar_date") or ev.get("report_date")
    return os.path.join(ROOT, "events", season, f"{key}_{date}"), date


def entry_open(gate):
    d = datetime.date.fromisoformat(gate["timing"]["entry"]["session"])
    return datetime.datetime.combine(d, datetime.time(9, 30), ET)


def sh(*args):
    r = subprocess.run([PY, *args], cwd=ROOT, capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode:
        print(r.stderr.strip()[-2000:])
    return r.returncode


def rel(path):
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


def commit(paths, message):
    paths = [rel(p) for p in paths if os.path.exists(p)]
    git("add", *paths)
    if not git("diff", "--cached", "--name-only"):
        return False
    git("commit", "-q", "-m", message + "\n\nCo-Authored-By: Claude Opus 5 <noreply@anthropic.com>")
    print(f"pushed: {push_all()}")
    return True


def due_today():
    """Every ungated CONFIRMED event whose snapshot session is today, with its S2 window."""
    now = now_et()
    today = now.date().isoformat()
    out = []
    for sf in status_files():
        st = load(sf)
        season = st["season"]
        rule = rule_for("D003_universe_screen", season)
        lo, hi = (datetime.datetime.combine(now.date(), t, ET) for t in s2_window(now.date(), rule["s2"]))
        for key, ev in st["events"].items():
            if ev.get("status") != "CONFIRMED" or ev.get("snapshot_session") != today:
                continue
            d, date = edir(season, key, ev)
            if os.path.exists(os.path.join(d, "gate.json")):
                continue
            out.append((lo, hi, key, date))
    return out


# A run that arrives this long before the window opens holds the runner until it does.
MAX_WAIT_MINUTES = 240


def wait_for_window(max_minutes=MAX_WAIT_MINUTES):
    """Sleep until the S2 window opens, when an ungated event is due today.

    THE TRIGGER CANNOT BE TRUSTED TO LAND INSIDE THE WINDOW. On 2026-09-21 and 09-22 GitHub produced
    no run at all between 18:30 and 19:50 UTC - it dropped both in-window fires on both days - and ran
    the remaining fires 20 to 145 minutes late. PAYX, DRI and BB were lost that way, with nothing
    wrong in this pipeline. Waiting changes the requirement from "a fire must land inside an 80-minute
    window" to "a fire must land somewhere in the four hours before it", which the same run history
    shows is reliable. It costs runner minutes only on days when an event is actually due.
    """
    due = due_today()
    if not due:
        print("wait: nothing ungated is due today")
        return
    lo, hi = min(d[0] for d in due), max(d[1] for d in due)
    names = ", ".join(f"{k} {d}" for _, _, k, d in due)
    now = now_et()
    if now >= hi:
        print(f"wait: the window ({lo:%H:%M}-{hi:%H:%M} ET) has closed - gate() will record missed_window")
        return
    if now >= lo:
        print(f"wait: window already open ({lo:%H:%M}-{hi:%H:%M} ET), gating {names} now")
        return
    seconds = (lo - now).total_seconds() + 60
    if seconds > max_minutes * 60:
        print(f"wait: window opens {lo:%H:%M} ET in {seconds / 60:.0f} min - beyond the {max_minutes} min "
              f"cap, leaving it to a later fire")
        return
    print(f"wait: holding this runner {seconds / 60:.1f} min, until {lo:%H:%M} ET + 1 min, to gate {names}",
          flush=True)
    time.sleep(seconds)
    print(f"wait: window open at {now_et():%H:%M:%S} ET - continuing", flush=True)


def gate():
    now = now_et()
    today = now.date().isoformat()
    for sf in status_files():
        st = load(sf)
        season = st["season"]
        changed = False
        rule = rule_for("D003_universe_screen", season)
        lo, hi = (datetime.datetime.combine(now.date(), t, ET) for t in s2_window(now.date(), rule["s2"]))
        for key, ev in st["events"].items():
            if ev.get("status") != "CONFIRMED" or ev.get("snapshot_session") != today:
                continue
            d, date = edir(season, key, ev)
            if os.path.exists(os.path.join(d, "gate.json")):
                continue
            if now < lo:
                print(f"{key} {date}: due today, window opens {lo:%H:%M} ET - later run")
                continue
            if now > hi:
                ev.update(status="INELIGIBLE", reason="missed_window",
                          missed_note=f"no gate.json by the end of the S2 window; checked {now.isoformat()}")
                changed = True
                print(f"{key} {date}: MISSED the S2 window - INELIGIBLE missed_window")
                continue
            if not os.path.exists(os.path.join(d, "confirm.json")):
                print(f"{key} {date}: CONFIRMED but no confirm.json - cannot gate")
                continue
            print(f"--- gating {key} {date}")
            if sh("pipeline/s2_gate.py", season, key, date) or not os.path.exists(os.path.join(d, "gate.json")):
                print(f"{key} {date}: s2_gate.py failed - a later run in the window will retry")
                continue
            if sh("pipeline/factors.py", season, key, date) or not os.path.exists(os.path.join(d, "factors.json")):
                # factors.py records failed blocks itself; a crash of the whole script leaves a stub so
                # the event can still be frozen, with the failure on the record.
                write_json(os.path.join(d, "factors.json"),
                           {"meta": {"ticker": key, "report_date": date, "captured_et": now_et().isoformat()},
                            "error": "factors.py crashed - no factor snapshot", "factors": {}})
            if not os.path.exists(os.path.join(d, "option_chain.json")):
                write_json(os.path.join(d, "option_chain.json"), {"error": "s2_gate.py wrote no chain"})
            g = load(os.path.join(d, "gate.json"))
            files = [os.path.join(d, f) for f in ("confirm.json", "gate.json", "option_chain.json", "factors.json")]
            if g["status"] != "PASS":
                sh("pipeline/freeze.py", season, key, date)
            else:
                commit(files, f"Capture {key} {date}: S2 gate PASS and factor snapshot - awaiting T2")
        if changed:  # committed by finalize, which always runs after this step
            write_json(sf, st)


def awaiting_t2():
    out = []
    for g in sorted(glob.glob(os.path.join(ROOT, "events", "*", "*", "gate.json"))):
        d = os.path.dirname(g)
        if os.path.exists(os.path.join(d, "manifest.json")):
            continue
        gj = load(g)
        if gj.get("dry") or gj["status"] != "PASS" or now_et() >= entry_open(gj):
            continue
        season = os.path.basename(os.path.dirname(d))
        out.append((season, gj["ticker"], gj["report_date"], d, gj))
    return out


def plan(schedule):
    t2 = [e for e in awaiting_t2() if now_et() < t2_deadline(e[0], e[4])]  # only events T2 may still decide
    housekeeping = schedule in ("", HOUSEKEEPING_CRON)  # "" = started by hand
    print(f"claude={'true' if (t2 or housekeeping) else 'false'}")
    print(f"housekeeping={'true' if housekeeping else 'false'}")
    print(f"last_chance={'true' if schedule == HOUSEKEEPING_CRON else 'false'}")
    print(f"t2_events={' ; '.join(f'{s} {t} {d}' for s, t, d, _, _ in t2)}")


def finalize(last_chance):
    for season, t, date, d, gj in awaiting_t2():
        dp = os.path.join(d, "decision.json")
        deadline = min(entry_open(gj), t2_deadline(season, gj))
        valid = os.path.exists(dp) and not decision_problems(load(dp), gj, deadline)
        if valid:
            print(f"--- {t} {date}: valid decision, not frozen - freezing")
            sh("pipeline/freeze.py", season, t, date)
        elif last_chance or now_et() >= deadline:
            why = ("no valid T2 decision by " + ("its deadline " + deadline.strftime("%Y-%m-%d %H:%M ET")
                   if now_et() >= deadline else "the day's last run (" + now_et().strftime("%Y-%m-%d %H:%M ET") + ")"))
            print(f"--- {t} {date}: {why} - freezing with T2 MISSING")
            sh("pipeline/freeze.py", season, t, date, "--t2-missing", why)
        else:
            print(f"--- {t} {date}: awaiting T2 - a later run will decide")
    # A systemic AI failure must not hide behind the T2-MISSING fallback (external review 2026-09-21).
    recent = []
    for m in sorted(glob.glob(os.path.join(ROOT, "events", "*", "*", "manifest.json")),
                    key=lambda p: load(p)["frozen_et"])[-5:]:
        man = load(m)
        if man["status"] == "PASS":
            dec = load(os.path.join(os.path.dirname(m), "decision.json"))
            recent.append(dec["t2"].get("decision") is None)
    if len(recent) >= 2 and sum(recent) >= 2:
        print(f"::warning::T2 was MISSING on {sum(recent)} of the last {len(recent)} eligible events - check the AI step")
    # bring every status file in line with the frozen record
    for sf in status_files():
        st = load(sf)
        before = json.dumps(st, sort_keys=True)
        season = st["season"]
        for key, ev in st["events"].items():
            d, date = edir(season, key, ev)
            mp = os.path.join(d, "manifest.json")
            if not os.path.exists(mp):
                continue
            man = load(mp)
            dec = load(os.path.join(d, "decision.json")).get("t2", {}) if "decision.json" in man["sha256"] else {}
            ev.update(status="FROZEN", gate_status=man["status"], gate_reason=man.get("reason"),
                      frozen_et=man["frozen_et"], t2_decision=dec.get("decision"), t2_confidence=dec.get("confidence"),
                      freeze_commit=git("log", "--diff-filter=A", "--format=%h", "--", rel(mp)))
        if json.dumps(st, sort_keys=True) != before or git("status", "--porcelain", "--", rel(sf)):
            st["updated_et"] = now_et().isoformat()
            write_json(sf, st)
            commit([sf], f"Status: {season} event statuses from the frozen record")


def midseason():
    """D003 §7, Fridays: run the mid-season screen for every active season and commit what it wrote."""
    if now_et().weekday() != 4:
        print("not a Friday - no mid-season screen")
        return
    sh("pipeline/s1_screen.py", "active", "midseason")
    paths = glob.glob(os.path.join(ROOT, "universe", "*", "midseason", "*.json"))
    paths += glob.glob(os.path.join(ROOT, "universe", "*", "candidates_midseason.json")) + status_files()
    commit(paths, f"Mid-season screen {now_et().date()} (D003 §7, code)")


def init_status(season):
    """After a season screen: one PENDING entry per candidate, with its calendar dates, so the daily
    housekeeping run looks for each company's own announcement (D003 §6). Never overwrites a status file."""
    base = os.path.join(ROOT, "universe", season)
    sp = os.path.join(base, "event_status.json")
    if os.path.exists(sp):
        print(f"{sp} exists - not touched")
        return
    cands = load(os.path.join(base, "candidates.json"))["candidates"]
    events = {}
    for c in cands:
        dates = sorted({x["date"] for src in c["calendar"].values() for x in src})
        events[c["ticker"]] = {"status": "PENDING", "calendar_dates": dates,
                               "note": "needs a company date + session (D003 §6) and a second source"}
    write_json(sp, {"season": season, "rule": rule_for("D003_universe_screen", season)["id"],
                    "updated_et": now_et().isoformat(), "events": events})
    commit([sp], f"{season}: event statuses initialised from the season screen ({len(events)} PENDING)")


if __name__ == "__main__":
    a = sys.argv[1:]
    cmd = a[0] if a else ""
    if cmd == "gate":
        gate()
    elif cmd == "wait":
        wait_for_window(int(a[a.index("--max-minutes") + 1]) if "--max-minutes" in a else MAX_WAIT_MINUTES)
    elif cmd == "due-today":
        for lo, hi, key, date in due_today():
            print(f"{key} {date} window {lo:%H:%M}-{hi:%H:%M} ET")
    elif cmd == "plan":
        plan(a[a.index("--schedule") + 1] if "--schedule" in a and len(a) > a.index("--schedule") + 1 else "")
    elif cmd == "t2-list":
        for s, t, d, _, _ in awaiting_t2():
            print(s, t, d)
    elif cmd == "init-status":
        init_status(a[1])
    elif cmd == "midseason":
        midseason()
    elif cmd == "finalize":
        finalize("--last-chance" in a)
    else:
        raise SystemExit(__doc__)
