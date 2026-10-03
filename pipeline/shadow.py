"""D009 shadow tracks - code only. Registered, graded and reported like the scored tracks, labelled
SHADOW, and never allowed to touch them (CHARTER §3.8; registry/D009_shadow_tracks_v1.md).

    python pipeline/shadow.py capture                 # the session's Nasdaq calendar -> shadow/calendar/<date>.json
    python pipeline/shadow.py grade <season> [--no-fetch]   # build the events, fetch settled prices once, recompute
    python pipeline/shadow.py report <season> [--write]     # the D009 statistics
    python pipeline/shadow.py report-pooled <seasonA> <seasonB> [--write] [--final]  # D009 §5 pooled verdict
    python pipeline/shadow.py commit                  # stage shadow/ and outcomes/shadow/, commit, push

Tracks (D009 §2-§4):
  SH-W  T0-wide: every allowlist event with a company-confirmed date and session, gate or no gate
        (gated out, missed window, T2 missing - all graded). Confirmation committed before the entry open.
  SH-M  market-wide: every name of the season's frozen S1 calendar capture that is a US-listed domestic
        common stock of >= $2B, on ANY industry, dated by the calendar captured on its snapshot session.
  SH-X  short straddle: every gated event whose gate recorded both ATM legs - sell call + put at the bid
        at the snapshot, hold to expiry, pay intrinsic value at the expiry close.

Outcomes go to outcomes/shadow/<season>/, which the T2 step never has on disk (D004: T2 does not see
this season's outcomes). Calendar captures go to shadow/calendar/ - they hold no outcome.
"""
import datetime
import glob
import json
import math
import os
import subprocess
import sys
import time

import numpy as np
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ET, ROOT, WEB_HEADERS, Sec, now_et, registry, rule_for, write_json, write_once  # noqa: E402
from sessions import is_session, shift, timing  # noqa: E402

D001 = registry("D001_outcome_v1.json")
CAL_DIR = os.path.join(ROOT, "shadow", "calendar")
COST = 0.002          # D008 / D001 secondary: 0.20% round trip
EXCHANGES = {"NMS": "Nasdaq", "NGM": "Nasdaq", "NCM": "Nasdaq", "NYQ": "NYSE", "ASE": "NYSE American"}
DOMESTIC = {"10-K", "10-Q", "10-K/A", "10-Q/A"}
PERIODIC = DOMESTIC | {"20-F", "40-F", "20-F/A", "40-F/A"}
NASDAQ_SESSION = {"time-pre-market": "BMO", "time-after-hours": "AMC"}
CAPTURE_DAYS = 6       # weekdays ahead
YF_FALLBACK_CAP = 1.5e9  # yfinance session lookup only for rows Nasdaq sizes above this (calls are slow)


def sh(path):
    return os.path.join(ROOT, path)


def load(path):
    return json.load(open(path, encoding="utf-8"))


def d(s):
    return datetime.date.fromisoformat(s)


def committed_at(path):
    """First commit that added the file (ISO), or None if it was never committed."""
    rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
    out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%cI", "--", rel],
                         cwd=ROOT, capture_output=True, text=True).stdout.split()
    return datetime.datetime.fromisoformat(out[-1]) if out else None


def entry_open_dt(entry_session):
    return datetime.datetime.combine(d(entry_session), datetime.time(9, 30), ET)


# ---------------------------------------------------------------- capture (D009 §3.2)

def parse_cap(s):
    try:
        return float(str(s).replace("$", "").replace(",", ""))
    except (TypeError, ValueError):
        return None


def yf_session(t, date):
    """yfinance timestamped earnings date -> BMO / AMC / None (CLAUDE.md: .calendar is a day late for AMC)."""
    import yfinance as yf
    try:
        df = yf.Ticker(t).get_earnings_dates(limit=6)
    except Exception as exc:
        return None, f"{type(exc).__name__}"
    if df is None or not len(df):
        return None, "no dates"
    for ts in df.index:
        x = ts.tz_convert(ET)
        if x.date().isoformat() == date:
            tm = x.time()
            if tm < datetime.time(9, 30):
                return "BMO", x.isoformat()
            if tm >= datetime.time(16, 0):
                return "AMC", x.isoformat()
            return None, f"intraday {x.isoformat()}"
    return None, "date not listed"


def capture(last_chance=False):
    """Once per session day: the Nasdaq calendar for the next CAPTURE_DAYS weekdays. Write-once - the
    first COMPLETE capture of the day is the one in force. Rows with no session get one yfinance lookup
    when Nasdaq sizes the company at >= $1.5B. A capture with a failed day is NOT written (a later fire
    retries) unless last_chance (the evening fire), when it is written with the failed days flagged.
    Exits 2 when a day failed, so the workflow shows it (review 2026-10-02, finding 1)."""
    now = now_et()
    today = now.date()
    if not is_session(today):
        print(f"{today} is not a session - no capture")
        return None
    path = os.path.join(CAL_DIR, f"{today.isoformat()}.json")
    if os.path.exists(path):
        print(f"{path} exists - the first capture of the day is the one in force")
        return None
    days, x = {}, today
    while len(days) < CAPTURE_DAYS:
        x += datetime.timedelta(days=1)
        if x.weekday() >= 5:
            continue
        rows = None
        for attempt in range(4):
            try:
                r = requests.get("https://api.nasdaq.com/api/calendar/earnings", params={"date": x.isoformat()},
                                 headers=WEB_HEADERS, timeout=30)
                r.raise_for_status()
                rows = (r.json().get("data") or {}).get("rows") or []
                break
            except (requests.RequestException, ValueError) as exc:
                err = f"{type(exc).__name__}: {exc}"
                time.sleep(3 * (attempt + 1))
        days[x.isoformat()] = ({"rows": [{"symbol": it["symbol"].strip().upper(), "time": it.get("time"),
                                          "marketCap": it.get("marketCap"), "name": it.get("name")} for it in rows]}
                               if rows is not None else {"error": err})
        time.sleep(1)
    failed = [k for k, v in days.items() if "error" in v]
    if failed and not last_chance:
        print(f"::error::Nasdaq failed for {failed} - capture NOT written; a later fire retries")
        raise SystemExit(2)
    looked = 0
    for date, v in days.items():
        for row in v.get("rows", []):
            row["session"] = NASDAQ_SESSION.get(row["time"])
            if row["session"] is None and (parse_cap(row["marketCap"]) or 0) >= YF_FALLBACK_CAP:
                row["session"], row["yf"] = yf_session(row["symbol"], date)
                row["session_source"] = "yfinance get_earnings_dates" if row["session"] else None
                looked += 1
                time.sleep(0.3)
            elif row["session"]:
                row["session_source"] = "nasdaq"
    out = {"captured_et": now.isoformat(timespec="seconds"), "finished_et": now_et().isoformat(timespec="seconds"),
           "session_day": today.isoformat(), "source": "api.nasdaq.com/api/calendar/earnings (+ yfinance where no time)",
           "rule": "D009 §3.2", "yfinance_lookups": looked, "failed_days": failed, "days": days}
    write_once(path, out)
    n = sum(len(v.get("rows", [])) for v in days.values())
    print(f"captured {n} calendar rows for {list(days)} ({looked} yfinance session lookups)")
    if failed:
        print(f"::error::written at last chance with failed days {failed}")
    return path


# ---------------------------------------------------------------- event sets

def sh_w_events(season):
    """SH-W (D009 §2): one event per events/<season>/<T>_<D>/confirm.json committed before its entry open."""
    rule = D001
    out = []
    for cp in sorted(glob.glob(os.path.join(ROOT, "events", season, "*", "confirm.json"))):
        edir = os.path.dirname(cp)
        t, date = os.path.basename(edir).rsplit("_", 1)
        conf = load(cp)
        sess = conf.get("session")
        if sess not in ("BMO", "AMC"):
            continue
        try:
            tm = timing(d(date), sess, rule)
        except ValueError as exc:
            print(f"{t} {date}: skipped - {exc}")
            continue
        when = committed_at(cp)
        man = os.path.join(edir, "manifest.json")
        gate_status = load(man)["status"] if os.path.exists(man) else None
        ev = {"track": "SH-W", "ticker": t, "date": date, "session": sess, "timing": tm,
              "confirm_committed": when.isoformat() if when else None,
              "gate_status": gate_status, "exists_before_entry": bool(when and when < entry_open_dt(tm["entry"]["session"]))}
        out.append(ev)
    return out


def sh_m_universe(season):
    """SH-M universe (D009 §3.1): the season's frozen S1 raw capture, any industry. Domestic-filer test is
    applied at grading (it needs the SEC, and only for names that formed an event)."""
    raw = os.path.join(ROOT, "universe", season, "raw")
    mk = os.path.join(raw, "yfinance_market.json")
    if not os.path.exists(mk):
        return {}
    import s1_screen
    rule = rule_for("D003_universe_screen", season)
    s1_screen.RULE = rule
    s1 = rule["s1"]
    out = {}
    when = committed_at(mk)
    for t, m in load(mk)["tickers"].items():
        if "error" in m or m.get("skipped") or s1_screen.ticker_excluded(t):
            continue
        if m.get("quoteType") != s1["quote_type"] or EXCHANGES.get(m.get("exchange")) not in s1["exchanges"]:
            continue
        if (m.get("currency") or "USD") != "USD" or (m.get("industry") in s1["exclude_industries"]):
            continue
        if not m.get("marketCap") or m["marketCap"] < s1["market_cap_min"]:
            continue
        out[t] = {"industry": m.get("industry"), "sector": m.get("sector"), "marketCap": m["marketCap"],
                  "universe_committed": when.isoformat() if when else None}
    return out


def captures():
    caps = {}
    for p in sorted(glob.glob(os.path.join(CAL_DIR, "*.json"))):
        caps[os.path.basename(p)[:-5]] = p
    return caps


def sh_m_events(season, universe):
    """SH-M (D009 §3.2): an event is (name, D, session) as listed in the capture taken ON its snapshot
    session (BMO: D-2 sessions, AMC: D-1). No capture that day -> no event (counted)."""
    rule = rule_for("D003_universe_screen", season)
    lo, hi = rule["seasons"][season]["window"]
    snap_off = rule["s2"]["snapshot_session"]
    caps = captures()
    out, missing_capture, no_session = [], set(), 0
    seen = set()
    for day, p in caps.items():
        c = load(p)
        for date, v in c["days"].items():
            if not (lo <= date <= hi) or not is_session(d(date)):
                continue
            for row in v.get("rows", []):
                t = row["symbol"]
                if t not in universe:
                    continue
                if row.get("session") not in ("BMO", "AMC"):
                    no_session += 1
                    continue
                snap = shift(d(date), snap_off[row["session"]]).isoformat()
                if snap != day or (t, date) in seen:
                    continue
                seen.add((t, date))
                try:
                    tm = timing(d(date), row["session"], D001)
                except ValueError:
                    continue
                when = committed_at(p)
                u_when = universe[t]["universe_committed"]
                if u_when and when:
                    when = max(when, datetime.datetime.fromisoformat(u_when))
                elif not u_when:
                    when = None
                out.append({"track": "SH-M", "ticker": t, "date": date, "session": row["session"],
                            "session_source": row.get("session_source"), "timing": tm, "snapshot": snap,
                            "capture": os.path.relpath(p, ROOT).replace(os.sep, "/"),
                            "capture_committed": when.isoformat() if when else None,
                            "exists_before_entry": bool(when and when < entry_open_dt(tm["entry"]["session"])),
                            **universe[t]})
    # D003 v3 by analogy: share classes of one issuer (same SEC CIK) are one event - alphabetically first
    sec = Sec(os.path.join(ROOT, "cache", "sec"))
    kept, seen = [], set()
    for ev in sorted(out, key=lambda e: (e["date"], e["ticker"])):
        cik = sec.cik(ev["ticker"])
        k = (cik or ev["ticker"], ev["date"])
        if k in seen:
            continue
        seen.add(k)
        kept.append(ev)
    return kept, {"rows_without_session": no_session, "capture_days": sorted(caps)}


def sh_x_events(season):
    """SH-X (D009 §4): every gate.json with both ATM legs quoted."""
    out = []
    for gp in sorted(glob.glob(os.path.join(ROOT, "events", season, "*", "gate.json"))):
        g = load(gp)
        o = g.get("options") or {}
        c, p = o.get("call") or {}, o.get("put") or {}
        if not (o.get("expiry") and o.get("strike") and c.get("bid") is not None and p.get("bid") is not None
                and o.get("spot")):
            continue
        out.append({"track": "SH-X", "ticker": g["ticker"], "date": g["report_date"], "session": g["session"],
                    "timing": g["timing"], "gate_status": g.get("status"), "expiry": o["expiry"], "strike": o["strike"],
                    "spot": o["spot"], "call_bid": c["bid"], "put_bid": p["bid"], "call_ask": c.get("ask"),
                    "put_ask": p.get("ask"), "implied_move": o.get("implied_move"),
                    "exists_before_entry": bool(committed_at(gp) and committed_at(gp) < entry_open_dt(g["timing"]["entry"]["session"]))})
    return out


# ---------------------------------------------------------------- prices (fetch once)

def settled(session):
    nxt = d(session) + datetime.timedelta(days=1)
    return now_et() >= datetime.datetime.combine(nxt, datetime.time(6, 0), ET)


class Prices:
    """outcomes/shadow/<season>/prices.jsonl - one row per (symbol, session, field), never rewritten."""

    def __init__(self, season):
        self.path = os.path.join(ROOT, "outcomes", "shadow", season, "prices.jsonl")
        self.rows = {}
        if os.path.exists(self.path):
            for line in open(self.path, encoding="utf-8"):
                r = json.loads(line)
                self.rows[(r["symbol"], r["session"], r["field"])] = r
        self.new = []

    def get(self, sym, session, field):
        r = self.rows.get((sym, session, field))
        return None if r is None else r["value"]

    def add(self, sym, session, field, value):
        k = (sym, session, field)
        if k in self.rows:
            return
        r = {"symbol": sym, "session": session, "field": field, "value": value, "source": "yfinance",
             "fetched_et": now_et().isoformat(timespec="seconds")}
        self.rows[k] = r
        self.new.append(r)

    def save(self):
        if not self.new:
            return
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "a", encoding="utf-8", newline="\n") as f:
            for r in self.new:
                f.write(json.dumps(r) + "\n")
        self.new = []


def fetch(prices, needs):
    """needs: {symbol: set((session, field))}. Daily bars, auto_adjust=False, in batches; settled only.
    Also records 'vol60' (annualised stdev of 60 daily close returns to the snapshot session) and
    dividends in the window. A failed fetch leaves the field missing - never filled."""
    import yfinance as yf
    todo = {s: {(ss, f) for ss, f in v if settled(ss) and prices.get(s, ss, f) is None} for s, v in needs.items()}
    todo = {s: v for s, v in todo.items() if v}
    syms = sorted(todo)
    for i in range(0, len(syms), 40):
        batch = syms[i:i + 40]
        sess = [d(ss) for s in batch for ss, _ in todo[s]]
        start = (min(sess) - datetime.timedelta(days=130)).isoformat()
        end = (max(sess) + datetime.timedelta(days=2)).isoformat()
        try:
            h = yf.download(batch, start=start, end=end, auto_adjust=False, actions=True, group_by="ticker",
                            progress=False, threads=True)
        except Exception as exc:
            print(f"yfinance batch failed: {type(exc).__name__}: {exc}")
            continue
        for s in batch:
            try:
                multi = hasattr(h.columns, "levels") and s in h.columns.get_level_values(0)
                df = (h[s] if multi else h).dropna(subset=["Open"])
            except Exception as exc:
                print(f"{s}: no bars ({type(exc).__name__}: {exc})")
                continue
            idx = [x.date().isoformat() if hasattr(x, "date") else str(x)[:10] for x in df.index]
            df.index = idx
            for ss, f in todo[s]:
                if f in ("open", "close"):
                    if ss in df.index:
                        v = df.loc[ss, "Open" if f == "open" else "Close"]
                        if v == v:
                            prices.add(s, ss, f, round(float(v), 4))
                elif f == "vol60":
                    # history_factors.py H4: stdev of 60 daily pct changes of ADJUSTED closes x sqrt(252),
                    # and the snapshot session's own bar must exist (no stale last bar)
                    col = "Adj Close" if "Adj Close" in df else "Close"
                    c = df[col][[x <= ss for x in df.index]].astype(float)
                    if len(c) and c.index[-1] == ss:
                        r = c.pct_change().dropna().values[-60:]
                        if len(r) >= 60:
                            prices.add(s, ss, f, round(float(np.std(r, ddof=1) * math.sqrt(252)), 6))
                elif f.startswith("div:") or f.startswith("split:"):
                    lo, colname = f.split(":", 1)[1], ("Dividends" if f.startswith("div:") else "Stock Splits")
                    if colname in df and ss in df.index:
                        v = [float(df.loc[x, colname]) for x in df.index if lo < x <= ss and df.loc[x, colname]]
                        prices.add(s, ss, f, float(sum(v)) if colname == "Dividends" else v)
        time.sleep(1)
    prices.save()


# ---------------------------------------------------------------- timing check (SEC 8-K item 2.02)

def sec_timing(sec, t, date, session, cache):
    """verified / contradicted / early / late / unverified / no_cik / foreign, from the 2.02 8-K."""
    cik = sec.cik(t)
    if not cik:
        return "no_cik", []
    if cik not in cache:
        try:
            cache[cik] = sec.submission(cik)
        except Exception as exc:
            return f"sec_error {type(exc).__name__}", []
    rec = cache[cik]["filings"]["recent"]
    periodic = [(rec["filingDate"][i], f) for i, f in enumerate(rec["form"]) if f in PERIODIC and rec["filingDate"][i] <= date]
    if periodic and max(periodic)[1] not in DOMESTIC:
        return "foreign", []
    D = d(date)
    prev_close = datetime.datetime.combine(shift(D, -1), datetime.time(16, 0), ET)
    d_open = datetime.datetime.combine(D, datetime.time(9, 30), ET)
    d_close = datetime.datetime.combine(D, datetime.time(16, 0), ET)
    next_open = datetime.datetime.combine(shift(D, 1), datetime.time(9, 30), ET)
    win = {"BMO": (prev_close, d_open), "AMC": (d_close, next_open)}
    lo = (D - datetime.timedelta(days=3)).isoformat()
    hi = (D + datetime.timedelta(days=10)).isoformat()
    hits = []
    for i, form in enumerate(rec["form"]):
        if form.startswith("8-K") and lo <= rec["filingDate"][i] <= hi and "2.02" in rec["items"][i].split(","):
            x = datetime.datetime.fromisoformat(rec["acceptanceDateTime"][i].replace("Z", "+00:00")).astimezone(ET)
            hits.append({"accepted_et": x.isoformat(), "window": next((k for k, (a, b) in win.items() if a <= x < b), "other")})
    if any(h["window"] == session for h in hits):
        return "verified", hits
    if any(h["window"] == ("AMC" if session == "BMO" else "BMO") for h in hits):
        return "contradicted", hits
    if any(datetime.datetime.fromisoformat(h["accepted_et"]) < win[session][0] for h in hits):
        return "early", hits
    # Late: every 2.02 8-K came after the exit-A open had already been reached by a full session close,
    # i.e. the print fell after the trade ended. An 8-K that merely lags its release within the reaction
    # day (BB 2026-09-24: release before the open, 8-K at 11:12) is NOT late - that stays unverified.
    late_from = datetime.datetime.combine(D if session == "BMO" else shift(D, 1), datetime.time(16, 0), ET)
    if hits and all(datetime.datetime.fromisoformat(h["accepted_et"]) >= late_from for h in hits):
        return "late", hits
    return "unverified", hits


# ---------------------------------------------------------------- grading (pure, from stored rows)

def stock_leg(prices, ev):
    tm = ev["timing"]
    e_s, x_s = tm["entry"]["session"], tm["exit_A"]["session"]
    e, x = prices.get(ev["ticker"], e_s, "open"), prices.get(ev["ticker"], x_s, "open")
    if e is None or x is None:
        return None
    div = prices.get(ev["ticker"], x_s, f"div:{e_s}")
    if div is None:  # the dividend field must be present, never assumed 0 (review finding 9)
        return None
    r = (x + div) / e - 1
    out = {"entry": e, "exit": x, "dividends": div, "raw_return": r, "net_return": r - COST, "WIN_raw": r > 0,
           "splits_in_window": [x for x in (prices.get(ev["ticker"], x_s, f"split:{e_s}") or []) if x]}
    # descriptive (D009 §5 note): minus SPY over the same opens, beta 1 - so a result is not just the market
    se, sx = prices.get("SPY", e_s, "open"), prices.get("SPY", x_s, "open")
    if se and sx:
        out["spy_return"] = sx / se - 1
        out["excess_spy"] = r - out["spy_return"]
    return out


def straddle(prices, ev):
    """Sell call + put at the bid at the snapshot; at the expiry close pay |S - K|. Per $1 of spot."""
    s = prices.get(ev["ticker"], ev["expiry"], "close")
    if s is None:
        return None
    prem = ev["call_bid"] + ev["put_bid"]
    payoff = abs(s - ev["strike"])
    mid = None
    if ev.get("call_ask") is not None and ev.get("put_ask") is not None:
        mid = ((ev["call_bid"] + ev["call_ask"]) / 2 + (ev["put_bid"] + ev["put_ask"]) / 2 - payoff) / ev["spot"]
    return {"expiry_close": s, "premium_bid": prem, "payoff": payoff, "pnl_on_spot": (prem - payoff) / ev["spot"],
            "pnl_on_spot_mid": mid, "realised_move": abs(s / ev["spot"] - 1)}


def grade_one(ev, prices, sec, subs, tstore, do_fetch):
    """D009 §1: existence before entry, the 2.02 8-K timing check (all three tracks), splits, then the leg."""
    key = f"{ev['ticker']}_{ev['date']}_{ev['session']}"
    out = dict(ev)
    out["void"] = None
    flags = []
    if not ev["exists_before_entry"]:
        out["void"] = "not_committed_before_entry"
    x_s = ev["timing"]["exit_A"]["session"]
    if do_fetch and settled(x_s) and (key not in tstore or not tstore[key].get("final")):
        st, hits = sec_timing(sec, ev["ticker"], ev["date"], ev["session"], subs)
        # a fetch error is never final (review finding 5): it is retried on the next run
        final = not st.startswith("sec_error") and now_et().date() > d(ev["date"]) + datetime.timedelta(days=10)
        tstore[key] = {"status": st, "hits": hits, "checked_et": now_et().isoformat(timespec="seconds"), "final": final}
    tc = tstore.get(key, {}).get("status", "pending")
    out["timing_check"] = tc
    out["timing_final"] = tstore.get(key, {}).get("final", False)
    if tc in ("contradicted", "early"):
        out["void"] = out["void"] or f"print_{tc}"
    if tc == "late":
        # stock tracks: graded, flagged, reported with and without (an 8-K may lag its release by up to four
        # business days). The straddle: VOID - a print after expiry would hand it a free premium.
        flags.append("late_8k")
        if ev["track"] == "SH-X":
            out["void"] = out["void"] or "print_late"
    if tc == "unverified":
        flags.append("timing_unverified")
    if ev["track"] == "SH-M" and tc in ("foreign", "no_cik"):
        out["void"] = out["void"] or f"not_domestic_{tc}"
    ready = tc not in ("pending",) and not tc.startswith("sec_error")
    if ev["track"] in ("SH-W", "SH-M"):
        leg = stock_leg(prices, ev)
        out["exit_A"] = leg
        e_s = ev["timing"]["entry"]["session"]
        out["vol60"] = prices.get(ev["ticker"], shift(d(e_s), -1).isoformat(), "vol60")
        if leg and leg.get("splits_in_window"):
            out["void"] = out["void"] or "split_in_window"  # entry and exit may sit on different split bases
        out["graded"] = bool(leg) and out["void"] is None and ready and settled(x_s)
    else:
        sd = straddle(prices, ev)
        out["straddle"] = sd
        out["graded"] = bool(sd) and out["void"] is None and ready
    out["flags"] = flags
    return out


def grade(season, do_fetch=True):
    universe = sh_m_universe(season)
    w = sh_w_events(season)
    m, mstat = sh_m_events(season, universe)
    x = sh_x_events(season)
    prices = Prices(season)
    if do_fetch:
        needs = {}
        for ev in w + m:
            tm = ev["timing"]
            e_s, x_s = tm["entry"]["session"], tm["exit_A"]["session"]
            snap = shift(d(e_s), -1).isoformat()
            needs.setdefault(ev["ticker"], set()).update({(e_s, "open"), (x_s, "open"), (x_s, f"div:{e_s}"),
                                                          (x_s, f"split:{e_s}"), (snap, "vol60")})
            needs.setdefault("SPY", set()).update({(e_s, "open"), (x_s, "open")})
        for ev in x:
            needs.setdefault(ev["ticker"], set()).add((ev["expiry"], "close"))
        fetch(prices, needs)
    sec = Sec(os.path.join(ROOT, "cache", "sec"))
    subs = {}
    tpath = os.path.join(ROOT, "outcomes", "shadow", season, "timing.json")
    tstore = load(tpath) if os.path.exists(tpath) else {}
    rows = []
    for ev in w + m + x:
        try:
            rows.append(grade_one(ev, prices, sec, subs, tstore, do_fetch))
        except Exception as exc:  # one bad event never stops the season (review finding 12)
            print(f"{ev['track']} {ev['ticker']} {ev['date']}: grading failed: {type(exc).__name__}: {exc}")
            rows.append({**ev, "void": None, "graded": False, "error": f"{type(exc).__name__}: {exc}"})
    write_json(tpath, tstore)
    write_json(os.path.join(ROOT, "outcomes", "shadow", season, "graded.json"),
               {"season": season, "rule": "D009_shadow_tracks_v1", "graded_by": "pipeline/shadow.py",
                "graded_et": now_et().isoformat(timespec="seconds"), "sh_m_universe": len(universe),
                "sh_m_stats": mstat, "events": rows})
    for tr in ("SH-W", "SH-M", "SH-X"):
        r = [e for e in rows if e["track"] == tr]
        print(f"{season} {tr}: {len(r)} events, {sum(e['graded'] for e in r)} graded, "
              f"{sum(1 for e in r if e['void'])} void")
    return rows


# ---------------------------------------------------------------- statistics (D009 §5)

def mean_test(y, g, name):
    """Mean > 0, one-sided: cluster-robust t by entry session and the D005 restricted wild cluster
    bootstrap (report.wild_p_k with an intercept-only model)."""
    import report
    y = np.asarray(y, float)
    g = np.asarray(g)
    if len(y) < 3 or len(set(g)) < 2:
        return {"n": len(y), "dates": len(set(g)), "mean": float(y.mean()) if len(y) else None, "note": "too few"}
    X = np.ones((len(y), 1))
    b, se, t = report.ols_k(y, X, g, 0)
    p = report.wild_p_k(y, X, g, 0, report.R(name))
    return {"n": len(y), "dates": len(set(g)), "mean": b, "se": se, "t": t, "p_one_sided": p,
            "status": "insufficient" if not report.sufficient(len(y), len(set(g))) else ("p<0.05" if p < 0.05 else "p>=0.05")}


def diff_test(y, x, g, name):
    import report
    y, x, g = np.asarray(y, float), np.asarray(x, float), np.asarray(g)
    if len(y) < 3 or len(set(x)) < 2 or len(set(g)) < 2:
        return {"n": len(y), "note": "too few"}
    X = np.column_stack([np.ones_like(x), x])
    b, se, t = report.ols_k(y, X, g, 1)
    p = report.wild_p_k(y, X, g, 1, report.R(name))
    return {"n": len(y), "dates": len(set(g)), "diff": b, "se": se, "t": t, "p_one_sided": p,
            "status": "insufficient" if not report.sufficient(len(y), len(set(g))) else ("p<0.05" if p < 0.05 else "p>=0.05")}


FAMILY = ("H-M", "H-X", "H-VOL")   # D009 §5: Holm over exactly these three, always m = 3


def mde(res):
    """Minimum detectable effect at one-sided 5% with 80% power: (1.645 + 0.842) x clustered se."""
    se = res.get("se")
    return None if se is None or se != se else 2.487 * se


def stats_(allrows, final=False):
    """D009 §5 over one list of shadow rows: the H-M / H-X / H-VOL family (Holm, m = 3), the
    sensitivity without unverified timing, and the descriptive block. Shared by report_ (one season) and
    report_pooled (Seasons A + B, D009 §5's registered verdict)."""
    import report
    rows = [e for e in allrows if e.get("graded")]
    W = [e for e in rows if e["track"] == "SH-W"]
    M = [e for e in rows if e["track"] == "SH-M"]
    X = [e for e in rows if e["track"] == "SH-X"]
    clean = lambda rs: [e for e in rs if not set(e.get("flags", [])) & {"timing_unverified", "late_8k"}]  # noqa: E731
    g = lambda rs: [e["timing"]["entry"]["session"] for e in rs]  # noqa: E731
    res = {}
    res["H-M"] = mean_test([e["exit_A"]["net_return"] for e in M], g(M), "H-M")
    res["H-X"] = mean_test([e["straddle"]["pnl_on_spot"] for e in X], g(X), "H-X")
    mv = [e for e in M if e.get("vol60") is not None]
    if len(mv) >= 3:
        med = float(np.median([e["vol60"] for e in mv]))
        res["H-VOL"] = diff_test([e["exit_A"]["net_return"] for e in mv], [1.0 if e["vol60"] > med else 0.0 for e in mv], g(mv), "H-VOL")
        res["H-VOL"]["median_vol60"] = med
    else:
        res["H-VOL"] = {"n": len(mv), "note": "too few"}
    # a missing or NaN p counts as 1.0, so the family is always m = 3 (review finding 3)
    ps = {k: (res[k].get("p_one_sided") if res[k].get("p_one_sided") == res[k].get("p_one_sided")
              and res[k].get("p_one_sided") is not None else 1.0) for k in FAMILY}
    adj = report.holm(ps)
    for k in FAMILY:
        r = res[k]
        r["p_holm"] = adj[k]
        r["mde"] = mde(r)
        n, dates = r.get("n", 0), r.get("dates", 0) or 0
        if not report.sufficient(n, dates):
            r["status"] = "insufficient"
        elif not final:
            r["status"] = "interim (monitoring only)"
        else:
            r["status"] = ("p < 0.05 after Holm (shadow, secondary)" if adj[k] < 0.05 else
                           f"no evidence (shadow) - an effect smaller than {r['mde'] * 100:.2f} pts would usually be missed"
                           if r.get("mde") else "no evidence (shadow)")
    sens = {"H-M without unverified/late timing": mean_test([e["exit_A"]["net_return"] for e in clean(M)], g(clean(M)), "H-M-clean"),
            "H-X without unverified timing": mean_test([e["straddle"]["pnl_on_spot"] for e in clean(X)], g(clean(X)), "H-X-clean")}
    desc = {"SH-W net mean (descriptive, D009 §5)": mean_test([e["exit_A"]["net_return"] for e in W], g(W), "H-W"),
            "SH-W hit": float(np.mean([e["exit_A"]["WIN_raw"] for e in W])) if W else None,
            "SH-M hit": float(np.mean([e["exit_A"]["WIN_raw"] for e in M])) if M else None,
            "SH-M mean excess over SPY (net)": float(np.mean([e["exit_A"]["excess_spy"] - COST for e in M if "excess_spy" in e["exit_A"]]))
            if any("excess_spy" in e["exit_A"] for e in M) else None,
            "SH-W mean excess over SPY (net)": float(np.mean([e["exit_A"]["excess_spy"] - COST for e in W if "excess_spy" in e["exit_A"]]))
            if any("excess_spy" in e["exit_A"] for e in W) else None,
            "SH-X mean realised/implied": float(np.mean([e["straddle"]["realised_move"] / e["implied_move"] for e in X
                                                         if e.get("implied_move")])) if X else None,
            "events": {tr: {"total": sum(1 for e in allrows if e["track"] == tr),
                            "graded": sum(1 for e in allrows if e["track"] == tr and e.get("graded")),
                            "void": {v: sum(1 for e in allrows if e["track"] == tr and e.get("void") == v)
                                     for v in sorted({e.get("void") for e in allrows if e["track"] == tr and e.get("void")})}}
                       for tr in ("SH-W", "SH-M", "SH-X")}}
    return res, sens, desc


def print_(res, desc):
    for k, v in res.items():
        print(f"{k:6} n={v.get('n')} dates={v.get('dates')} "
              + (f"mean={v['mean'] * 100:+.2f}% " if v.get("mean") is not None else "")
              + (f"diff={v['diff'] * 100:+.2f}pt " if v.get("diff") is not None else "")
              + (f"t={v['t']:.2f} p={v['p_one_sided']:.3f} " if v.get("t") is not None and v["t"] == v["t"] else "")
              + f"holm={v['p_holm']:.3f} {v['status']}")
    print(json.dumps(desc, default=str))


def report_(season, write=False, final=False):
    """D009 §5. Interim runs are monitoring only; a verdict is printed with --final (season end = the
    season's last report date + 10 days, when every timing check is final)."""
    path = os.path.join(ROOT, "outcomes", "shadow", season, "graded.json")
    allrows = load(path)["events"]
    res, sens, desc = stats_(allrows, final)
    out = {"season": season, "rule": "D009_shadow_tracks_v1 §5", "run_et": now_et().isoformat(timespec="seconds"),
           "label": "SHADOW - secondary; never a scored track" + ("" if final else "; INTERIM - no verdict"),
           "tests": res, "sensitivity": sens, "descriptive": desc}
    print_(res, desc)
    if write:
        write_json(os.path.join(ROOT, "outcomes", "shadow", "reports", f"{season}_{now_et():%Y-%m-%d}.json"), out)
    return out


def pool(seasons_rows):
    """Concatenate seasons' shadow rows for the pooled report, each tagged with its season. Entry
    sessions are calendar dates, so clusters never merge across seasons. A (track, ticker, date, session)
    seen in an earlier season is dropped and counted - season windows do not overlap, so this is a guard,
    not a rule."""
    rows, seen, dropped = [], set(), []
    for season, srows in seasons_rows:
        for e in srows:
            key = (e["track"], e["ticker"], e["date"], e.get("session"))
            if key in seen:
                dropped.append({"season": season, "track": e["track"], "ticker": e["ticker"], "date": e["date"]})
                continue
            seen.add(key)
            rows.append({**e, "season": season})
    return rows, dropped


def report_pooled(seasons, write=False, final=False):
    """D009 §5's registered verdict: Seasons A and B POOLED - the same three tests, the same Holm m = 3,
    the same seeds by test name, the MDE and the sensitivity, over both seasons' graded events. H-VOL's
    median split is taken over the pooled sample. --final only at Season B's end (its last report date +
    10 days). The pilot is never pooled (D009 §6)."""
    if any(s.lower().startswith("pilot") for s in seasons):
        raise SystemExit("D009 §6: pilot numbers are never pooled into any season result")
    if len(set(seasons)) != len(seasons) or len(seasons) < 2:
        raise SystemExit("report-pooled needs two or more different seasons, e.g. seasonA seasonB")
    loaded = [(s, load(os.path.join(ROOT, "outcomes", "shadow", s, "graded.json"))["events"]) for s in seasons]
    allrows, dropped = pool(loaded)
    res, sens, desc = stats_(allrows, final)
    per = {s: {tr: {"total": sum(1 for e in allrows if e["season"] == s and e["track"] == tr),
                    "graded": sum(1 for e in allrows if e["season"] == s and e["track"] == tr and e.get("graded"))}
               for tr in ("SH-W", "SH-M", "SH-X")} for s in seasons}
    out = {"seasons": list(seasons), "pooled": True, "rule": "D009_shadow_tracks_v1 §5 (pooled verdict)",
           "run_et": now_et().isoformat(timespec="seconds"),
           "label": "SHADOW - secondary; never a scored track" + ("" if final else "; INTERIM - no verdict"),
           "tests": res, "sensitivity": sens, "descriptive": desc, "by_season": per,
           "duplicates_dropped": dropped}
    print(f"POOLED {' + '.join(seasons)}" + ("" if final else " (interim)"))
    print_(res, desc)
    if dropped:
        print(f"{len(dropped)} duplicate event(s) dropped: {dropped}")
    if write:
        write_json(os.path.join(ROOT, "outcomes", "shadow", "reports",
                                f"pooled_{'+'.join(seasons)}_{now_et():%Y-%m-%d}.json"), out)
    return out


def commit(msg):
    from freeze import git, push_all
    paths = [p for p in ("shadow", os.path.join("outcomes", "shadow")) if os.path.isdir(os.path.join(ROOT, p))]
    if not paths:
        print("nothing to commit")
        return
    git("add", *paths)
    if not git("diff", "--cached", "--name-only"):
        print("nothing new to commit")
        return
    git("commit", "-q", "-m", msg + chr(10) * 2 + "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>")
    print(f"pushed: {push_all()}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["capture"]:
        p = capture(last_chance="--last-chance" in a)
        if p and "--commit" in a:
            commit(f"Shadow calendar capture {now_et():%Y-%m-%d %H:%M} ET (code, D009 §3.2)")
    elif a[:1] == ["grade"]:
        grade(a[1], do_fetch="--no-fetch" not in a)
        if "--commit" in a:
            commit(f"Shadow grade {a[1]} as of {now_et():%Y-%m-%d %H:%M} ET (code, D009)")
    elif a[:1] == ["commit-grade"]:
        commit(f"Shadow grade as of {now_et():%Y-%m-%d %H:%M} ET (code, D009)")
    elif a[:1] == ["report"]:
        report_(a[1], write="--write" in a, final="--final" in a)
    elif a[:1] == ["report-pooled"]:
        report_pooled([x for x in a[1:] if not x.startswith("--")], write="--write" in a, final="--final" in a)
    else:
        raise SystemExit(__doc__)
