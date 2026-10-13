"""D014 v2 section 2: the pre-print state (ret5) and the sector's week (rel5) for every D014 history event.
Alpaca daily bars (free plan, feed sip, adjustment split). Writes analysis/d014/raw/events_v2.csv and manifest_v2.json.

    python analysis/d014/fetch_v2.py [--commit]

Keys come from APCA_API_KEY_ID / APCA_API_SECRET_KEY (GitHub secrets); they are never printed or stored.
"""
import csv
import datetime
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import fetch  # noqa: E402  (v1's frozen request layer, session calendar and segments)

FIELDS = ["ticker", "R", "etf", "ret5", "etf_ret5", "spy_ret5", "rel5"]


def etf_map():
    d3 = json.load(open(os.path.join(ROOT, "registry", "D003_universe_screen_v4.json"), encoding="utf-8"))
    u = json.load(open(os.path.join(ROOT, "analysis", "history", "universe.json"), encoding="utf-8"))
    out = {}
    for t, c in u["clusters"].items():
        if t in d3["named"]:
            out[t] = d3["named"][t]["etf"]
        elif (c or {}).get("industry") in d3["industry_map"]:
            out[t] = d3["industry_map"][c["industry"]]["etf"]
    return out


def closes(sym):
    """{ET date: split-adjusted close}, or None if the symbol failed."""
    try:
        js = fetch.paged("bars", {"symbols": sym, "timeframe": "1Day", "feed": "sip", "adjustment": "split",
                                  "start": "2022-06-01", "end": "2026-09-30T23:00:00Z", "limit": 10000}, "bars")
    except fetch.FetchFailed:
        return None
    return {fetch.et_of(b["t"]).date(): b["c"] for b in js.get(sym, [])}


def r5(px, sessions, day):
    if px is None:
        return None
    i = sessions.index(day)
    a, b = px.get(sessions[i - 6]), px.get(sessions[i - 1])
    return b / a - 1 if a and b else None


def build(evs, sessions, emap, get_closes):
    syms = sorted({e["ticker"] for e in evs} | set(emap.values()) | {"SPY"})
    px = {s: get_closes(s) for s in syms}
    rows = []
    for e in evs:
        day = datetime.date.fromisoformat(e["exit_A"])
        if day not in sessions:
            continue
        etf = emap.get(e["ticker"])
        ret5, spy5 = r5(px[e["ticker"]], sessions, day), r5(px["SPY"], sessions, day)
        etf5 = r5(px.get(etf), sessions, day) if etf else None
        rows.append({"ticker": e["ticker"], "R": e["exit_A"], "etf": etf, "ret5": ret5, "etf_ret5": etf5,
                     "spy_ret5": spy5, "rel5": etf5 - spy5 if etf5 is not None and spy5 is not None else None})
    return rows, sorted(s for s, v in px.items() if v is None)


def main(do_commit=False):
    evs = json.load(open(os.path.join(ROOT, "analysis", "history", "graded_events.json"), encoding="utf-8"))["events"]
    evs = [e for e in evs if fetch.segment(datetime.date.fromisoformat(e["exit_A"]))]
    rows, failed = build(evs, fetch.spy_sessions(), etf_map(), closes)
    os.makedirs(fetch.RAW, exist_ok=True)
    with open(os.path.join(fetch.RAW, "events_v2.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    json.dump({"rule": "D014_exploration_postprint_v2 section 2",
               "run_utc": datetime.datetime.now(fetch.UTC).isoformat(timespec="seconds"),
               "fetch_v2_sha256": hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest(),
               "rows": len(rows), "failed_symbols": failed, "requests": fetch.stats,
               "source": "Alpaca market data v2, free plan, feed sip, adjustment split, daily bars"},
              open(os.path.join(fetch.RAW, "manifest_v2.json"), "w", encoding="utf-8", newline="\n"), indent=1)
    print(f"done: {len(rows)} rows, failed symbols {failed}, {fetch.stats}")
    if do_commit:
        fetch.commit(f"D014 v2 fetch: {len(rows)} rows")


if __name__ == "__main__":
    main("--commit" in sys.argv)
