"""Factor snapshot for one event, taken in the S2 window, before entry. Free sources only.

    python pipeline/factors.py <season> <TICKER> <YYYY-MM-DD> [--dry]

Every value carries its source. A failed fetch is recorded as missing, never filled in.
Candidates are labelled with their literature-review id (LRxx) or FRAMEWORK family; none is a rule.
"""
import datetime
import json
import math
import os
import sys
import traceback

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ET, ROOT, now_et, registry, write_json, write_once  # noqa: E402
from sessions import shift  # noqa: E402

D001 = registry("D001_outcome_v1.json")


def clean(x):
    if isinstance(x, (np.floating, np.integer)):
        x = x.item()
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return None
    return x


def put(sheet, key, value, source, note=None):
    sheet[key] = {"value": clean(value), "source": source}
    if note:
        sheet[key]["note"] = note


def safely(sheet, key, fn):
    try:
        fn()
    except Exception as exc:
        sheet[key] = {"value": None, "error": f"{type(exc).__name__}: {exc}",
                      "trace": traceback.format_exc(limit=2)}


def price_block(sheet, tk, snap_session):
    h = tk.history(period="2y", auto_adjust=True)
    h.index = h.index.tz_convert(ET)
    h = h[h.index.date <= snap_session]  # nothing after the snapshot session
    h = h.dropna(subset=["Close", "Open"])  # vendor leaves a NaN placeholder bar for some sessions
    c, v = h["Close"], h["Volume"]
    r = c.pct_change()
    src = "yfinance history(2y, auto_adjust=True), to snapshot session (intraday last bar if live)"
    put(sheet, "A_ret_12m_LR01", c.iloc[-1] / c.iloc[-253] - 1 if len(c) > 253 else None, src)
    put(sheet, "A_ret_1m", c.iloc[-1] / c.iloc[-22] - 1, src)
    put(sheet, "A_ret_5d_LR10", c.iloc[-1] / c.iloc[-6] - 1, src)
    put(sheet, "A_max_daily_ret_21d_LR11", r.iloc[-21:].max(), src)
    put(sheet, "A_vol_60d_ann", r.iloc[-60:].std() * math.sqrt(252), src)
    put(sheet, "A_volume_20d_vs_250d", v.iloc[-20:].mean() / v.iloc[-250:].mean(), src)
    put(sheet, "A_dist_from_52w_high", c.iloc[-1] / c.iloc[-252:].max() - 1, src)
    return h


def past_prints(sheet, tk, h, report_date):
    """E-family: the last 4 prints scored the D001 way (open before -> open after), on this stock's history."""
    ed = tk.get_earnings_dates(limit=12)
    rows = []
    for ts, row in ed.iterrows():
        d = ts.astimezone(ET).date()
        if d >= report_date:
            continue
        t = ts.astimezone(ET).time()
        sess = "BMO" if t < datetime.time(9, 30) else "AMC" if t >= datetime.time(16, 0) else None
        if not sess:
            continue
        tim = D001["timing"][sess]
        try:
            e_day, x_day = shift(d, tim["entry"][1]), shift(d, tim["exit_A"][1])
        except ValueError:
            continue
        days = {x.date(): x for x in h.index}
        if e_day in days and x_day in days:
            o_e, o_x = h.loc[days[e_day], "Open"], h.loc[days[x_day], "Open"]
            vol_ratio = h.loc[days[x_day], "Volume"] / h["Volume"].loc[:days[e_day]].iloc[-21:-1].mean()
            rows.append({"date": d.isoformat(), "session": sess, "raw_return_A": clean(o_x / o_e - 1),
                         "eps_est": clean(row.get("EPS Estimate")), "eps_rep": clean(row.get("Reported EPS")),
                         "surprise_pct": clean(row.get("Surprise(%)")), "reaction_volume_ratio": clean(vol_ratio)})
        if len(rows) == 4:
            break
    src = "yfinance get_earnings_dates + history (adjusted opens)"
    put(sheet, "E_last4_prints", rows, src, "EPS basis NOT pinned (STATE #2) - surprise is vendor-defined")
    wins = [x["raw_return_A"] > 0 for x in rows if x["raw_return_A"] is not None]
    put(sheet, "E_last4_win_rate_A", sum(wins) / len(wins) if wins else None, src)
    vr = [x["reaction_volume_ratio"] for x in rows if x["reaction_volume_ratio"]]
    put(sheet, "E_past_reaction_volume_LR02", sum(vr) / len(vr) if vr else None, src)
    last = rows[0]["surprise_pct"] if rows else None
    put(sheet, "E_last_surprise_pct_LR17", last, src, "EPS basis NOT pinned")


def expectations(sheet, tk):
    src = "yfinance eps_trend / earnings_estimate / info"
    et = tk.eps_trend
    if et is not None and len(et):
        row = et.iloc[0]
        put(sheet, "D_eps_trend_current_q", {k: clean(row.get(k)) for k in et.columns}, src)
        cur, d90 = clean(row.get("current")), clean(row.get("90daysAgo"))
        put(sheet, "D_eps_revision_90d_LR19", (cur - d90) / abs(d90) if cur is not None and d90 else None, src)
    ee = tk.earnings_estimate
    if ee is not None and len(ee):
        row = ee.iloc[0]
        avg, lo, hi = clean(row.get("avg")), clean(row.get("low")), clean(row.get("high"))
        put(sheet, "D_eps_est_current_q", {k: clean(row.get(k)) for k in ee.columns}, src)
        put(sheet, "C_analyst_dispersion_LR08", (hi - lo) / abs(avg) if None not in (hi, lo, avg) and avg else None,
            src, "(high-low)/|avg| - a crude dispersion proxy")
    info = tk.info or {}
    for k, key in [("shortPercentOfFloat", "C_short_pct_float"), ("forwardPE", "J_forward_pe_LR20"),
                   ("priceToSalesTrailing12Months", "J_price_to_sales_LR20"), ("revenueGrowth", "J_revenue_growth"),
                   ("marketCap", "K_market_cap"), ("recommendationMean", "C_analyst_rec_mean")]:
        put(sheet, key, info.get(k), "yfinance info (vendor snapshot, no timestamp)")


def options_block(sheet, chain, gate):
    src = "own option-chain capture (gate step, yfinance)"
    if not chain or "calls" not in chain or not gate.get("options"):
        put(sheet, "B_options", None, src, "no chain captured")
        return
    o = gate["options"]
    spot, k = o["spot"], o["strike"]
    put(sheet, "B_implied_move", o.get("implied_move"), src)
    put(sheet, "B_iv_spread_call_minus_put_atm_LR12",
        (o["call"]["impliedVolatility"] or 0) - (o["put"]["impliedVolatility"] or 0), src)
    puts = [p for p in chain["puts"] if p.get("impliedVolatility")]
    otm = min(puts, key=lambda p: abs(p["strike"] - 0.9 * spot)) if puts else None
    put(sheet, "B_put_skew_90_LR13",
        otm["impliedVolatility"] - o["call"]["impliedVolatility"] if otm and o["call"]["impliedVolatility"] else None,
        src, "IV(put nearest 0.9*spot) - IV(ATM call), same expiry")
    cv = sum(c.get("volume") or 0 for c in chain["calls"] if clean(c.get("volume")) is not None)
    pv = sum(p.get("volume") or 0 for p in chain["puts"] if clean(p.get("volume")) is not None)
    coi = sum(c.get("openInterest") or 0 for c in chain["calls"] if clean(c.get("openInterest")) is not None)
    poi = sum(p.get("openInterest") or 0 for p in chain["puts"] if clean(p.get("openInterest")) is not None)
    put(sheet, "B_put_call_volume_LR14", pv / cv if cv else None, src, "plain volume, gate expiry only")
    put(sheet, "B_put_call_oi", poi / coi if coi else None, src, "gate expiry only")
    put(sheet, "B_option_volume_gate_expiry", cv + pv, src)


def calendar_block(sheet, ticker, report_date):
    import requests
    from common import WEB_HEADERS
    r = requests.get("https://api.nasdaq.com/api/calendar/earnings",
                     params={"date": report_date.isoformat()}, headers=WEB_HEADERS, timeout=30)
    rows = (r.json().get("data") or {}).get("rows") or []
    put(sheet, "L_same_day_reporters_LR06", len(rows), "nasdaq calendar (all caps)")
    put(sheet, "L_weekday_LR07", report_date.strftime("%A"), "report date")


def stage_block(sheet, ticker, snapshot_date):
    """D004 §4: business stage from SEC XBRL companyfacts, facts filed before the snapshot."""
    from common import Sec
    sec = Sec(os.path.join(ROOT, "cache", "sec"))
    cik = sec.cik(ticker)
    facts = json.loads(sec.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"))["facts"].get("us-gaap", {})
    src = "SEC XBRL companyfacts (10-Q/10-K, filed before snapshot)"

    def quarters(tag):
        """{(fy_end_label, fp, end): value} for ~3-month facts, plus annual facts, filed before the snapshot."""
        units = facts.get(tag, {}).get("units", {}).get("USD", [])
        q, a = {}, {}
        for u in units:
            if u.get("form") not in ("10-Q", "10-K", "10-Q/A", "10-K/A") or u["filed"] > snapshot_date or "start" not in u:
                continue
            days = (datetime.date.fromisoformat(u["end"]) - datetime.date.fromisoformat(u["start"])).days
            if 80 <= days <= 100:
                q[u["end"]] = (u["start"], u["val"])
            elif 350 <= days <= 380:
                a[u["end"]] = (u["start"], u["val"])
        # derive Q4 = annual - three quarters inside that year, where the 3-month fact is missing
        for end, (start, val) in a.items():
            inside = [v for e, (s, v) in q.items() if start <= s and e < end]
            if end not in q and len(inside) == 3:
                q[end] = ("derived", val - sum(inside))
        return q

    rev = {}
    for tag in ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"):
        for end, v in quarters(tag).items():
            rev.setdefault(end, v)  # per quarter, the first tag in priority order that has a value
    op = quarters("OperatingIncomeLoss")
    if not rev or not op:
        put(sheet, "K_stage", "unknown", src, "revenue or operating income missing")
        return
    common_q = set(rev) & set(op)
    if not common_q:
        put(sheet, "K_stage", "unknown", src, "no quarter with both revenue and operating income")
        return
    latest = max(common_q)
    if (datetime.date.fromisoformat(snapshot_date) - datetime.date.fromisoformat(latest)).days > 200:
        put(sheet, "K_stage", "unknown", src, f"stale: latest quarter with both inputs ends {latest}")
        return
    le = datetime.date.fromisoformat(latest)
    prior = [e for e in rev if 350 <= (le - datetime.date.fromisoformat(e)).days <= 380]
    growth = rev[latest][1] / rev[prior[0]][1] - 1 if prior and rev[prior[0]][1] else None
    margin = op[latest][1] / rev[latest][1] if latest in op and rev[latest][1] else None
    flags = [f for f, cond in [("q4_derived", rev[latest][0] == "derived" or op.get(latest, ("",))[0] == "derived")] if cond]
    if growth is None or margin is None:
        stage = "unknown"
    elif growth >= 0.20:
        stage = "unprofitable_growth" if margin < 0 else "profitable_growth"
    else:
        stage = "mature"
    put(sheet, "K_stage", stage, src, f"quarter ending {latest}; flags {flags}")
    put(sheet, "K_rev_growth_yoy_q", growth, src, f"quarter ending {latest}")
    put(sheet, "K_op_margin_q", margin, src, f"quarter ending {latest}")


def run(season, ticker, report_date, dry=False):
    import yfinance as yf
    ticker = ticker.upper()
    base = (os.path.join(ROOT, "cache", "dry", f"{ticker}_{report_date}") if dry
            else os.path.join(ROOT, "events", season, f"{ticker}_{report_date}"))
    gate = json.load(open(os.path.join(base, "gate.json"), encoding="utf-8"))
    chain_path = os.path.join(base, "option_chain.json")
    chain = json.load(open(chain_path, encoding="utf-8")) if os.path.exists(chain_path) else None
    snap_session = datetime.date.fromisoformat(gate["snapshot_session"])
    tk = yf.Ticker(ticker)
    sheet = {}
    meta = {"ticker": ticker, "report_date": report_date.isoformat(), "session": gate["session"],
            "captured_et": now_et().isoformat(), "snapshot_session": gate["snapshot_session"], "dry": dry}
    hist = {}
    safely(sheet, "price_block", lambda: hist.setdefault("h", price_block(sheet, tk, snap_session)))
    if "h" in hist:
        safely(sheet, "past_prints", lambda: past_prints(sheet, tk, hist["h"], report_date))
    safely(sheet, "expectations", lambda: expectations(sheet, tk))
    safely(sheet, "options", lambda: options_block(sheet, chain, gate))
    safely(sheet, "calendar", lambda: calendar_block(sheet, ticker, report_date))
    safely(sheet, "stage", lambda: stage_block(sheet, ticker, meta["captured_et"][:10]))
    out = {"meta": meta, "factors": sheet}
    (write_json if dry else write_once)(os.path.join(base, "factors.json"), out)
    print(json.dumps({k: v.get("value") for k, v in sheet.items() if k != "E_last4_prints"}, indent=1, default=str))
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    run(a[0], a[1], datetime.date.fromisoformat(a[2]), dry="--dry" in a)
