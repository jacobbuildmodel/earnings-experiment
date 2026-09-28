"""The history study (D006): build the event table and H factors, then - only once D006 is frozen -
the outcomes and the rule-v0 search.

    python pipeline/history.py build [TICKER ...]   # events + factors, NO outcomes -> analysis/history/
    python pipeline/history.py study                # D006 §5 steps 2-8; refuses unless D006 is frozen

Code only (D005 v2 §7.2). Order is enforced by code: nothing that touches a return runs before
registry/D006_history_study_v1.md is in FROZEN.sha256.
"""
import datetime
import json
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ET, REGISTRY, ROOT, Sec, now_et, write_json  # noqa: E402
import history_factors as hf  # noqa: E402

OUT = os.path.join(ROOT, "analysis", "history")
FIRST, LAST = datetime.date(2022, 9, 1), datetime.date(2026, 9, 18)   # D006 §2
PRICE_START = "2021-06-01"                                          # 252 sessions before FIRST, and more


def d006_frozen():
    for line in open(os.path.join(REGISTRY, "FROZEN.sha256"), encoding="utf-8"):
        if line.strip() and line.split(maxsplit=1)[1].strip().lstrip("*").startswith("D006_history_study_v"):
            return True
    return False


def universe():
    u = json.load(open(os.path.join(OUT, "universe.json"), encoding="utf-8"))
    return u["tickers"]


def spy_calendar():
    import yfinance as yf
    h = yf.Ticker("SPY").history(start=PRICE_START, end=(LAST + datetime.timedelta(days=10)).isoformat(),
                                 auto_adjust=False)
    return hf.Calendar([x.date() for x in h.tz_convert(ET).index])


def build_one(t, sec, cal, clusters):
    """Every agreed print of one company in the window, with its H factors. No outcome is computed."""
    import yfinance as yf
    cik = sec.cik(t)
    if not cik:
        return [], [{"ticker": t, "why": "no_cik"}]
    tk = yf.Ticker(t)
    sec_list = hf.sec_prints(sec, cik, cal)
    try:
        yf_list = hf.yf_prints(tk, 28, cal)
    except Exception as exc:
        return [], [{"ticker": t, "why": f"yfinance_dates_failed {type(exc).__name__}"}]
    agreed, rejected = hf.agreed_prints(sec_list, yf_list, cal)
    facts = json.loads(sec.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"))["facts"]
    end = (LAST + datetime.timedelta(days=10)).isoformat()
    adj = tk.history(start=PRICE_START, end=end, auto_adjust=True).tz_convert(ET)
    raw = tk.history(start=PRICE_START, end=end, auto_adjust=False).tz_convert(ET)
    splits = tk.splits
    events, excluded = [], [{**r, "ticker": t} for r in rejected
                            if FIRST.isoformat() <= r["date"] <= LAST.isoformat()]
    for i, p in enumerate(agreed):
        d = datetime.date.fromisoformat(p["date"])
        if not FIRST <= d <= LAST:
            continue
        try:
            tm = hf.timing(p["date"], p["session"], cal)
            f = hf.compute(tm["snapshot"], agreed[:i], facts, adj, raw, splits, d, cal)
        except Exception as exc:
            excluded.append({"ticker": t, "date": p["date"], "why": f"factor_error {type(exc).__name__}: {exc}",
                             "trace": traceback.format_exc(limit=2)})
            continue
        c = clusters.get(t, {})
        floor = c.get("market_cap_min") or 2e9
        ev = {"ticker": t, "date": p["date"], "session": p["session"], "cluster": c.get("cluster"),
              "snapshot": tm["snapshot"].isoformat(), "entry": tm["entry"].isoformat(),
              "exit_A": tm["exit_A"].isoformat(), "accepted_et": p["accepted_et"], "yf_ts": p["yf_ts"],
              "factors": f}
        if f["market_cap_pit"] is None:
            excluded.append({"ticker": t, "date": p["date"], "why": "no_pit_size"})
        elif f["market_cap_pit"] < floor:
            excluded.append({"ticker": t, "date": p["date"], "why": "size_below_floor_pit",
                             "cap": f["market_cap_pit"], "floor": floor})
        else:
            events.append(ev)
    return events, excluded


def build(only=None):
    sec = Sec(os.path.join(ROOT, "cache", "sec"))
    cal = spy_calendar()
    u = json.load(open(os.path.join(OUT, "universe.json"), encoding="utf-8"))
    clusters = u.get("clusters", {})
    tickers = only or u["tickers"]
    events, excluded = [], []
    for n, t in enumerate(tickers):
        try:
            ev, ex = build_one(t, sec, cal, clusters)
        except Exception as exc:
            ev, ex = [], [{"ticker": t, "why": f"build_error {type(exc).__name__}: {exc}"}]
        events += ev
        excluded += ex
        print(f"{n + 1}/{len(tickers)} {t}: {len(ev)} events, {len(ex)} excluded", flush=True)
        time.sleep(0.3)
    counts = {}
    for e in excluded:
        k = e["why"].split(" ")[0]
        counts[k] = counts.get(k, 0) + 1
    name = "events.json" if not only else "events_partial.json"
    write_json(os.path.join(OUT, name), {
        "built_et": now_et().isoformat(), "rule": "D006 §2-§4", "window": [FIRST.isoformat(), LAST.isoformat()],
        "note": "events and point-in-time factors only - no outcome has been computed",
        "n_events": len(events), "excluded_counts": counts, "events": events, "excluded": excluded})
    print(f"{len(events)} events; excluded {counts}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "build":
        build(a[1:] or None)
    elif a and a[0] == "study":
        if not d006_frozen():
            raise SystemExit("D006 is not frozen - no outcome may be computed yet (D005 v2 §7.1)")
        import history_study
        history_study.run()
    else:
        raise SystemExit(__doc__)
