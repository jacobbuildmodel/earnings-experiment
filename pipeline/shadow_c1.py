"""D015 C1 live shadow - code only, no AI (registry/D015_c1_live_v1.md).

D014 found one first-hour signal on TRAIN that failed VALIDATION: when the pre-market gap is bigger than the move
the options priced, the stock gives part of it back after the open (C1). This module tests it on fresh data, on
the market-wide SH-M events (D009 §3), graded after the fact from Alpaca history. No order is ever sent.

    python pipeline/shadow_c1.py capture [--wait] [--commit]   # on P: the implied move of each SH-M event entering today
    python pipeline/shadow_c1.py grade <season> [--no-fetch] [--commit]
    python pipeline/shadow_c1.py status <season>                 # BLIND: counts and coverage only, never a return
    python pipeline/shadow_c1.py look1 [--commit]                # D015 §6 look 1 (Season A), once, from 2026-12-07
    python pipeline/shadow_c1.py final <seasonA> <seasonB> [--commit]   # D015 §6 final look (pooled), once
    python pipeline/shadow_c1.py probe <R>                       # ops check before registration: coverage, writes nothing

P is the D001 entry session, the session before the reaction session R. The capture runs from 35 to 5 minutes
before P's close and is write-once (shadow/c1/im/<P>.json). Prices come from analysis/d014/fetch.py (v1) and
fetch_v3.py (the retail entry), imported unchanged. Outcomes go to outcomes/shadow/<season>/, which T2 never has
on disk. Until a look is taken, no C1 return statistic is printed or written (D015 §6, blinding).
"""
import concurrent.futures
import datetime
import glob
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ET, ROOT, Sec, now_et, write_json, write_once  # noqa: E402
from sessions import LAST_KNOWN, close_time, is_session, shift  # noqa: E402

D014 = os.path.join(ROOT, "analysis", "d014")
sys.path.insert(0, D014)

IM_DIR = os.path.join(ROOT, "shadow", "c1", "im")
RULE = "D015_c1_live_v1"
FLOOR = 0.01                  # D014 §4: |g| >= 1%
PRIMARY_H = "30"              # D015 §6: y_30, open auction -> 10:00 ET
HS = ("5", "10", "30", "60", "c")
LOOK1_P = 0.005               # D015 §6: Season A alone
FINAL_P = 0.045               # D015 §6: A + B pooled
LOOK1_FROM = datetime.date(2026, 12, 7)
MIN_N, MIN_DATES = 30, 10     # rule 7
CAPTURE_FROM, CAPTURE_TO = 35, 5    # minutes before P's close
WORKERS = 3
RETRY_SLEEP = 60
SIGNAL_CUT = datetime.time(9, 27)
MAX_WAIT_H = 4.75
SEC_PATIENCE = datetime.timedelta(days=10)   # D009's timing finality; an SEC lookup still failing then -> VOID
TIGHT_SPREAD = 0.10           # the S2 gate's max_rel_spread_each_leg (D003 v4), for a secondary only

# the code whose drift ends D015 v1 (rule 5). check.py verifies EVERY line of the list (shadow.py, sessions.py,
# common.py, s1_screen.py included); this guard stops capture and grade on the files below.
PINNED = ("pipeline/shadow_c1.py", "analysis/d014/fetch.py", "analysis/d014/fetch_v3.py", "analysis/d014/run_d014.py",
          "analysis/d014/run_d014_v2.py", "analysis/d014/run_d014_v3.py")
IMPL_LIST = os.path.join(ROOT, "registry", "D015_implementation_v1.sha256")


def registered_hashes(path):
    """{file: digest} from a hash list; a later line for the same file wins (a dated re-registration)."""
    want = {}
    for line in open(path, encoding="utf-8"):
        if line.strip() and not line.startswith("#"):
            dg, rel = line.split(maxsplit=1)
            want[rel.strip()] = dg
    return want


def drift():
    """Refuse to capture or grade on code that differs from its registered hash. Before the list exists, no check."""
    import hashlib
    if not os.path.exists(IMPL_LIST):
        return
    want = registered_hashes(IMPL_LIST)
    bad = []
    for rel in PINNED:
        data = open(os.path.join(ROOT, rel), "rb").read().replace(b"\r\n", b"\n")
        if want.get(rel) != hashlib.sha256(data).hexdigest():
            bad.append(rel)
    if bad:
        raise SystemExit(f"D015 v1 code changed without a new version (rule 5): {bad}")


# ---------------------------------------------------------------- the implied move (pure)

def is_monthly(e):
    """A standard monthly expiry: the third Friday, or the Thursday before it when that Friday is not a session."""
    d = datetime.date.fromisoformat(e)
    if d.weekday() == 4 and 15 <= d.day <= 21:
        return True
    nxt = d + datetime.timedelta(days=1)
    return d.weekday() == 3 and 15 <= nxt.day <= 21 and nxt <= LAST_KNOWN and not is_session(nxt)


def pick_expiry(expiries, R, monthly=False):
    """The first listed expiration strictly after R (D010 §3); with monthly=True, the first MONTHLY one, which is
    what D010's chains held for 82% of D014's implied moves (median 15 days after R)."""
    after = sorted(e for e in expiries if datetime.date.fromisoformat(e) > R and (not monthly or is_monthly(e)))
    return after[0] if after else None


def pick_strike(call_strikes, put_strikes, spot):
    """The strike listed for both calls and puts nearest to spot; a tie takes the lower strike (D015 §3)."""
    common = sorted(set(call_strikes) & set(put_strikes))
    if not common or spot is None:
        return None
    return min(common, key=lambda k: (abs(k - spot), k))


def implied_move(call, put, spot):
    """(call mid + put mid) / spot, or None unless both bids are > 0 and neither quote is crossed."""
    for leg in (call, put):
        b, a = leg.get("bid"), leg.get("ask")
        if b is None or a is None or not (b > 0) or a < b:
            return None
    if not spot or spot <= 0:
        return None
    return ((call["bid"] + call["ask"]) / 2 + (put["bid"] + put["ask"]) / 2) / spot


def capture_window(day):
    close = datetime.datetime.combine(day, close_time(day), ET)
    return close - datetime.timedelta(minutes=CAPTURE_FROM), close - datetime.timedelta(minutes=CAPTURE_TO)


# ---------------------------------------------------------------- the capture (on P)

def num(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def seasons():
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "universe", "*", "raw", "yfinance_market.json"))):
        s = os.path.basename(os.path.dirname(os.path.dirname(p)))
        if s != "pilot":
            out.append(s)
    return out


def due_events(day):
    """Every SH-M event (D009 §3) whose entry session is `day`, so R is the next session."""
    import shadow
    out = []
    for season in seasons():
        try:
            universe = shadow.sh_m_universe(season)
            evs, _ = shadow.sh_m_events(season, universe)
        except (SystemExit, KeyError, ValueError) as exc:
            print(f"{season}: no SH-M events ({type(exc).__name__}: {exc})")
            continue
        for e in evs:
            if e["timing"]["entry"]["session"] == day.isoformat():
                out.append({"season": season, "ticker": e["ticker"], "date": e["date"], "session": e["session"],
                            "R": e["timing"]["exit_A"]["session"]})
    return out


def read_contract(tk, expiry, spot, R):
    """The straddle at the strike nearest to spot for one expiry: {expiry, days_after_R, strike, call, put, im, status}."""
    ch = tk.option_chain(expiry)
    k = pick_strike(list(ch.calls.strike), list(ch.puts.strike), spot)
    rec = {"expiry": expiry, "days_after_R": (datetime.date.fromisoformat(expiry) - R).days, "strike": k}
    if k is None:
        return dict(rec, im=None, status="no_strike")
    keys = ("bid", "ask", "lastPrice", "lastTradeDate", "impliedVolatility", "openInterest", "volume")
    c = ch.calls[ch.calls.strike == k].iloc[0]
    p = ch.puts[ch.puts.strike == k].iloc[0]
    call = {x: (str(c[x]) if x == "lastTradeDate" else num(c[x])) for x in keys}
    put = {x: (str(p[x]) if x == "lastTradeDate" else num(p[x])) for x in keys}
    im = implied_move(call, put, spot)
    return dict(rec, call=call, put=put, im=im, status="ok" if im is not None else "no_quote")


def fetch_im(ticker, R):
    """One yfinance read for an event reacting on R. The primary contract is the first MONTHLY expiry strictly after
    R; `nearest` is the first listed expiry strictly after R (a secondary). Never raises."""
    rec = {"fetched_et": now_et().isoformat(timespec="seconds")}
    try:
        import yfinance as yf
        tk = yf.Ticker(ticker)
        spot = num(tk.fast_info["last_price"])
        rec["spot"] = spot
        exps = list(tk.options or [])
        if not exps:
            return dict(rec, status="no_options")
        m, n = pick_expiry(exps, R, monthly=True), pick_expiry(exps, R)
        if m is None:
            rec.update(status="no_expiry", expiries=exps[:8])
        else:
            rec.update(read_contract(tk, m, spot, R))
        if n is not None:
            try:
                rec["nearest"] = ({k: rec.get(k) for k in ("expiry", "days_after_R", "strike", "call", "put", "im", "status")}
                                  if n == m else read_contract(tk, n, spot, R))
            except Exception as exc:
                rec["nearest"] = {"expiry": n, "im": None, "status": f"fetch_error {type(exc).__name__}"}
        return rec
    except Exception as exc:  # recorded as missing, never filled (CLAUDE.md)
        return dict(rec, status=f"fetch_error {type(exc).__name__}: {str(exc)[:120]}")


def capture(wait=False, do_commit=False):
    now = now_et()
    today = now.date()
    if not is_session(today):
        print(f"{today} is not a session - no capture")
        return None
    path = os.path.join(IM_DIR, f"{today.isoformat()}.json")
    if os.path.exists(path):
        print(f"{path} exists - the first capture of the day is the one in force")
        return None
    start, stop = capture_window(today)
    if now >= stop:
        print(f"::warning::{now:%H:%M} ET is past the capture window ({stop:%H:%M}) - no capture today; "
              f"its events grade as no_capture")
        return None
    due = due_events(today)
    meta = {"rule": f"{RULE} §3", "session_P": today.isoformat(), "window_et": [start.isoformat(), stop.isoformat()],
            "source": "yfinance Ticker.options / option_chain / fast_info (quotes about 15 minutes delayed)"}
    if not due:
        write_once(path, dict(meta, captured_et=now.isoformat(timespec="seconds"), events=[]))
        print("no SH-M event enters today - empty capture written")
        if do_commit:
            commit(f"C1 implied-move capture {today}: no events (code, D015)", [path])
        return path
    if now < start:
        if not wait:
            print(f"window opens {start:%H:%M} ET - run with --wait")
            return None
        if (start - now).total_seconds() > MAX_WAIT_H * 3600:
            print(f"window opens {start:%H:%M} ET, more than {MAX_WAIT_H} h away - a later trigger captures")
            return None
        print(f"{len(due)} event(s) due; waiting until {start:%H:%M} ET", flush=True)
        time.sleep(max(0.0, (start - now_et()).total_seconds()))
    results, passes = {}, 0
    todo = list(range(len(due)))
    while todo and now_et() < stop:
        passes += 1
        with concurrent.futures.ThreadPoolExecutor(WORKERS) as ex:
            got = list(ex.map(lambda i: (i, fetch_im(due[i]["ticker"], datetime.date.fromisoformat(due[i]["R"]))), todo))
        for i, rec in got:
            rec["attempt"] = passes
            results[i] = rec
        todo = [i for i in todo if results[i]["status"] not in ("ok", "no_expiry")]
        print(f"pass {passes}: {len(due) - len(todo)}/{len(due)} settled, {len(todo)} to retry", flush=True)
        if todo and now_et() + datetime.timedelta(seconds=RETRY_SLEEP) < stop:
            time.sleep(RETRY_SLEEP)
        else:
            break
    events = [dict(due[i], **results.get(i, {"status": "not_reached"})) for i in range(len(due))]
    out = dict(meta, captured_et=now.isoformat(timespec="seconds"), finished_et=now_et().isoformat(timespec="seconds"),
               passes=passes, events=events)
    write_once(path, out)
    ok = sum(1 for e in events if e["status"] == "ok")
    print(f"captured {ok}/{len(events)} implied moves in {passes} pass(es)")
    if do_commit:
        commit(f"C1 implied-move capture {today}: {ok}/{len(events)} (code, D015)", [path])
    return path


# ---------------------------------------------------------------- grading (after R)

def commit(msg, paths):
    """Commit and push to every remote. A failed push exits 2: the runner is ephemeral, so the file would be lost."""
    from freeze import git, push_all
    git("add", "--", *paths)
    if git("diff", "--cached", "--name-only"):
        git("commit", "-q", "-m", msg)
        res = push_all()
        print("pushed:", res)
        if not all(res.values()):
            raise SystemExit(2)


def committed_at(path):
    import shadow
    return shadow.committed_at(path)


def registered_at():
    """The D015 freeze: the later of the spec's and the implementation list's first commits."""
    ts = [committed_at(os.path.join(ROOT, "registry", f)) for f in ("D015_c1_live_v1.md", "D015_implementation_v1.sha256")]
    return None if any(t is None for t in ts) else max(ts)


def session_list(R):
    """R and the 21 sessions before it, oldest first (fetch.build_date indexes sessions[i - 20])."""
    xs = [shift(R, -k) for k in range(21, 0, -1)] + [R]
    return xs + [shift(R, 1)]


def captures():
    out = {}
    for p in sorted(glob.glob(os.path.join(IM_DIR, "*.json"))):
        c = json.load(open(p, encoding="utf-8"))
        when = committed_at(p)
        for e in c.get("events", []):
            out[(e["ticker"], e["date"], e["session"])] = dict(e, capture=os.path.relpath(p, ROOT).replace(os.sep, "/"),
                                                               capture_committed=when.isoformat() if when else None)
    return out


def accepted_for(hits, session):
    xs = sorted(h["accepted_et"] for h in hits if h.get("window") == session)
    return xs[0] if xs else None


def price_path(season, R):
    return os.path.join(ROOT, "outcomes", "shadow", season, "c1", f"prices_{R}.json")


def unresolved(status):
    return status.startswith(("sec_error", "pending"))


def fetch_prices(season, R, evs, tstore):
    """Write-once per reaction session: D014 v1 prices and the v3 retail entry for every event reacting on R. Each
    row keeps the SEC timing status it was priced under (an unresolved one had no acceptance floor)."""
    import fetch
    import fetch_v3
    path = price_path(season, R)
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    day = datetime.date.fromisoformat(R)
    ins, st_at = [], {}
    for e in evs:
        key = f"{e['ticker']}_{e['date']}_{e['session']}"
        acc = accepted_for(tstore.get(key, {}).get("hits", []), e["session"])
        st_at[e["ticker"]] = tstore.get(key, {}).get("status", "pending")
        ins.append({"ticker": e["ticker"], "date": e["date"], "session": e["session"], "cluster": e.get("industry"),
                    "accepted_et": acc, "factors": {"market_cap_pit": e.get("marketCap")}})
    fetch.stats.update(requests=0, retries=0, failed=0)
    try:
        rows = fetch.build_date(day, ins, session_list(day), {})
        ok = [r for r in rows if not r.get("void")]
        v3 = {r["ticker"]: r for r in fetch_v3.build_date(day, ok)} if ok else {}
    except fetch.FetchFailed as exc:
        print(f"{season} R {R}: prices NOT written, a request failed ({exc}); the next run retries")
        return None
    for r in rows:
        r.update({k: v3.get(r["ticker"], {}).get(k) for k in ("entry_t", "vw", "first_bid", "first_ask", "hs_first", "status")})
        r["sec_status_at_fetch"] = st_at.get(r["ticker"])
    out = {"rule": f"{RULE} §4", "R": R, "fetched_et": now_et().isoformat(timespec="seconds"),
           "source": "Alpaca market data v2, free plan, feed sip, adjustment raw (analysis/d014/fetch.py, fetch_v3.py)",
           "requests": dict(fetch.stats), "rows": rows}
    write_once(path, out)
    return out


def settled(R):
    """Alpaca's free plan withholds the latest 15 minutes: grade from 17:00 ET on R."""
    return now_et() >= datetime.datetime.combine(datetime.date.fromisoformat(R), datetime.time(17, 0), ET)


def contract_ok(cap, R):
    """The capture belongs to this event: same R, and its primary expiry is strictly after R."""
    return cap.get("R") == R and (cap.get("expiry") is None or cap["expiry"] > R)


def rel_spread_max(c):
    return max((l["ask"] - l["bid"]) / ((l["ask"] + l["bid"]) / 2) for l in (c["call"], c["put"]))


def event_row(ev, cap, reg, tstat, prow, today=None):
    """One graded C1 row: voids in a fixed order, then g, s, the C1 flag and the returns (D015 §5)."""
    import run_d014 as rd
    today = today or now_et().date()
    tm = ev["timing"]
    R = tm["exit_A"]["session"]
    out = {"ticker": ev["ticker"], "date": ev["date"], "session": ev["session"], "R": R,
           "P": tm["entry"]["session"], "industry": ev.get("industry"), "marketCap": ev.get("marketCap"),
           "timing_check": tstat, "void": None, "im": None, "im_status": None, "im_nearest": None, "c1": None}
    r_open = datetime.datetime.combine(datetime.date.fromisoformat(R), datetime.time(9, 30), ET)
    cut = datetime.datetime.combine(datetime.date.fromisoformat(R), SIGNAL_CUT, ET)
    patience_over = today > datetime.date.fromisoformat(ev["date"]) + SEC_PATIENCE
    if reg is None or reg >= r_open:
        out["void"] = "before_registration"
    elif not ev["exists_before_entry"]:
        out["void"] = "not_committed_before_entry"
    elif tstat in ("contradicted", "early"):
        out["void"] = f"print_{tstat}"
    elif tstat in ("foreign", "no_cik"):
        out["void"] = f"not_domestic_{tstat}"
    elif unresolved(tstat) and patience_over:
        out["void"] = "sec_unresolved"
    if cap is None:
        out["im_status"] = "no_capture"
    else:
        cw = cap.get("capture_committed")
        cwt = datetime.datetime.fromisoformat(cw) if cw else None
        if cwt is None or cwt >= cut:
            out["im_status"] = "im_late"
        elif reg is not None and cwt <= reg:
            out["im_status"] = "pre_registration"
        elif not contract_ok(cap, R):
            out["im_status"] = "mismatch"
        else:
            out["im_status"] = cap["status"]
            out["im"] = cap.get("im") if cap["status"] == "ok" else None
            out["im_days_after_R"] = cap.get("days_after_R")
            if out["im"] is not None:
                out["im_rel_spread_max"] = rel_spread_max(cap)
            nr = cap.get("nearest") or {}
            if nr.get("status") == "ok" and nr.get("expiry", "") > R:
                out["im_nearest"] = nr.get("im")
                out["im_nearest_days_after_R"] = nr.get("days_after_R")
    if out["void"] or prow is None:
        out["graded"] = False
        return out
    if prow.get("void"):
        out["void"] = prow["void"]
        out["graded"] = False
        return out
    if unresolved(prow.get("sec_status_at_fetch") or "pending"):
        out["void"] = "sec_unresolved"          # priced with no acceptance floor; decided without any outcome
        out["graded"] = False
        return out
    c0, o, pm = rd.num(prow["c0"]), rd.num(prow["o"]), rd.num(prow["pm"])
    g = pm / c0 - 1
    s = rd.sign(g)
    out.update({"g": g, "s": s, "c0": c0, "o": o, "pm": pm, "pm_t": prow.get("pm_t"), "o_t": prow.get("o_t"),
                "accepted_et": prow.get("accepted_et"), "split_check": prow.get("split_check")})
    out["below_floor"] = abs(g) < FLOOR
    p = {h: rd.num(prow.get(f"p{h}")) for h in ("5", "10", "30", "60")}
    p["c"] = rd.num(prow.get("pc"))
    e = {"g": g, "s": s, "o": o, "p": p, "R": R,
         "hs": {k: rd.num(prow.get(f"hs{k}")) for k in ("0935", "0940", "1000", "1030")},
         "mid": {k: rd.num(prow.get(f"mid{k}")) for k in ("0935", "0940", "1000", "1030")},
         "vw": rd.num(prow.get("vw")), "hs_first": rd.num(prow.get("hs_first")),
         "first_bid": rd.num(prow.get("first_bid")), "first_ask": rd.num(prow.get("first_ask"))}
    y = {h: (s * rd.ret(p[h], o) if p[h] is not None and s else None) for h in HS}
    y["d"] = s * rd.ret(p["30"], p["5"]) if p["30"] is not None and p["5"] and s else None
    so = rd.num(prow.get("spy_o"))
    sp = {h: rd.num(prow.get(f"spy_p{h}")) for h in ("5", "10", "30", "60")}
    sp["c"] = rd.num(prow.get("spy_pc"))
    spy_r = {h: rd.ret(sp[h], so) if sp[h] is not None and so else None for h in HS}
    out["y"] = y
    out["y_adj"] = {h: (y[h] - s * spy_r[h] if y[h] is not None and spy_r[h] is not None else None) for h in HS}
    out["c1"] = bool(out["im"] is not None and not out["below_floor"] and abs(g) > out["im"])
    out["c1_nearest"] = bool(out["im_nearest"] is not None and not out["below_floor"] and abs(g) > out["im_nearest"])
    if s:
        import run_d014_v3 as r3
        out["net_auction"] = {h: rd.net(e, h, -1) for h in ("30", "c")}
        out["net_retail"] = {h: r3.retail_net(e, h, -1, "primary", 0.0002) for h in ("30", "c")}
    out["graded"] = True
    return out


def grade(season, do_fetch=True):
    import shadow
    universe = shadow.sh_m_universe(season)
    evs, mstat = shadow.sh_m_events(season, universe)
    caps = captures()
    reg = registered_at()
    sec = Sec(os.path.join(ROOT, "cache", "sec"))
    subs = {}
    tpath = os.path.join(ROOT, "outcomes", "shadow", season, "c1_timing.json")
    tstore = json.load(open(tpath, encoding="utf-8")) if os.path.exists(tpath) else {}
    by_r = {}
    for ev in evs:
        by_r.setdefault(ev["timing"]["exit_A"]["session"], []).append(ev)
    rows, failed = [], []
    today = now_et().date()
    for R in sorted(by_r):
        group = by_r[R]
        r_open = datetime.datetime.combine(datetime.date.fromisoformat(R), datetime.time(9, 30), ET)
        live = reg is not None and reg < r_open
        if do_fetch and live and settled(R):
            for ev in group:
                key = f"{ev['ticker']}_{ev['date']}_{ev['session']}"
                if key in tstore and tstore[key].get("final"):
                    continue
                try:
                    st, hits = shadow.sec_timing(sec, ev["ticker"], ev["date"], ev["session"], subs)
                except Exception as exc:  # a network failure is retried on the next run, never fatal
                    st, hits = f"sec_error {type(exc).__name__}", []
                final = today > datetime.date.fromisoformat(ev["date"]) + SEC_PATIENCE   # unresolved then -> VOID
                tstore[key] = {"status": st, "hits": hits, "checked_et": now_et().isoformat(timespec="seconds"), "final": final}
        prices = None
        if live and settled(R):
            waiting = [e for e in group if unresolved(tstore.get(f"{e['ticker']}_{e['date']}_{e['session']}", {}).get("status", "pending"))
                       and today <= datetime.date.fromisoformat(e["date"]) + SEC_PATIENCE]
            if os.path.exists(price_path(season, R)):
                prices = json.load(open(price_path(season, R), encoding="utf-8"))
            elif do_fetch and waiting:
                print(f"{season} R {R}: SEC timing unresolved for {[e['ticker'] for e in waiting]} - prices wait "
                      f"(the acceptance floor needs it; after {SEC_PATIENCE.days} days those events are VOID sec_unresolved)")
                failed.append(R)
            elif do_fetch:
                prices = fetch_prices(season, R, group, tstore)
                if prices is None:
                    failed.append(R)
        prow = {r["ticker"]: r for r in (prices or {}).get("rows", [])}
        for ev in group:
            key = f"{ev['ticker']}_{ev['date']}_{ev['session']}"
            cap = caps.get((ev["ticker"], ev["date"], ev["session"]))
            tstat = tstore.get(key, {}).get("status", "pending")
            try:
                rows.append(event_row(ev, cap, reg, tstat, prow.get(ev["ticker"]) if prices else None, today))
            except Exception as exc:  # one bad event never stops the season
                print(f"C1 {ev['ticker']} {ev['date']}: grading failed: {type(exc).__name__}: {exc}")
                rows.append({"ticker": ev["ticker"], "date": ev["date"], "R": R, "graded": False,
                             "error": f"{type(exc).__name__}: {exc}"})
    write_json(tpath, tstore)
    out = {"season": season, "rule": RULE, "graded_by": "pipeline/shadow_c1.py", "graded_et": now_et().isoformat(timespec="seconds"),
           "registered_et": reg.isoformat() if reg else None, "sh_m_stats": mstat, "price_fetch_failed": failed, "events": rows}
    write_json(os.path.join(ROOT, "outcomes", "shadow", season, "c1.json"), out)
    print(status_text(season, rows, failed))
    return out


def probe(R):
    """Ops check that writes nothing: price the SH-M events reacting on R, a session BEFORE the registration, and
    print coverage only (voids, sources, times; never a return)."""
    import fetch
    import fetch_v3
    import shadow
    day = datetime.date.fromisoformat(R)
    reg = registered_at()
    if reg is not None and reg < datetime.datetime.combine(day, datetime.time(9, 30), ET):
        raise SystemExit(f"{R} is on or after the registration - probe only sessions before it")
    sec, subs, ins = Sec(os.path.join(ROOT, "cache", "sec")), {}, []
    for season in seasons():
        universe = shadow.sh_m_universe(season)
        evs, _ = shadow.sh_m_events(season, universe)
        for e in evs:
            if e["timing"]["exit_A"]["session"] == R:
                try:
                    st, hits = shadow.sec_timing(sec, e["ticker"], e["date"], e["session"], subs)
                except Exception as exc:
                    st, hits = f"sec_error {type(exc).__name__}", []
                ins.append({"ticker": e["ticker"], "date": e["date"], "session": e["session"], "cluster": e.get("industry"),
                            "accepted_et": accepted_for(hits, e["session"]), "factors": {"market_cap_pit": e.get("marketCap")},
                            "timing_check": st})
    print(f"{R}: {len(ins)} SH-M event(s)")
    rows = fetch.build_date(day, ins, session_list(day), {})
    ok = [r for r in rows if not r.get("void")]
    v3 = {r["ticker"]: r for r in fetch_v3.build_date(day, ok)} if ok else {}
    tc = {i["ticker"]: i["timing_check"] for i in ins}
    for r in rows:
        q = sum(1 for k in ("0935", "0940", "1000", "1030") if r.get(f"hs{k}") is not None)
        print(f"  {r['ticker']:6} {r['session']} timing={tc[r['ticker']]:12} void={r.get('void') or '-':13} "
              f"c0={r.get('c0_src')} o={r.get('o_src')} o_t={r.get('o_t')} pm_t={r.get('pm_t')} acc={r.get('accepted_et')} "
              f"split={r.get('split_check')} quotes={q}/4 retail={v3.get(r['ticker'], {}).get('status')}")
    print("requests:", fetch.stats)


# ---------------------------------------------------------------- statistics (D015 §6-§7)

def _betacf(a, b, x):
    """Continued fraction for the incomplete beta (Lentz)."""
    tiny, qab, qap, qam = 1e-300, a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c if abs(1.0 + aa / c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c if abs(1.0 + aa / c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-14:
            break
    return h


def betainc(a, b, x):
    """The regularized incomplete beta I_x(a, b)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lb = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x)
    if x < (a + 1) / (a + b + 2):
        return math.exp(lb) * _betacf(a, b, x) / a
    return 1.0 - math.exp(lb) * _betacf(b, a, 1 - x) / b


def t_cdf(t, df):
    """P(T <= t) for Student's t with df degrees of freedom."""
    tail = 0.5 * betainc(df / 2.0, 0.5, df / (df + t * t))
    return tail if t < 0 else 1.0 - tail


def cr1_test(rows, key=("y", PRIMARY_H)):
    """Mean, CR1 SE by R, t, and the one-sided lower-tail p from Student's t with G - 1 df (G = R dates)."""
    import run_d014 as rd
    xs = [(r[key[0]][key[1]], r["R"]) for r in rows if r.get(key[0]) and r[key[0]].get(key[1]) is not None]
    n, dates = len(xs), len({d for _, d in xs})
    out = {"n": n, "dates": dates}
    if n < MIN_N or dates < MIN_DATES:
        out["status"] = "insufficient"
        return out
    m, se = rd.cr1([y for y, _ in xs], [d for _, d in xs])
    t = m / se if se else None
    out.update(mean=m, se=se, t=t, df=dates - 1, p_one_sided=(t_cdf(t, dates - 1) if t is not None else 1.0))
    return out


def verdict(test, look):
    """D015 §6. look 'season_A' (look 1), 'final' (A + B pooled); anything else is interim and carries no verdict."""
    if look not in ("season_A", "final"):
        return "interim - no verdict"
    if test.get("status") == "insufficient":
        return "insufficient"
    bar = LOOK1_P if look == "season_A" else FINAL_P
    if test["p_one_sided"] < bar:
        return "CONFIRMED"
    return "not yet - continue to the pooled look" if look == "season_A" else "NOT CONFIRMED"


def c1_rows(rows):
    return [r for r in rows if r.get("graded") and r.get("c1")]


def counts(rows):
    """Blind: no return of any kind."""
    g = [r for r in rows if r.get("graded") and not r.get("below_floor")]
    c1 = c1_rows(rows)
    voids, ims = {}, {}
    for r in rows:
        if r.get("void"):
            voids[r["void"]] = voids.get(r["void"], 0) + 1
        if r.get("graded"):
            ims[r.get("im_status")] = ims.get(r.get("im_status"), 0) + 1
    ratios = sorted(abs(r["g"]) / r["im"] for r in g if r.get("im"))
    q = (lambda xs, f: round(xs[int(f * (len(xs) - 1))], 3) if xs else None)
    return {"events": len(rows), "graded": sum(1 for r in rows if r.get("graded")), "gap_ge_1pct": len(g),
            "with_im": sum(1 for r in g if r.get("im") is not None), "c1": len(c1),
            "c1_dates": len({r["R"] for r in c1}),
            "c1_missing_y30": sum(1 for r in c1 if (r.get("y") or {}).get("30") is None),
            "c1_nearest": sum(1 for r in g if r.get("c1_nearest")),
            "voids": voids, "im_status_of_graded": ims,
            "abs_gap_over_im": {str(f): q(ratios, f) for f in (0.25, 0.5, 0.75, 0.9)}}


def stats_(rows):
    import run_d014 as rd
    g = [r for r in rows if r.get("graded") and not r.get("below_floor")]
    c1 = c1_rows(rows)
    sec = {f"y|{h}": cr1_test(c1, ("y", h)) for h in HS + ("d",)}
    sec.update({f"y_adj|{h}": cr1_test(c1, ("y_adj", h)) for h in HS})
    sec.update({f"net_auction_fade|{h}": cr1_test(c1, ("net_auction", h)) for h in ("30", "c")})
    sec.update({f"net_retail_fade|{h}": cr1_test(c1, ("net_retail", h)) for h in ("30", "c")})
    sec["c1_timing_verified|30"] = cr1_test([r for r in c1 if r.get("timing_check") == "verified"])
    sec["c1_tight_im|30"] = cr1_test([r for r in c1 if r.get("im_rel_spread_max") is not None
                                      and r["im_rel_spread_max"] <= TIGHT_SPREAD])
    sec["c1_mid_cap|30"] = cr1_test([r for r in c1 if (r.get("marketCap") or 0) < 10e9])
    sec["c1_nearest_expiry_im|30"] = cr1_test([r for r in g if r.get("c1_nearest")])
    sec["complement|30"] = cr1_test([r for r in g if r.get("im") is not None and not r.get("c1")])
    sec["all_gaps|30"] = cr1_test(g)
    return {"primary": cr1_test(c1), "secondary": sec, "counts": counts(rows), "fee": rd.FEE}


def load(season):
    p = os.path.join(ROOT, "outcomes", "shadow", season, "c1.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"events": [], "price_fetch_failed": []}


def status_text(season, rows, failed):
    return f"D015 C1 {season} (BLIND - counts only): {json.dumps(counts(rows))} - R dates waiting {failed}"


def fmt(t):
    if t.get("status") == "insufficient":
        return f"insufficient (n {t['n']}, dates {t['dates']})"
    return (f"{t['mean']:+.3%} (t {t['t']:+.2f}, df {t['df']}, p1 {t['p_one_sided']:.4f}, n {t['n']}, "
            f"dates {t['dates']})")


def render(title, res, look):
    L = [f"# {title}", "", f"Rule `registry/{RULE}.md`. SHADOW: graded after the fact from Alpaca history; no order.", "",
         f"**H-C1 (primary, y_30 in the C1 group, one-sided, CR1 by R, Student t with G - 1 df):** {fmt(res['primary'])}",
         "", f"**Verdict ({look}):** {verdict(res['primary'], look)}", "",
         "## Secondary (descriptive, decide nothing; a p here is lower-tail and means nothing for a fade's net)", "",
         "| statistic | value |", "|---|---|"]
    L += [f"| {k} | {fmt(v)} |" for k, v in res["secondary"].items()]
    L += ["", "## Counts", "", "```", json.dumps(res["counts"], indent=1), "```", ""]
    return "\n".join(L)


def all_final(season):
    """Every SEC timing check of the season is final and no reaction date is still waiting for prices."""
    tp = os.path.join(ROOT, "outcomes", "shadow", season, "c1_timing.json")
    ts = json.load(open(tp, encoding="utf-8")) if os.path.exists(tp) else {}
    data = load(season)
    rows = data["events"]
    pending = [r for r in rows if not r.get("graded") and not r.get("void") and not r.get("error")]
    return bool(ts) and all(v.get("final") for v in ts.values()) and not data.get("price_fetch_failed") and not pending


def take_look(name, rows, look, title, ready, today=None):
    """Write a look once. Refuses when not ready or when the look already exists (no second look)."""
    base = os.path.join(ROOT, "outcomes", "shadow", "c1_looks")
    jp, mp = os.path.join(base, f"{name}.json"), os.path.join(base, f"{name}.md")
    if os.path.exists(jp):
        raise SystemExit(f"{jp} exists - a look is taken once (D015 §6)")
    if not ready:
        raise SystemExit(f"{name}: not ready - every timing check must be final and every reaction date priced")
    res = stats_(rows)
    res["verdict"] = verdict(res["primary"], look)
    res["taken_et"] = now_et().isoformat(timespec="seconds")
    text = render(title, res, look)
    write_once(jp, {"rule": RULE, "look": look, **res})
    with open(mp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")
    print(text)
    return [jp, mp]


def look1(today=None):
    today = today or now_et().date()
    if today < LOOK1_FROM:
        raise SystemExit(f"look 1 is taken on or after {LOOK1_FROM} (D015 §6); until then the shadow is blind")
    return take_look("look1_seasonA", load("seasonA")["events"], "season_A", "D015 C1 live - look 1 (Season A)",
                     all_final("seasonA"))


def final(sa, sb):
    return take_look(f"final_{sa}_{sb}", load(sa)["events"] + load(sb)["events"], "final",
                     f"D015 C1 live - final look ({sa} + {sb} pooled)", all_final(sa) and all_final(sb))


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    if a[0] in ("capture", "grade", "look1", "final"):
        drift()
    if a[0] == "capture":
        capture(wait="--wait" in a, do_commit="--commit" in a)
    elif a[0] == "grade":
        grade(a[1], do_fetch="--no-fetch" not in a)
        if "--commit" in a:
            base = os.path.join(ROOT, "outcomes", "shadow", a[1])
            commit(f"C1 shadow grade {a[1]} {now_et():%Y-%m-%d %H:%M} ET (code, D015)",
                   [p for p in (os.path.join(base, "c1.json"), os.path.join(base, "c1_timing.json"), os.path.join(base, "c1"))
                    if os.path.exists(p)])
    elif a[0] == "status":
        d = load(a[1])
        print(status_text(a[1], d["events"], d.get("price_fetch_failed")))
    elif a[0] == "look1":
        paths = look1()
        if "--commit" in a:
            commit("D015 look 1 (Season A) taken (code)", paths)
    elif a[0] == "final":
        paths = final(a[1], a[2])
        if "--commit" in a:
            commit(f"D015 final look ({a[1]} + {a[2]}) taken (code)", paths)
    elif a[0] == "probe":
        probe(a[1])
    else:
        raise SystemExit(__doc__)
