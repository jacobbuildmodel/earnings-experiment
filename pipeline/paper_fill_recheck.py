"""D011 paper orders re-checked against real exchange prints, after the fact (descriptive, decides nothing).
Code only, no AI. Registered with the paper report views (registry/D011_report_views_v1.md).

    python pipeline/paper_fill_recheck.py probe [--commit]            # what the free plan's options history returns
    python pipeline/paper_fill_recheck.py fetch [SEASON] [--commit]   # store real prints around every paper order

Why: the paper orders are priced from Alpaca's free "indicative" feed (randomised quotes), and Alpaca's paper engine
fills them against real quotes we never see. Alpaca's historical options BARS and TRADES are real OPRA prints: trades,
not quotes. They can check an order after the fact. They cannot say what the quote was.
Probed 2026-10-16 (ops/probes/alpaca_options_history_2026-10-16.json): 1-minute bars and trades answer on this plan,
also for an expired contract; there is no historical quotes endpoint (404); a daily range ending on the current date
and the latest OPRA trade were refused ("OPRA agreement is not signed"); the bars endpoint takes no feed parameter.

fetch, per order record that reached Alpaca (it has an order id) and is final, per leg, raw and write-once in
paper/fill_recheck/<season>/<client_order_id>.json:
- a FILLED order: the 1-minute bars from BAR_MIN before to BAR_MIN after the fill, and every trade from TRADE_MIN
  before to TRADE_MIN after it;
- an order that ended UNFILLED: the 1-minute bars while it was live (sent -> cancel requested + 2 min, never past the
  session's 16:00 ET close; with no cancel request, to that close);
- an order with a filled quantity but no fill time is not fetched (the report says so).
A window is fetched once it ended SETTLE_H hours ago, so a same-day answer that had not settled is never stored.
A request that fails leaves the whole file unwritten and a later run retries. The one exception: a request error
about the contract or window itself (400, 404, 422) for a window older than GIVE_UP_DAYS is stored as that leg's
error, so one bad contract cannot turn every run red. Auth, plan and rate answers (401, 403, 408, 429) and 5xx are
never stored: the run stays red until a person looks. An answer with no prints is stored as an empty list: no real
trade, which the report shows as missing. Nothing is ever filled in. With --commit, neither fetch nor probe runs
from 14:00 to 16:05 ET on a weekday (the paper window's commits).
The report (pipeline/paper_options_report_v2.py) compares each order with these prints (compare_filled(),
compare_unfilled()).
"""
import datetime
import json
import os
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ET, ROOT, now_et, write_json, write_once  # noqa: E402

DATA = "https://data.alpaca.markets/v1beta1/options"
BARS, TRADES, QUOTES = DATA + "/bars", DATA + "/trades", DATA + "/quotes"
LATEST_TRADES = DATA + "/trades/latest"
LEDGERS = {"PX-F": os.path.join("paper", "options_ledger.json"), "PX-L": os.path.join("paper", "long_ledger.json")}
BAR_MIN = 30            # filled: 1-minute bars from 30 min before to 30 min after the fill
TRADE_MIN = 15          # filled: trade prints from 15 min before to 15 min after (thin contracts print rarely)
NEAR_S = 60             # a print this close to the fill counts as "at the fill" in the headline comparisons
SETTLE_H = 12           # a window is fetched once it ended this long ago (the probe only saw data hours old)
GIVE_UP_DAYS = 3        # a request error for a window older than this is stored as the leg's error
PERMANENT = (400, 404, 422)   # request errors about this contract or window; 401/403/408/429/5xx are about the
                              # account or the moment (403 = "OPRA agreement is not signed"): never stored, run red
CANCEL_GRACE_MIN = 2    # unfilled: an order counts as live until its cancel request + this
SESSION_END = datetime.time(16, 0)
QUIET = (datetime.time(14, 0), datetime.time(16, 5))   # no committing fetch inside the paper window (weekdays)
PAUSE_S = 0.35          # between requests (the free plan allows 200 a minute)
TERMINAL = ("filled", "canceled", "expired", "rejected", "done_for_day", "replaced")   # paper_options.TERMINAL


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
    """Every row for one symbol across pages: (rows, None, 200) or (None, failure text, status)."""
    rows, token = [], None
    for _ in range(50):
        p = dict(params, symbols=sym, limit=10000, sort="asc")
        if token:
            p["page_token"] = token
        code, body, text = get(url, p)
        time.sleep(PAUSE_S)
        if code != 200 or not isinstance(body, dict):
            return None, f"HTTP {code}: {text}", code
        rows += (body.get(field) or {}).get(sym) or []
        token = body.get("next_page_token")
        if not token:
            return rows, None, 200
    return None, "more than 50 pages", None


def is_filled(rec):
    return bool(rec.get("filled_qty") and rec.get("filled_at"))


def fill_time_unknown(rec):
    return bool(rec.get("filled_qty")) and not rec.get("filled_at")


def order_records(season, root=ROOT):
    """(account, trade, which, record) for every order record of the season that reached Alpaca and is final:
    filled with a fill time, or ended unfilled. Both ledgers."""
    out = []
    for acct, rel in LEDGERS.items():
        p = os.path.join(root, rel)
        led = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
        for k, t in (led.get("trades") or {}).items():
            if (t.get("season") or k.split("-")[0]) != season:
                continue
            for which in ("open", "close"):
                for r in (t.get("orders") or {}).get(which) or []:
                    if not (r.get("client_order_id") and r.get("id")) or fill_time_unknown(r):
                        continue
                    if is_filled(r) or r.get("status") in TERMINAL:
                        out.append((acct, t, which, r))
    return out


def live_window(rec):
    """(start, end) in UTC of an order that ended unfilled: sent -> cancel requested + grace, never past the close."""
    s = utc(rec["sent_et"])
    close = datetime.datetime.combine(s.astimezone(ET).date(), SESSION_END, ET).astimezone(datetime.timezone.utc)
    end = close
    if rec.get("cancel_requested"):
        end = min(close, utc(rec["cancel_requested"]) + datetime.timedelta(minutes=CANCEL_GRACE_MIN))
    return s, max(s, end)


def windows(rec):
    """{"bars": (start, end), "trades": (start, end) or None} for one order record."""
    if is_filled(rec):
        f = utc(rec["filled_at"])
        return {"bars": (f - datetime.timedelta(minutes=BAR_MIN), f + datetime.timedelta(minutes=BAR_MIN)),
                "trades": (f - datetime.timedelta(minutes=TRADE_MIN), f + datetime.timedelta(minutes=TRADE_MIN))}
    return {"bars": live_window(rec), "trades": None}


def window_end(rec):
    return max(v[1] for v in windows(rec).values() if v)


def leg_symbols(rec):
    if is_filled(rec):
        return [lg["symbol"] for lg in rec.get("legs_filled") or [] if lg.get("symbol") and lg.get("qty")]
    return sorted(rec.get("sides") or {})


def cache_path(season, cid, root=ROOT):
    return os.path.join(root, "paper", "fill_recheck", season, f"{cid}.json")


def load_cached(season, cid, root=ROOT):
    p = cache_path(season, cid, root)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def fetch_one(acct, t, which, rec, get=default_get, now=None):
    """The raw record for one order, or None if a request failed (nothing is written; a later run retries)."""
    now = now or now_et()
    w = windows(rec)
    old = now - window_end(rec) >= datetime.timedelta(days=GIVE_UP_DAYS)
    legs = {}
    for sym in leg_symbols(rec):
        legs[sym] = {}
        for name, url, win in (("bars", BARS, w["bars"]), ("trades", TRADES, w["trades"])):
            if not win:
                continue
            params = {"start": z(win[0]), "end": z(win[1])}
            if name == "bars":
                params["timeframe"] = "1Min"
            rows, err, code = paged(get, url, params, name, sym)
            if err is None:
                legs[sym][name] = rows
            elif old and code in PERMANENT:
                legs[sym][name] = None
                legs[sym]["error"] = err                  # refused for good: stored, shown as missing with its reason
            else:
                print(f"{rec['client_order_id']} {sym} {name}: {err} - not written, retried next run")
                return None
    if not legs:
        return None
    return {"rule": "D011 report views v1: paper order re-check (descriptive, decides nothing)",
            "account": acct, "key": t.get("key"), "which": which, "client_order_id": rec["client_order_id"],
            "order_id": rec.get("id"), "kind": "filled" if is_filled(rec) else "unfilled",
            "filled_at": rec.get("filled_at"), "sent_et": rec.get("sent_et"),
            "fetched_et": now.isoformat(timespec="seconds"),
            "source": {"bars": BARS + " timeframe=1Min", "trades": TRADES,
                       "what": "OPRA trade prints via Alpaca market data (free plan); trades, not quotes"},
            "window_utc": {k: ([z(v[0]), z(v[1])] if v else None) for k, v in w.items()},
            "legs": legs}


def in_quiet(now):
    et = now.astimezone(ET)
    return et.weekday() < 5 and QUIET[0] <= et.time() < QUIET[1]


def fetch(season="seasonA", commit=False, get=default_get, now=None, root=ROOT):
    """0 = nothing failed; 1 = a request or a push failed (the run goes red; a later run retries)."""
    now = now or now_et()
    if commit and in_quiet(now):
        print("14:00-16:05 ET on a weekday: the paper window commits now - nothing fetched, a later run catches up")
        return 0
    wrote, waiting, failed = [], 0, 0
    for acct, t, which, rec in order_records(season, root):
        p = cache_path(season, rec["client_order_id"], root)
        if os.path.exists(p):
            continue
        if now - window_end(rec) < datetime.timedelta(hours=SETTLE_H):
            waiting += 1
            continue
        got = fetch_one(acct, t, which, rec, get, now)
        if got is None:
            failed += 1
            continue
        write_once(p, got)
        wrote.append(os.path.relpath(p, root).replace(os.sep, "/"))
        n_tr = sum(len(v.get("trades") or []) for v in got["legs"].values())
        n_b = sum(len(v.get("bars") or []) for v in got["legs"].values())
        print(f"{rec['client_order_id']} ({got['kind']}): {len(got['legs'])} leg(s), {n_b} bar(s), {n_tr} trade(s)")
    print(f"order re-check {season}: wrote {len(wrote)}, waiting {waiting}, failed {failed}")
    pushed = True
    if commit and wrote:
        from freeze import git, push_all
        git("add", *wrote)
        git("commit", "-q", "-m", f"Paper order re-check {season}: {len(wrote)} order(s) vs real OPRA prints (code, "
            f"D011 report views v1)\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
        res = push_all()
        print(f"pushed: {res}")
        pushed = all(res.values())
    return 1 if failed or not pushed else 0


# ---------------------------------------------------------------- compare (used by the report; offline)
def sign_of(side):
    return 1 if side == "buy" else -1


def limit_net(rec):
    """The order's limit in the debit-positive convention. A v3 one-leg close is sent as a simple order whose
    limit_price is always positive; a SELL there is a credit, so its sign is restored."""
    try:
        lim = float(rec["limit_price"])
    except (KeyError, TypeError, ValueError):
        return None
    sides = rec.get("sides") or {}
    if rec.get("order_class") == "simple" and len(sides) == 1 and next(iter(sides.values())) == "sell":
        return -abs(lim)
    return lim


def compare_filled(rec, cached):
    """A filled order against the prints around its fill. Per leg: the real trade nearest the fill (any distance up
    to TRADE_MIN), the 1-minute bar holding the fill, and the low-high of the bars around it. worse_by: + = the paper
    fill was worse for us than that print (paid more, or received less). Per order, two nets: at the nearest prints
    however far apart (max_leg_dt_s says how far: NOT simultaneous), and at prints within NEAR_S of the fill on every
    leg, the headline. Condition codes (multi-leg prints included) are recorded, not filtered."""
    f = utc(rec["filled_at"])
    sides = rec.get("all_sides") or rec.get("sides") or {}
    out, nets, complete, near_ok, dts = {}, 0.0, True, True, []
    legs = [lg for lg in rec.get("legs_filled") or [] if lg.get("symbol") and lg.get("qty")]
    for lg in legs:
        sym, px = lg["symbol"], lg.get("price")
        side = sides.get(sym) or lg.get("side")
        c = ((cached or {}).get("legs") or {}).get(sym)
        row = {"side": side, "paper_price": px}
        out[sym] = row
        if c is None or c.get("error"):
            row["missing"] = "not fetched" if c is None else f"data refused: {c['error']}"
            complete = near_ok = False
            continue
        trades = [(abs((utc(x["t"]) - f).total_seconds()), x) for x in c.get("trades") or []
                  if x.get("p") is not None and x.get("t")]
        if trades:
            dt, near = min(trades, key=lambda y: y[0])
            row.update(nearest_trade=near["p"], nearest_trade_t=near["t"], nearest_trade_dt_s=round(dt, 1),
                       nearest_trade_condition=near.get("c"), nearest_trade_exchange=near.get("x"),
                       trades_in_window=len(trades))
            if px is not None:
                row["worse_by_vs_nearest_trade"] = round(sign_of(side) * (px - near["p"]), 4)
            nets += sign_of(side) * near["p"]
            dts.append(dt)
            near_ok = near_ok and dt <= NEAR_S
        else:
            row["nearest_trade"] = None
            row["missing"] = f"no real trade within +-{TRADE_MIN} min"
            complete = near_ok = False
        minute = f.replace(second=0, microsecond=0)
        bars = [b for b in c.get("bars") or [] if b.get("t") and b.get("l") is not None and b.get("h") is not None]
        held = next((b for b in bars if utc(b["t"]) == minute), None)
        row["fill_minute_bar"] = {k: held.get(k) for k in ("t", "o", "h", "l", "c", "v", "vw")} if held else None
        row["range_bars"] = [min(b["l"] for b in bars), max(b["h"] for b in bars)] if bars else None
        if bars and px is not None:
            row["paper_inside_range"] = row["range_bars"][0] - 1e-9 <= px <= row["range_bars"][1] + 1e-9
    paper = None
    if legs and all(lg.get("price") is not None for lg in legs):
        paper = sum(lg["price"] * sign_of(sides.get(lg["symbol"]) or lg.get("side")) for lg in legs)
    res = {"kind": "filled", "legs": out, "paper_net": paper,
           "net_at_nearest_trades": nets if complete and out else None,
           "max_leg_dt_s": round(max(dts), 1) if complete and dts else None,
           f"net_at_trades_within_{NEAR_S}s": nets if complete and near_ok and out else None}
    if res["net_at_nearest_trades"] is not None and paper is not None:
        res["worse_by_vs_nearest_trades (not simultaneous)"] = round(paper - res["net_at_nearest_trades"], 4)
    if res[f"net_at_trades_within_{NEAR_S}s"] is not None and paper is not None:
        res[f"worse_by_vs_trades_within_{NEAR_S}s"] = round(paper - nets, 4)
    return res


def compare_unfilled(rec, cached):
    """An order that ended unfilled, against the prints while it was live. Per leg: did any real print reach the
    recorded indicative far side (buy: a low at or under the ask; sell: a high at or over the bid)? Per order: the
    best net the prints allowed, legs taken at their best price at ANY minute, so NOT simultaneous: a ceiling on how
    marketable the limit was, suggestive only."""
    sides, q = rec.get("sides") or {}, rec.get("quotes") or {}
    out, best, complete = {}, 0.0, True
    for sym in sorted(sides):
        side = sides[sym]
        qq = q.get(sym) or {}
        far = qq.get("ask") if side == "buy" else qq.get("bid")
        c = ((cached or {}).get("legs") or {}).get(sym)
        row = {"side": side, "recorded_far_side": far}
        out[sym] = row
        if c is None or c.get("error"):
            row["missing"] = "not fetched" if c is None else f"data refused: {c['error']}"
            complete = False
            continue
        bars = [b for b in c.get("bars") or [] if b.get("l") is not None and b.get("h") is not None]
        row["bars_while_live"] = len(bars)
        if not bars:
            row["missing"] = "no real trade while the order was live"
            complete = False
            continue
        lo, hi = min(b["l"] for b in bars), max(b["h"] for b in bars)
        row["range_while_live"] = [lo, hi]
        bp = lo if side == "buy" else hi
        row["best_print"] = bp
        if far is not None:
            row["print_reached_far_side"] = (lo <= far + 1e-9) if side == "buy" else (hi >= far - 1e-9)
        best += sign_of(side) * bp
    lim = limit_net(rec)
    res = {"kind": "unfilled", "legs": out, "limit": lim, "best_net_from_prints": best if complete and out else None}
    if res["best_net_from_prints"] is not None and lim is not None:
        res["prints_reached_limit (not simultaneous)"] = res["best_net_from_prints"] <= lim + 1e-9
    return res


# ---------------------------------------------------------------- probe
def probe(commit=False, get=default_get, now=None):
    """What the free plan returns for options history, recorded as found. Uses real fills from the ledgers."""
    now = now or now_et()
    if commit and in_quiet(now):
        print("14:00-16:05 ET on a weekday: the paper window commits now - no probe")
        return None
    recs = [x for x in order_records("seasonA") if is_filled(x[3])]
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
        w1 = {"start": z(f - datetime.timedelta(minutes=15)), "end": z(f + datetime.timedelta(minutes=15))}
        w5 = {"start": z(f - datetime.timedelta(minutes=5)), "end": z(f + datetime.timedelta(minutes=5))}
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
