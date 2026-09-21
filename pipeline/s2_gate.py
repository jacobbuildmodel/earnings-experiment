"""D003 S2 - the per-event gate, plus the full option-chain capture.

    python pipeline/s2_gate.py <season> <TICKER> <YYYY-MM-DD>           # live: inside the S2 window only
    python pipeline/s2_gate.py <season> <TICKER> <YYYY-MM-DD> --dry     # test: anywhere, writes to cache/dry/

Needs events/<season>/<TICKER>_<date>/confirm.json, written by hand from the COMPANY source:
    {"session": "BMO"|"AMC", "company_source": {"url": ..., "quote": ..., "retrieved_et": ...},
     "session_from_call_time": false}
"""
import datetime
import json
import math
import os
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ET, ROOT, WEB_HEADERS, now_et, registry, write_json, write_once  # noqa: E402
from sessions import shift, timing  # noqa: E402

D001 = registry("D001_outcome_v1.json")
D003 = registry("D003_universe_screen_v1.json")
S2 = D003["s2"]


def num(x):
    try:
        x = float(x)
        return None if math.isnan(x) else x
    except (TypeError, ValueError):
        return None


def session_from_ts(ts):
    t = ts.astimezone(ET).time()
    if t < datetime.time(9, 30):
        return "BMO"
    if t >= datetime.time(16, 0):
        return "AMC"
    return "INTRADAY"


def second_sources(ticker, report_date):
    import yfinance as yf
    found = []
    try:
        ed = yf.Ticker(ticker).get_earnings_dates(limit=12)
        for ts in ed.index:
            if ts.astimezone(ET).date() == report_date:
                found.append({"source": "yfinance get_earnings_dates", "timestamp": ts.isoformat(),
                              "session": session_from_ts(ts)})
    except Exception as exc:
        found.append({"source": "yfinance get_earnings_dates", "error": f"{type(exc).__name__}: {exc}"})
    try:
        r = requests.get("https://api.nasdaq.com/api/calendar/earnings",
                         params={"date": report_date.isoformat()}, headers=WEB_HEADERS, timeout=30)
        rows = (r.json().get("data") or {}).get("rows") or []
        for row in rows:
            if row["symbol"].upper() == ticker:
                sess = {"time-pre-market": "BMO", "time-after-hours": "AMC"}.get(row.get("time"))
                found.append({"source": "nasdaq calendar", "time": row.get("time"), "session": sess})
    except Exception as exc:
        found.append({"source": "nasdaq calendar", "error": f"{type(exc).__name__}: {exc}"})
    return found


def chain_gate(ticker, reaction_day, dry=False):
    import yfinance as yf
    tk = yf.Ticker(ticker)
    spot = num(tk.fast_info["last_price"])
    expiries = [e for e in tk.options if datetime.date.fromisoformat(e) >= reaction_day]
    if not expiries:
        return {"status": "INELIGIBLE", "reason": "no_expiry"}, None
    expiry = expiries[0]

    def fetch():
        c = tk.option_chain(expiry)
        return c.calls, c.puts

    calls, puts = fetch()
    strikes = sorted(set(calls.strike) & set(puts.strike))
    if not strikes or spot is None:
        full = {"expiry": expiry, "calls": calls.to_dict("records"), "puts": puts.to_dict("records"),
                "all_expiries": list(tk.options)}
        return {"status": "INELIGIBLE", "reason": "no_quote", "spot": spot, "expiry": expiry,
                "detail": "no spot price" if spot is None else "no strike listed for both calls and puts"}, full
    strike = min(strikes, key=lambda k: (abs(k - spot), k))

    def legs(calls, puts):
        c = calls[calls.strike == strike].iloc[0]
        p = puts[puts.strike == strike].iloc[0]
        return ({k: num(c[k]) for k in ("bid", "ask", "openInterest", "lastPrice", "impliedVolatility")},
                {k: num(p[k]) for k in ("bid", "ask", "openInterest", "lastPrice", "impliedVolatility")})

    call, put = legs(calls, puts)
    quoted = lambda l: (l["bid"] or 0) > 0 and (l["ask"] or 0) > (l["bid"] or 0)  # noqa: E731
    retried = False
    if not (quoted(call) and quoted(put)):
        retried = True
        time.sleep(0 if dry else S2["quote_retry_minutes"] * 60)
        calls, puts = fetch()
        call, put = legs(calls, puts)

    rec = {"spot": spot, "expiry": expiry, "strike": strike, "call": call, "put": put,
           "quote_retried": retried, "flags": []}
    exp_d = datetime.date.fromisoformat(expiry)
    gap = sum(1 for i in range(1, 30) if shift(reaction_day, i) <= exp_d)
    rec["expiry_sessions_after_reaction"] = gap
    if gap > S2["diluted_flag_if_expiry_sessions_after_reaction_gt"]:
        rec["flags"].append("diluted_implied_move")

    if not (quoted(call) and quoted(put)):
        rec.update(status="INELIGIBLE", reason="no_quote")
    else:
        mid = lambda l: (l["bid"] + l["ask"]) / 2  # noqa: E731
        rec["implied_move"] = (mid(call) + mid(put)) / spot
        rec["rel_spread"] = {"call": (call["ask"] - call["bid"]) / mid(call), "put": (put["ask"] - put["bid"]) / mid(put)}
        rec["oi_sum"] = (call["openInterest"] or 0) + (put["openInterest"] or 0)
        if rec["implied_move"] < S2["implied_move_min"]:
            rec.update(status="INELIGIBLE", reason="low_implied_move")
        elif max(rec["rel_spread"].values()) > S2["max_rel_spread_each_leg"]:
            rec.update(status="INELIGIBLE", reason="wide_spread")
        elif rec["oi_sum"] < S2["min_oi_call_plus_put"]:
            rec.update(status="INELIGIBLE", reason="thin_oi")
        else:
            rec.update(status="PASS")
    full = {"expiry": expiry, "calls": calls.to_dict("records"), "puts": puts.to_dict("records"),
            "all_expiries": list(tk.options)}
    return rec, full


def run(season, ticker, report_date, dry=False):
    ticker = ticker.upper()
    edir = os.path.join(ROOT, "events", season, f"{ticker}_{report_date.isoformat()}")
    cdir = os.path.join(ROOT, "cache", "dry", f"{ticker}_{report_date}") if dry else edir
    confirm = json.load(open(os.path.join(cdir, "confirm.json"), encoding="utf-8"))
    session = confirm["session"]
    tm = timing(report_date, session, D001)
    snap_session = shift(report_date, S2["snapshot_session"][session])
    now = now_et()
    lo, hi = (datetime.datetime.combine(snap_session, datetime.time.fromisoformat(x), ET) for x in S2["window_et"])
    in_window = lo <= now <= hi
    if not in_window and not dry:
        raise SystemExit(f"ET {now:%Y-%m-%d %H:%M} is outside the S2 window {lo:%Y-%m-%d %H:%M}-{hi:%H:%M}")

    window = D003["seasons"][season]["window"]
    gate = {"season": season, "ticker": ticker, "report_date": report_date.isoformat(), "session": session,
            "timing": tm, "snapshot_session": snap_session.isoformat(), "captured_et": now.isoformat(),
            "in_s2_window": in_window, "dry": dry, "rule": "D003_universe_screen_v1 §6",
            "company_source": confirm["company_source"], "flags": []}
    if confirm.get("session_from_call_time"):
        gate["flags"].append("session_from_call_time")

    seconds = second_sources(ticker, report_date)
    gate["second_sources"] = seconds
    agree = [s for s in seconds if s.get("session") == session]
    disagree = [s for s in seconds if s.get("session") and s.get("session") != session]
    in_season = window[0] <= report_date.isoformat() <= window[1]

    full = None
    if not confirm["company_source"].get("url"):
        gate.update(status="INELIGIBLE", reason="unconfirmed", detail="no company source")
    elif not in_season:
        gate.update(status="INELIGIBLE", reason="outside_window")
    elif disagree or not agree:
        gate.update(status="INELIGIBLE", reason="unconfirmed",
                    detail="second source disagrees" if disagree else "no second source for date+session")
    else:
        gate["second_source_used"] = agree[0]
        opt, full = chain_gate(ticker, datetime.date.fromisoformat(tm["reaction_day"]), dry)
        gate["options"] = opt
        gate["flags"] += opt.pop("flags", [])
        gate.update(status=opt.pop("status"), reason=opt.pop("reason", None))
    if full is None:  # capture the chain anyway (literature review §6), without a gate reading
        try:
            _, full = chain_gate(ticker, datetime.date.fromisoformat(tm["reaction_day"]), dry)
        except Exception as exc:
            full = {"error": f"{type(exc).__name__}: {exc}"}

    target = os.path.join(ROOT, "cache", "dry", f"{ticker}_{report_date}") if dry else edir
    save = write_json if dry else write_once
    save(os.path.join(target, "gate.json"), gate)
    save(os.path.join(target, "option_chain.json"), full)
    print(f"{ticker} {report_date} {session}: {gate['status']} {gate.get('reason') or ''} "
          f"implied_move={gate.get('options', {}).get('implied_move')}")
    return gate


if __name__ == "__main__":
    a = sys.argv[1:]
    run(a[0], a[1], datetime.date.fromisoformat(a[2]), dry="--dry" in a)
