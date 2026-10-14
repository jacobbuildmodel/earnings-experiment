"""D014 v3 section 1: the retail entry. For every non-void v1 event: the VWAP of the first regular 1-minute bar at or
after the official open's minute, and the first NBBO quote at or after the open. Alpaca market data (free plan,
feed sip, adjustment raw). Reads v1's rows for o_t only; prints no price. Writes raw/events_v3.csv, manifest_v3.json.

    python analysis/d014/fetch_v3.py [--commit]

Keys come from APCA_API_KEY_ID / APCA_API_SECRET_KEY (GitHub secrets); they are never printed or stored.
"""
import csv
import datetime
import gzip
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fetch  # noqa: E402  (v1's frozen request layer)

FIELDS = ["ticker", "R", "o_t", "entry_t", "vw", "first_bid", "first_ask", "hs_first", "status"]
LAST_ENTRY = datetime.time(9, 50)


def entry_bar(bars, o_t):
    """(start, vw) of the first regular bar starting at or after o_t's minute and before 09:50 ET, else (None, None)."""
    floor = o_t.replace(second=0, microsecond=0)
    for b in sorted(bars or [], key=lambda b: b["t"]):
        t = fetch.et_of(b["t"])
        if t >= floor and datetime.time(9, 30) <= t.time() < LAST_ENTRY:
            return t, b.get("vw")
    return None, None


def first_quote(sym, o_t):
    js = fetch.get(f"{sym}/quotes", {"feed": "sip", "limit": 1, "sort": "asc",
                                     "start": o_t.astimezone(fetch.UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                                     "end": (o_t + datetime.timedelta(minutes=2)).astimezone(fetch.UTC)
                                     .strftime("%Y-%m-%dT%H:%M:%S.%fZ")})
    q = (js or {}).get("quotes") or []
    if not q:
        return None, None, None
    bid, ask = q[0].get("bp"), q[0].get("ap")
    if not bid or not ask or bid <= 0 or ask < bid:
        return None, None, None
    return bid, ask, (ask - bid) / (ask + bid)


def build_date(day, evs):
    """evs: v1 rows reacting on `day` (non-void, with o_t). Raises fetch.FetchFailed if the bars request failed."""
    syms = sorted({e["ticker"] for e in evs})
    bars = fetch.paged("bars", {"symbols": ",".join(syms), "timeframe": "1Min", "feed": "sip", "adjustment": "raw",
                                "limit": 10000, "start": fetch.utc(day, "09:30"), "end": fetch.utc(day, "09:50")}, "bars")
    out = []
    for e in evs:
        o_t = datetime.datetime.fromisoformat(e["o_t"]).astimezone(fetch.ET)
        t, vw = entry_bar(bars.get(e["ticker"]), o_t)
        bid, ask, hs = first_quote(e["ticker"], o_t)
        status = "ok" if vw and hs is not None else "no_entry_minute" if not vw else "no_first_quote"
        out.append({"ticker": e["ticker"], "R": e["R"], "o_t": e["o_t"], "entry_t": t.isoformat() if t else None,
                    "vw": vw, "first_bid": bid, "first_ask": ask, "hs_first": hs, "status": status})
    return out


def main(do_commit=False):
    rows = list(csv.DictReader(gzip.open(os.path.join(fetch.RAW, "events_intraday.csv.gz"), "rt", encoding="utf-8")))
    live = [r for r in rows if not r.get("void") and r.get("o_t")]
    by_day = {}
    for r in live:
        by_day.setdefault(r["R"], []).append(r)
    out, failed = [], []
    for day in sorted(by_day):
        try:
            out += build_date(datetime.date.fromisoformat(day), by_day[day])
        except fetch.FetchFailed:
            failed.append(day)
    if failed:
        raise SystemExit(f"bars failed for {len(failed)} date(s): {failed[:10]} - rerun")
    with open(os.path.join(fetch.RAW, "events_v3.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    counts = {}
    for r in out:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    json.dump({"rule": "D014_exploration_postprint_v3 section 1",
               "run_utc": datetime.datetime.now(fetch.UTC).isoformat(timespec="seconds"),
               "fetch_v3_sha256": hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest(),
               "rows": len(out), "status": counts, "requests": fetch.stats,
               "source": "Alpaca market data v2, free plan, feed sip, adjustment raw"},
              open(os.path.join(fetch.RAW, "manifest_v3.json"), "w", encoding="utf-8", newline="\n"), indent=1)
    print(f"done: {len(out)} rows, {counts}, {fetch.stats}")
    if do_commit:
        fetch.commit(f"D014 v3 fetch: {len(out)} rows")


if __name__ == "__main__":
    main("--commit" in sys.argv)
