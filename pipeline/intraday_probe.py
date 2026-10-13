"""Read-only probe: can the Alpaca market-data API (free plan, the paper keys) give 1-minute history for a
post-print study? Run on NON-event days only (SPY, and AAPL on a day it did not report), so it sees no outcome.

    python pipeline/intraday_probe.py

Answers: does the SIP feed serve history on the free plan (and from when), are pre-market bars included,
does a multi-symbol request work, and do historical quotes (spreads at the open) come back.
Keys come from APCA_API_KEY_ID / APCA_API_SECRET_KEY (GitHub secrets); they are never printed or stored.
"""
import os

import requests

BASE = "https://data.alpaca.markets/v2/stocks"


def headers():
    return {"APCA-API-KEY-ID": os.environ["APCA_API_KEY_ID"], "APCA-API-SECRET-KEY": os.environ["APCA_API_SECRET_KEY"]}


def get(path, **params):
    r = requests.get(f"{BASE}/{path}", params=params, headers=headers(), timeout=30)
    return r.status_code, (r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text[:300])


def bars(symbols, day, feed, start="08:00", end="10:35"):
    code, js = get("bars", symbols=",".join(symbols), timeframe="1Min", feed=feed, adjustment="raw", limit=10000,
                   start=f"{day}T{start}:00-05:00" if day < "2025-03-09" else f"{day}T{start}:00-04:00",
                   end=f"{day}T{end}:00-05:00" if day < "2025-03-09" else f"{day}T{end}:00-04:00")
    if code != 200:
        return f"HTTP {code}: {str(js)[:200]}"
    out = []
    for s, bs in (js.get("bars") or {}).items():
        out.append(f"{s}: {len(bs)} bars, first {bs[0]['t']} last {bs[-1]['t']}, "
                   f"first-bar o/v {bs[0]['o']}/{bs[0]['v']}" if bs else f"{s}: 0 bars")
    return "; ".join(out) or "no bars"


def main():
    for feed in ("sip", "iex"):
        for day in ("2022-09-06", "2024-06-04", "2025-03-04"):
            print(f"[bars {feed} {day}]", bars(["SPY", "AAPL"], day, feed))
    code, js = get("quotes", symbols="AAPL", feed="sip", limit=5, start="2025-03-04T14:30:00Z",
                   end="2025-03-04T14:31:00Z")
    q = (js.get("quotes") or {}).get("AAPL", []) if code == 200 else []
    print(f"[quotes sip 2025-03-04 09:30] HTTP {code}, {len(q)} quotes",
          (q[0].get("bp"), q[0].get("ap")) if q else str(js)[:200])
    code, js = get("auctions", symbols="AAPL,SPY,NOC", start="2025-03-03", end="2025-03-04")
    for s, days in ((js.get("auctions") or {}) if code == 200 else {}).items():
        for d in days:
            print(f"[auctions {s} {d.get('d')}] open prints {[(x.get('x'), x.get('c'), x.get('p'), x.get('s')) for x in d.get('o') or []]}"
                  f" close prints {len(d.get('c') or [])}")
    if code != 200:
        print(f"[auctions] HTTP {code}", str(js)[:300])
    code, js = get("AAPL/quotes", feed="sip", limit=1, sort="desc", start="2025-03-04T14:30:00Z",
                   end="2025-03-04T14:35:00Z")
    print(f"[quotes sort=desc, last before 09:35] HTTP {code}", str(js)[:300])
    code, js = get("bars", symbols="SPY", timeframe="1Day", feed="sip", adjustment="split", start="2022-07-01",
                   end="2022-09-10", limit=10000)
    print(f"[daily SPY 2022-07-01..09-10] HTTP {code}", [b["t"] for b in (js.get("bars") or {}).get("SPY", [])][-6:]
          if code == 200 else str(js)[:200])


if __name__ == "__main__":
    main()
