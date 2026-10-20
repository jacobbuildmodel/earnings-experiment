"""Housekeeping records, written by code for the AI (ops/actions_prompt.md section B; the cloud routine
`earnings-housekeeping-cloud`, ops/cloud_housekeeping_prompt.md). The AI reads company pages; this file writes
universe/<season>/event_status.json, confirm.json and the STATE.md Cloud run log, and refuses what D003 §6 refuses.

    python pipeline/hk.py worklist [--max N]                 # PENDING names, most urgent first, with code's last note
    python pipeline/hk.py confirm <T> <YYYY-MM-DD> <BMO|AMC> <url> <published_et> "<title>" "<quote>" [--call-time]
    python pipeline/hk.py retire <T> unconfirmed|outside_window "<why>"
    python pipeline/hk.py note <T> "<what the re-check showed>"
    python pipeline/hk.py log "<one line for today>"

- confirm: the snapshot session must still be ahead (today only before the window opens - 5 min), the date inside
  the season window, and a second source must agree with date AND session now (s2_gate.votes, the gate's own rule).
- retire unconfirmed: only once every snapshot session its calendar dates allow has passed.
2026-10-20: written when the Actions AI step was refused ("organization has disabled Claude subscription access")."""
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, now_et, rule_for, write_json  # noqa: E402

SEASON = "seasonA"


def status_path(season=SEASON):
    return os.path.join(ROOT, "universe", season, "event_status.json")


def snaps(date, rule):
    """Snapshot sessions for a report date, BMO and AMC."""
    from sessions import shift
    d = datetime.date.fromisoformat(date)
    out = {}
    for s, n in rule["s2"]["snapshot_session"].items():
        try:
            out[s] = shift(d, n)
        except ValueError:
            pass
    return out


def passed(snap, rule, now):
    import find_dates as fd
    today = now.date()
    return snap < today or (snap == today and now >= fd.window_open(today, rule) - datetime.timedelta(minutes=5))


def worklist(st, rule, now, n=25):
    rows = []
    for k, e in st["events"].items():
        if e.get("status") != "PENDING":
            continue
        dates = e.get("calendar_dates") or ["9999-12-31"]
        last = (e.get("rechecks") or [""])[-1]
        rows.append((min(dates), k, last[:220]))
    return sorted(rows)[:n]


def confirm(st, t, date, session, url, pub, title, quote, call, rule, now, season=SEASON):
    import find_dates as fd
    e = st["events"][t]
    if e.get("status") != "PENDING":
        raise SystemExit(f"{t}: status {e.get('status')}, not PENDING")
    if session not in ("BMO", "AMC"):
        raise SystemExit(f"{t}: session must be BMO or AMC")
    lo, hi = rule["seasons"][season]["window"]
    if not lo <= date <= hi:
        raise SystemExit(f"{t}: {date} is outside the season window {lo}..{hi} - retire it outside_window instead")
    snap = snaps(date, rule).get(session)
    if snap is None:
        raise SystemExit(f"{t}: {date} is not a session")
    stamp = now.isoformat(timespec="seconds")
    if passed(snap, rule, now):
        raise SystemExit(f"{t}: snapshot {snap} has passed - cannot confirm")
    ok, seconds = fd.second_source_agrees(t, date, session)
    if not ok:
        e.setdefault("rechecks", []).append(f"{stamp}: housekeeping - company states {date} {session} ({url}) but no "
                                           f"second source agrees yet ({seconds}) - left PENDING")
        return f"{t}: no second source agrees {seconds} - left PENDING (noted)"
    cpath = os.path.join(ROOT, "events", season, f"{t}_{date}", "confirm.json")
    if os.path.exists(cpath):
        raise SystemExit(f"{t}: {cpath} exists")
    write_json(cpath, {"session": session, "session_from_call_time": call,
                       "company_source": {"url": url, "published_et": pub, "quote": quote, "title": title,
                                          "retrieved_et": stamp,
                                          "how": "housekeeping (pipeline/hk.py), read from the company's own release; "
                                                 "the quote is the sentence stating date and session"},
                       "second_sources_at_confirm": seconds})
    from sessions import shift
    e.update(status="CONFIRMED", calendar_date=date, session=session, snapshot_session=snap.isoformat(),
             entry=f"{shift(datetime.date.fromisoformat(date), rule['s2']['snapshot_session'][session] + 1)} open",
             flags=sorted(set(e.get("flags", []) + (["session_from_call_time"] if call else []))))
    e.setdefault("rechecks", []).append(f"{stamp}: housekeeping - company statement ({url}); CONFIRMED {date} {session}, "
                                       f"snapshot {snap}")
    return f"{t}: CONFIRMED {date} {session}, snapshot {snap} -> {cpath}"


def retire(st, t, reason, why, rule, now):
    e = st["events"][t]
    if e.get("status") != "PENDING":
        raise SystemExit(f"{t}: status {e.get('status')}, not PENDING")
    if reason not in ("unconfirmed", "outside_window"):
        raise SystemExit("reason must be unconfirmed or outside_window")
    if reason == "unconfirmed":
        dates = e.get("calendar_dates") or []
        open_ = [f"{d} {s} -> {v}" for d in dates for s, v in snaps(d, rule).items() if not passed(v, rule, now)]
        if not dates or open_:
            raise SystemExit(f"{t}: a snapshot session is still ahead ({open_ or 'no calendar date'}) - not retired")
    e.update(status="INELIGIBLE", reason=reason)
    e.setdefault("rechecks", []).append(f"{now.isoformat(timespec='seconds')}: housekeeping - INELIGIBLE {reason}: {why}")
    return f"{t}: INELIGIBLE {reason}"


def log_line(text, now, state=None):
    p = state or os.path.join(ROOT, "STATE.md")
    s = open(p, encoding="utf-8").read()
    if "## Cloud run log" not in s:
        raise SystemExit("STATE.md has no Cloud run log section")
    line = f"- **{now:%Y-%m-%d (%a)}, housekeeping {now:%H:%M} ET:** {re.sub(r'\s+', ' ', text).strip()}\n"
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s.rstrip("\n") + "\n" + line)
    return line


def main(a):
    rule, now = rule_for("D003_universe_screen", SEASON), now_et()
    if a[0] == "log":
        print(log_line(a[1], now), end="")
        return
    st = json.load(open(status_path(), encoding="utf-8"))
    if a[0] == "worklist":
        n = int(a[a.index("--max") + 1]) if "--max" in a else 25
        for d, k, last in worklist(st, rule, now, n):
            print(f"{d}  {k:6}  {last}")
        return
    t = a[1].upper()
    if a[0] == "note":
        st["events"][t].setdefault("rechecks", []).append(f"{now.isoformat(timespec='seconds')}: housekeeping - {a[2]}")
        msg = f"{t}: noted"
    elif a[0] == "retire":
        msg = retire(st, t, a[2], a[3], rule, now)
    elif a[0] == "confirm":
        msg = confirm(st, t, a[2], a[3], a[4], a[5], a[6], a[7], "--call-time" in a, rule, now)
    else:
        raise SystemExit(__doc__)
    st["updated_et"] = now.isoformat()
    write_json(status_path(), st)
    print(msg)


if __name__ == "__main__":
    main(sys.argv[1:] or ["--help"])
