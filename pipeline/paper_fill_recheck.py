"""D011 paper fills re-checked against real exchange prints, after the fact (descriptive, decides nothing).
Code only, no AI. Registered with the paper report views (registry/D011_report_views_v1.md).

    python pipeline/paper_fill_recheck.py probe [--commit]            # what the free plan's options history returns
    python pipeline/paper_fill_recheck.py fetch [SEASON] [--commit]   # store real prints around every paper fill

Why: the paper orders are priced from Alpaca's free "indicative" feed (randomised quotes), and Alpaca's paper engine
fills them against real quotes we never see. Alpaca's historical options BARS and TRADES are real OPRA prints: trades,
not quotes. They can check a fill after the fact. They cannot say what the quote was.

fetch: for every filled order record (open or close) in both paper ledgers whose fill is at least SETTLE_MIN old, it
stores, per filled leg, the 1-minute bars from BAR_MIN before to BAR_MIN after the fill and every trade from
TRADE_MIN before to TRADE_MIN after. Raw and write-once, in paper/fill_recheck/<season>/<client_order_id>.json.
- A request that fails (network, or any answer other than 200) leaves the whole file unwritten, so a later run retries.
- An answer with no prints is stored as an empty list: no real trade, which the report shows as missing. Nothing is
  ever filled in.
The report (pipeline/paper_options_report_v2.py) compares the ledger's paper fill with these prints (compare()).
"""
import datetime
import json
import os
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, now_et, write_json, write_once  # noqa: E402

DATA = "https://data.alpaca.markets/v1beta1/options"
BARS, TRADES, QUOTES = DATA + "/bars", DATA + "/trades", DATA + "/quotes"
LATEST_TRADES = DATA + "/trades/latest"
LEDGERS = {"PX-F": os.path.join("paper", "options_ledger.json"), "PX-L": os.path.join("paper", "long_ledger.json")}
CACHE = os.path.join(ROOT, "paper", "fill_recheck")
BAR_MIN = 15            # 1-minute bars kept from 15 min before to 15 min after the fill
TRADE_MIN = 5           # trade prints kept from 5 min before to 5 min after the fill
SETTLE_MIN = 40         # fetched once the fill is this old: the window is over and past the 15-minute data delay
PAUSE_S = 0.35          # between requests (the free plan allows 200 a minute)


def utc(ts):
    """An ISO timestamp (any offset, or Z) as an aware UTC datetime."""
    return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(datetime.timezone.utc)


def z(d):
    return d.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def default_get(url, params):
    """(status, json or None, text) from Alpaca market data. Keys from APCA_API_KEY_ID / APCA_API_SECRET_KEY."""
    from paper import headers
    try:
        r = requests.get(url, params=params, headers=headers(), timeout=30)
    except requests.RequestException as e:
        return None, None, type(e).__name__
    try:
        body = r.json() if r.text else {}
    except ValueError:
        body = None
    return r.status_code, body, r.text[:300]


def paged(get, url, params, field, sym):
    """Every row for one symbol across pages; (rows, None) or (None, failure text)."""
    rows, token = [], None
    for _ in range(50):
        p = dict(params, symbols=sym, limit=10000, sort="asc")
        if token:
            p["page_token"] = token
        code, body, text = get(url, p)
        time.sleep(PAUSE_S)
        if code != 200 or not isinstance(body, dict):
            return None, f"HTTP {code}: {text}"
        rows += (body.get(field) or {}).get(sym) or []
        token = body.get("next_page_token")
        if not token:
            return rows, None
    return None, "more than 50 pages"


def filled_records(season):
    """(account, trade, which, record) for every filled order record of the season, both ledgers."""
    out = []
    for acct, rel in LEDGERS.items():
        p = os.path.join(ROOT, rel)
        led = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
        for k, t in (led.get("trades") or {}).items():
            if (t.get("season") or k.split("-")[0]) != season:
                continue
            for which in ("open", "close"):
                for r in (t.get("orders") or {}).get(which) or []:
                    if r.get("filled_qty") and r.get("filled_at") and r.get("client_order_id"):
                        out.append((acct, t, which, r))
    return out


def cache_path(season, cid):
    return os.path.join(CACHE, season, f"{cid}.json")


def fetch_one(acct, t, which, rec, get=default_get, now=None):
    """The raw record for one filled order, or None if any request failed (nothing is written; a later run retries)."""
    f = utc(rec["filled_at"])
    bw = (f - datetime.timedelta(minutes=BAR_MIN), f + datetime.timedelta(minutes=BAR_MIN))
    tw = (f - datetime.timedelta(minutes=TRADE_MIN), f + datetime.timedelta(minutes=TRADE_MIN))
    legs = {}
    for lg in rec.get("legs_filled") or []:
        sym = lg.get("symbol")
        if not sym or not lg.get("qty"):
            continue
        bars, err = paged(get, BARS, {"timeframe": "1Min", "start": z(bw[0]), "end": z(bw[1])}, "bars", sym)
        if err:
            print(f"{rec['client_order_id']} {sym} bars: {err} - not written, retried next run")
            return None
        trades, err = paged(get, TRADES, {"start": z(tw[0]), "end": z(tw[1])}, "trades", sym)
        if err:
            print(f"{rec['client_order_id']} {sym} trades: {err} - not written, retried next run")
            return None
        legs[sym] = {"bars": bars, "trades": trades}
    if not legs:
        return None
    return {"rule": "D011 report views v1: paper fill re-check (descriptive, decides nothing)",
            "account": acct, "key": t.get("key"), "which": which, "client_order_id": rec["client_order_id"],
            "order_id": rec.get("id"), "filled_at": rec["filled_at"],
            "fetched_et": (now or now_et()).isoformat(timespec="seconds"),
            "source": {"bars": BARS + " timeframe=1Min", "trades": TRADES,
                       "what": "OPRA trade prints via Alpaca market data (free plan); trades, not quotes"},
            "window_utc": {"bars": [z(bw[0]), z(bw[1])], "trades": [z(tw[0]), z(tw[1])]},
            "legs": legs}


def fetch(season="seasonA", commit=False, get=default_get, now=None):
    now = now or now_et()
    wrote, waiting, failed = [], 0, 0
    for acct, t, which, rec in filled_records(season):
        p = cache_path(season, rec["client_order_id"])
        if os.path.exists(p):
            continue
        if now - utc(rec["filled_at"]) < datetime.timedelta(minutes=SETTLE_MIN):
            waiting += 1
            continue
        got = fetch_one(acct, t, which, rec, get, now)
        if got is None:
            failed += 1
            continue
        write_once(p, got)
        wrote.append(os.path.relpath(p, ROOT).replace(os.sep, "/"))
        n_tr = sum(len(v["trades"]) for v in got["legs"].values())
        print(f"{rec['client_order_id']}: {len(got['legs'])} leg(s), {n_tr} real trade(s) in +-{TRADE_MIN} min")
    print(f"fill re-check {season}: wrote {len(wrote)}, waiting {waiting}, failed {failed}")
    if commit and wrote:
        from freeze import git, push_all
        git("add", *wrote)
        git("commit", "-q", "-m", f"Paper fill re-check {season}: {len(wrote)} order(s) vs real OPRA prints (code, "
            f"D011 report views v1)\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
        print(f"pushed: {push_all()}")
    return 1 if failed else 0


# ---------------------------------------------------------------- compare (used by the report; offline)
def compare(rec, cached, side_of):
    """One filled order against the cached prints. side_of: {symbol: 'buy'|'sell'} as WE sent it.
    Per leg: the real trade nearest the fill, the 1-minute bar holding the fill, and the low-high of the bars around
    it. worse_by: + = the paper fill was worse for us than that print (paid more, or received less)."""
    f = utc(rec["filled_at"])
    out, nets, complete = {}, 0.0, True
    for lg in rec.get("legs_filled") or []:
        sym, px = lg.get("symbol"), lg.get("price")
        side = side_of.get(sym) or lg.get("side")
        if not sym or not lg.get("qty"):
            continue
        sign = 1 if side == "buy" else -1
        c = (cached.get("legs") or {}).get(sym)
        row = {"side": side, "paper_price": px}
        if c is None:
            row["missing"] = "not fetched"
            complete = False
            out[sym] = row
            continue
        trades = [(abs((utc(x["t"]) - f).total_seconds()), x) for x in c.get("trades") or []
                  if x.get("p") is not None and x.get("t")]
        if trades:
            dt, near = min(trades, key=lambda y: y[0])
            row.update(nearest_trade=near["p"], nearest_trade_t=near["t"], nearest_trade_dt_s=round(dt, 1),
                       trades_in_window=len(trades))
            if px is not None:
                row["worse_by_vs_nearest_trade"] = round(sign * (px - near["p"]), 4)
            nets += sign * near["p"]
        else:
            row["nearest_trade"] = None
            row["missing"] = f"no real trade within +-{TRADE_MIN} min"
            complete = False
        minute = f.replace(second=0, microsecond=0)
        bars = [b for b in c.get("bars") or [] if b.get("t") and b.get("l") is not None and b.get("h") is not None]
        held = next((b for b in bars if utc(b["t"]) == minute), None)
        row["fill_minute_bar"] = {k: held.get(k) for k in ("t", "o", "h", "l", "c", "v", "vw")} if held else None
        if bars:
            lo, hi = min(b["l"] for b in bars), max(b["h"] for b in bars)
            row["range_bars"] = [lo, hi]
            if px is not None:
                row["paper_inside_range"] = lo - 1e-9 <= px <= hi + 1e-9
        else:
            row["range_bars"] = None
        out[sym] = row
    fill = None
    if all(lg.get("price") is not None for lg in rec.get("legs_filled") or [] if lg.get("qty")):
        fill = sum(lg["price"] * (1 if (side_of.get(lg["symbol"]) or lg.get("side")) == "buy" else -1)
                   for lg in rec.get("legs_filled") or [] if lg.get("qty"))
    res = {"legs": out, "paper_net": fill, "net_at_nearest_trades": nets if complete and out else None}
    if res["net_at_nearest_trades"] is not None and fill is not None:
        res["worse_by_vs_nearest_trades"] = round(fill - res["net_at_nearest_trades"], 4)
    return res


# ---------------------------------------------------------------- probe
def probe(commit=False, get=default_get, now=None):
    """What the free plan returns for options history, recorded as found. Uses real fills from the ledgers."""
    now = now or now_et()
    recs = filled_records("seasonA")
    picks = []
    for acct in LEDGERS:
        mine = [x for x in recs if x[0] == acct]
        if mine:
            picks.append(max(mine, key=lambda x: x[3]["filled_at"]))     # the latest fill: a live contract
    if recs:
        oldest = min(recs, key=lambda x: x[3]["filled_at"])              # the oldest fill: by now, often expired
        if oldest not in picks:
            picks.append(oldest)
    today, after_close = now.date().isoformat(), now.time() >= datetime.time(16, 0)
    results = []
    for acct, t, which, rec in picks:
        f = utc(rec["filled_at"])
        sym = rec["legs_filled"][0]["symbol"]
        w1 = {"start": z(f - datetime.timedelta(minutes=BAR_MIN)), "end": z(f + datetime.timedelta(minutes=BAR_MIN))}
        w5 = {"start": z(f - datetime.timedelta(minutes=TRADE_MIN)), "end": z(f + datetime.timedelta(minutes=TRADE_MIN))}
        day = {"start": (f - datetime.timedelta(days=10)).date().isoformat(), "end": f.date().isoformat()}
        calls = [("bars 1Min +-15 min", BARS, dict(w1, timeframe="1Min"), "bars"),
                 ("trades +-5 min", TRADES, w5, "trades"),
                 ("quotes (historical) +-5 min", QUOTES, w5, "quotes"),
                 ("bars 1Day, 10 days to the fill", BARS, dict(day, timeframe="1Day"), "bars"),
                 ("bars 1Min feed=opra", BARS, dict(w1, timeframe="1Min", feed="opra"), "bars"),
                 ("bars 1Min feed=indicative", BARS, dict(w1, timeframe="1Min", feed="indicative"), "bars"),
                 ("latest trade feed=opra", LATEST_TRADES, {"feed": "opra"}, "trades"),
                 ("latest trade feed=indicative", LATEST_TRADES, {"feed": "indicative"}, "trades")]
        for name, url, params, field in calls:
            code, body, text = get(url, dict(params, symbols=sym))
            time.sleep(PAUSE_S)
            rows = (body or {}).get(field) if isinstance(body, dict) else None
            got = rows.get(sym) if isinstance(rows, dict) else None
            n = len(got) if isinstance(got, list) else (1 if isinstance(got, dict) else 0)
            first = got[0] if isinstance(got, list) and got else (got if isinstance(got, dict) else None)
            exp = t.get("expiry") or "9999-12-31"
            res = {"account": acct, "order": rec["client_order_id"], "symbol": sym, "expiry": t.get("expiry"),
                   "expired": exp < today or (exp == today and after_close), "fill_utc": z(f), "call": name, "url": url,
                   "params": {k: v for k, v in params.items()}, "http": code, "rows": n, "first_row": first,
                   "next_page_token": bool(isinstance(body, dict) and body.get("next_page_token")),
                   "error": None if code == 200 else text}
            results.append(res)
            print(f"{acct} {sym} {name}: HTTP {code}, {n} row(s){'' if code == 200 else ' - ' + str(text)[:160]}")
    out = {"what": "probe of Alpaca's options market-data history on this account's (free) plan",
           "run_et": now.isoformat(timespec="seconds"), "results": results}
    p = os.path.join(ROOT, "ops", "probes", f"alpaca_options_history_{now:%Y-%m-%d}.json")
    write_json(p, out)
    if commit:
        from freeze import git, push_all
        git("add", os.path.relpath(p, ROOT).replace(os.sep, "/"))
        if git("diff", "--cached", "--name-only"):
            git("commit", "-q", "-m", "Probe: Alpaca options history on the free plan (code, D011 report views)"
                "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
            print(f"pushed: {push_all()}")
    return out


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if a and a[0] == "probe":
        probe("--commit" in sys.argv)
    elif a and a[0] == "fetch":
        sys.exit(fetch(a[1] if len(a) > 1 else "seasonA", "--commit" in sys.argv))
    else:
        raise SystemExit(__doc__)
