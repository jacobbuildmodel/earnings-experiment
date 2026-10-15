"""D014 descriptive control (no test, no rule): the cost of entering at the open on ordinary days, for the same names.
Asked by the DRIVE chat via Jacob, 2026-10-14: how much of the ~0.8% market-order-at-the-open cost found by D014 v3 is
the print, and how much is the open itself?

Method, fixed before any control-day number was fetched:
- For each non-void D014 v1 event (ticker, reaction session R), the control day is the session 10 sessions before R
  on SPY's calendar. It is dropped if any D006 reaction session of the same ticker lies within 3 sessions of it.
- On the control day, exactly v1/v3's definitions: the official open O (the largest opening-auction print at or after
  09:30), the first regular minute at or after the open's minute and its VWAP, the first NBBO quote at or after the
  open (half-spread hs_first), and the last quote at or before 09:35 (hs_0935).
- The same four numbers on the print day come from D014's own files (events_intraday, events_v3).
- Reported for both: the median and mean of hs_first, hs_0935, |VWAP / O - 1|, and the two-sided market-order
  penalty against the official open: a buy pays VWAP(1 + hs)/O - 1, a short sale 1 - VWAP(1 - hs)/O; their average
  is hs_first * VWAP/O. (On print days D014 v3 signed the penalty by the trade's direction, which also carries the
  drift from the auction to the first minute; this two-sided version is computed for both day types alike.)
  Split by mid-cap (< $10B) and large.
Alpaca market data (free plan, feed sip, adjustment raw). Writes analysis/d014/control_days.json and CONTROL.md.

    python analysis/d014/control_days.py [--commit]
"""
import csv
import datetime
import gzip
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fetch  # noqa: E402
import fetch_v3  # noqa: E402

ROOT = fetch.ROOT


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def control_rows(rows, sessions, prints):
    out = []
    for r in rows:
        day = datetime.date.fromisoformat(r["R"])
        if day not in sessions:
            continue
        i = sessions.index(day)
        c = sessions[i - 10]
        near = [p for p in prints.get(r["ticker"], []) if p in sessions
                and abs(sessions.index(p) - sessions.index(c)) <= 3]
        if not near:
            out.append({"ticker": r["ticker"], "R": r["R"], "C": c, "mcap": num(r.get("mcap"))})
    return out


def measure_day(day, evs):
    syms = sorted({e["ticker"] for e in evs})
    auc = fetch.paged("auctions", {"symbols": ",".join(syms), "feed": "sip", "start": day.isoformat(),
                                   "end": fetch.utc(day, "20:00"), "limit": 10000}, "auctions")
    bars = fetch.paged("bars", {"symbols": ",".join(syms), "timeframe": "1Min", "feed": "sip", "adjustment": "raw",
                                "limit": 10000, "start": fetch.utc(day, "09:30"), "end": fetch.utc(day, "09:50")}, "bars")
    out = []
    for e in evs:
        o, o_t = fetch.auction(auc, e["ticker"], day, "o", not_before=fetch.at(day, "09:30"))
        if o is None or o_t is None:
            out.append({**e, "status": "no_open"})
            continue
        _, vw = fetch_v3.entry_bar(bars.get(e["ticker"]), o_t)
        _, _, hs = fetch_v3.first_quote(e["ticker"], o_t)
        hs35, _ = fetch.quote(e["ticker"], day, "09:35")
        out.append({**e, "C": day.isoformat(), "o": o, "vw": vw, "hs_first": hs, "hs0935": hs35, "status": "ok"})
    return out


def stats(xs):
    xs = [x for x in xs if x is not None]
    return {"n": len(xs), "median": statistics.median(xs) if xs else None, "mean": sum(xs) / len(xs) if xs else None}


def block(rs):
    return {"hs_first": stats([r["hs_first"] for r in rs]), "hs0935": stats([r["hs0935"] for r in rs]),
            "abs_vwap_vs_open": stats([abs(r["vw"] / r["o"] - 1) if r["vw"] and r["o"] else None for r in rs]),
            "market_order_penalty_two_sided": stats([r["hs_first"] * r["vw"] / r["o"]
                                                     if r["vw"] and r["o"] and r["hs_first"] is not None else None
                                                     for r in rs])}


def main(do_commit=False):
    rows = [r for r in csv.DictReader(gzip.open(os.path.join(fetch.RAW, "events_intraday.csv.gz"), "rt",
                                                encoding="utf-8")) if not r.get("void")]
    rows = [r for r in rows if num(r["pm"]) and num(r["c0"]) and abs(num(r["pm"]) / num(r["c0"]) - 1) >= 0.01]
    evs = json.load(open(os.path.join(ROOT, "analysis", "history", "graded_events.json"), encoding="utf-8"))["events"]
    prints = {}
    for e in evs:
        prints.setdefault(e["ticker"], []).append(datetime.date.fromisoformat(e["exit_A"]))
    sessions = fetch.spy_sessions()
    ctrl = control_rows(rows, sessions, prints)
    by_day = {}
    for c in ctrl:
        by_day.setdefault(c["C"], []).append(c)
    measured, failed = [], []
    for day in sorted(by_day):
        try:
            measured += measure_day(day, by_day[day])
        except fetch.FetchFailed:
            failed.append(day.isoformat())
    ok = [m for m in measured if m.get("status") == "ok"]
    v3 = {(r["ticker"], r["R"]): r for r in csv.DictReader(open(os.path.join(fetch.RAW, "events_v3.csv"), encoding="utf-8"))}
    keys = {(m["ticker"], m["R"]) for m in ok}
    printday = []
    for r in rows:
        if (r["ticker"], r["R"]) in keys:
            x = v3.get((r["ticker"], r["R"]), {})
            printday.append({"o": num(r["o"]), "vw": num(x.get("vw")), "hs_first": num(x.get("hs_first")),
                             "hs0935": num(r["hs0935"]), "mcap": num(r["mcap"])})
    res = {"label": "DESCRIPTIVE control for D014 v3 - no test, no rule",
           "control_events": len(ctrl), "measured_ok": len(ok), "failed_days": failed,
           "status": {s: sum(1 for m in measured if m.get("status") == s) for s in ("ok", "no_open")},
           "matched_pairs": len(printday)}
    for name, f in (("all", lambda r: True), ("mid_cap", lambda r: r["mcap"] is not None and r["mcap"] < 10e9),
                    ("large", lambda r: r["mcap"] is not None and r["mcap"] >= 10e9)):
        res[name] = {"print_day": block([r for r in printday if f(r)]), "control_day": block([m for m in ok if f(m)])}
    json.dump(res, open(os.path.join(HERE, "control_days.json"), "w", encoding="utf-8", newline="\n"), indent=1,
              default=str)
    pct = lambda d: "-" if d["median"] is None else f"{d['median'] * 100:.3f}% (mean {d['mean'] * 100:.3f}%, n {d['n']})"
    L = ["# D014 control: the cost of the open on ordinary days vs print days (descriptive)", "",
         f"Control day = 10 sessions before the reaction day, no print of the same name within 3 sessions. "
         f"{res['measured_ok']} control days measured; {res['matched_pairs']} print days matched.", ""]
    for name in ("all", "mid_cap", "large"):
        L += [f"## {name}", "", "| measure (median) | print day | control day |", "|---|---|---|"]
        for k in ("hs_first", "hs0935", "abs_vwap_vs_open", "market_order_penalty_two_sided"):
            L.append(f"| {k} | {pct(res[name]['print_day'][k])} | {pct(res[name]['control_day'][k])} |")
        L.append("")
    open(os.path.join(HERE, "CONTROL.md"), "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    print("\n".join(L))
    if do_commit:
        from freeze import git, push_all
        git("add", "analysis/d014/control_days.json", "analysis/d014/CONTROL.md")
        git("commit", "-q", "-m", "D014 control: open costs on ordinary days (descriptive)\n\n"
            "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
        print("pushed:", push_all())


if __name__ == "__main__":
    main("--commit" in sys.argv)
