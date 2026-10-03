"""D009 v2 (DRAFT) - the year-round market-wide shadow: SH-MO, market-wide prints on OFF-SEASON sessions.
Code only, no AI. It refuses to run until registry/D009_shadow_tracks_v2.json is frozen (the draft lives in
reviews/proposals/D009_v2_yearround_DRAFT.md / .json). It never changes a v1 track: v1's SH-M, its family
(H-M, H-X, H-VOL; Holm m = 3) and its files are untouched.

    python pipeline/shadow_offseason.py windows                      # the registered off-season windows
    python pipeline/shadow_offseason.py screen <window>              # the window's fixed-date universe capture
    python pipeline/shadow_offseason.py grade <window> [--no-fetch]  # SH-MO events, prices once, recompute
    python pipeline/shadow_offseason.py report <window> [--with seasonA seasonB] [--write] [--final]

Universe (rule 8): one screen per off-season window on its registered screen date - Nasdaq's stock screener
(every NYSE / Nasdaq / NYSE American listing with its market cap) united with the Nasdaq calendar for every
weekday of the window; Yahoo market data for each name Nasdaq sizes at >= $1.5B (or does not size); then
v1's S1 filters verbatim (EQUITY, US exchange, USD, >= $2B at capture, no excluded ticker, not a shell).
Dating: v1's daily calendar captures (shadow/calendar/), an event being (name, D, session) as listed in the
capture taken on its snapshot session - exactly SH-M's rule (D009 §3.2), only the window differs.
Grading: shadow.grade_one, unchanged (the events are graded as SH-M and then labelled SH-MO).
"""
import datetime
import json
import os
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shadow  # noqa: E402
from common import REGISTRY, ROOT, WEB_HEADERS, Sec, now_et, registry, rule_for, write_json, write_once  # noqa: E402
from sessions import is_session, shift, timing  # noqa: E402

RULE_FILE = "D009_shadow_tracks_v2.json"
TRACK = "SH-MO"
SCREENER = "https://api.nasdaq.com/api/screener/stocks"
KEEP = ["quoteType", "exchange", "marketCap", "industry", "sector", "longName", "shortName", "currency"]


def load_rule():
    """The frozen v2 rule. registry() refuses an unfrozen or altered file, so nothing here runs on a draft."""
    if not os.path.exists(os.path.join(REGISTRY, RULE_FILE)):
        raise SystemExit(f"registry/{RULE_FILE} does not exist - D009 v2 is a DRAFT "
                         "(reviews/proposals/D009_v2_yearround_DRAFT.md) and nothing runs until it is frozen")
    return registry(RULE_FILE)


def screen_dir(wid):
    return os.path.join(ROOT, "shadow", "offseason", wid)


def season_windows():
    """Every season window registered in any frozen D003 version: {season: (lo, hi)}."""
    out = {}
    for line in open(os.path.join(REGISTRY, "FROZEN.sha256"), encoding="utf-8"):
        if not line.strip():
            continue
        name = line.split(maxsplit=1)[1].strip().lstrip("*")
        if name.startswith("D003_universe_screen_v") and name.endswith(".json"):
            for s, v in (registry(name).get("seasons") or {}).items():
                out[s] = tuple(v["window"])
    return out


def window(rule, wid, seasons=None):
    """A registered off-season window. Refuses one that overlaps a registered season window: a print is
    either in-season (v1 SH-M) or off-season (SH-MO), never both."""
    w = rule["windows"].get(wid)
    if w is None:
        raise SystemExit(f"{wid!r} is not a registered off-season window ({sorted(rule['windows'])})")
    lo, hi = w["window"]
    for s, (a, b) in (season_windows() if seasons is None else seasons).items():
        if s.lower().startswith("pilot"):
            continue
        if not (hi < a or lo > b):
            raise SystemExit(f"off-season window {wid} {lo}..{hi} overlaps {s} {a}..{b} - fix the v2 rule")
    return {"id": wid, "lo": lo, "hi": hi, "screen_date": w["screen_date"], "after_season": w["after_season"]}


# ---------------------------------------------------------------- the fixed-date universe screen

def nasdaq_screener(attempts=4):
    """Every listed stock with Nasdaq's market cap. None on failure (recorded, never fabricated)."""
    err = None
    for attempt in range(attempts):
        try:
            r = requests.get(SCREENER, params={"tableonly": "true", "limit": "25000", "download": "true"},
                             headers=WEB_HEADERS, timeout=60)
            r.raise_for_status()
            rows = (r.json().get("data") or {}).get("rows") or []
            if rows:
                return [{"symbol": str(x.get("symbol", "")).strip().upper(), "marketCap": x.get("marketCap"),
                         "name": x.get("name"), "country": x.get("country"), "industry": x.get("industry")}
                        for x in rows if x.get("symbol")], None
            err = "empty"
        except (requests.RequestException, ValueError) as exc:
            err = f"{type(exc).__name__}: {exc}"
        time.sleep(5 * (attempt + 1))
    return None, err


def nasdaq_calendar(lo, hi):
    """The Nasdaq earnings calendar for every weekday of the window, as of the screen date."""
    days, x = {}, datetime.date.fromisoformat(lo)
    while x <= datetime.date.fromisoformat(hi):
        if x.weekday() < 5:
            rows, err = None, None
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
            days[x.isoformat()] = ({"symbols": sorted({it["symbol"].strip().upper() for it in rows}),
                                    "marketCap": {it["symbol"].strip().upper(): it.get("marketCap") for it in rows}}
                                   if rows is not None else {"error": err})
            time.sleep(1)
        x += datetime.timedelta(days=1)
    return days


def screen(wid):
    """Write-once shadow/offseason/<wid>/market.json. Runs on the window's screen date, or on a later
    session before the window's first event's entry open (an event whose entry precedes the commit of this
    file is VOID not_committed_before_entry, mechanically). A failed screener is recorded and the calendar
    union carries the screen; a failed Yahoo name is recorded as an error, never filled."""
    import yfinance as yf
    rule = load_rule()
    w = window(rule, wid)
    today = now_et().date()
    if today.isoformat() < w["screen_date"]:
        raise SystemExit(f"{wid}: the screen date is {w['screen_date']} - not before")
    path = os.path.join(screen_dir(wid), "market.json")
    if os.path.exists(path):
        raise SystemExit(f"{path} exists - one screen per window (rule 8)")
    import s1_screen
    s1_screen.RULE = rule_for("D003_universe_screen", w["after_season"])
    started = now_et()
    scr, scr_err = nasdaq_screener()
    cal = nasdaq_calendar(w["lo"], w["hi"])
    pre_min = rule["screen"]["pre_filter_market_cap_min"]
    names = {}
    for x in scr or []:
        names.setdefault(x["symbol"], {"sources": []})["sources"].append("screener")
        names[x["symbol"]]["nasdaq_cap"] = shadow.parse_cap(x["marketCap"])
    for day, v in cal.items():
        for t in v.get("symbols", []):
            names.setdefault(t, {"sources": []})
            if "calendar" not in names[t]["sources"]:
                names[t]["sources"].append("calendar")
            names[t].setdefault("nasdaq_cap", shadow.parse_cap(v["marketCap"].get(t)))
    todo = sorted(t for t, v in names.items() if not s1_screen.ticker_excluded(t)
                  and (v.get("nasdaq_cap") is None or v["nasdaq_cap"] >= pre_min))
    part = os.path.join(ROOT, "cache", f"offseason_{wid}_market_partial.json")
    tick = json.load(open(part, encoding="utf-8")) if os.path.exists(part) else {}
    print(f"{wid}: {len(names)} names, {len(todo)} sized >= ${pre_min / 1e9:.1f}B or unsized; "
          f"{len([t for t in todo if t not in tick or 'error' in tick[t]])} to fetch")
    for i, t in enumerate(todo):
        if t in tick and "error" not in tick[t]:
            continue
        for attempt in range(3):
            try:
                info = yf.Ticker(t).info or {}
                tick[t] = {k: info.get(k) for k in KEEP}
                break
            except Exception as exc:  # recorded, never fabricated
                tick[t] = {"error": f"{type(exc).__name__}: {exc}"}
                if "404" in str(exc) or "Not Found" in str(exc):
                    break
                time.sleep(60 if "Too Many Requests" in str(exc) or "429" in str(exc) else 5)
        if i % 100 == 99:
            print(f"  {i + 1}/{len(todo)}", flush=True)
            write_json(part, tick)
        time.sleep(0.3)
    out = {"window": w, "rule": "D009_shadow_tracks_v2 (SH-MO universe)", "captured_et": started.isoformat(timespec="seconds"),
           "finished_et": now_et().isoformat(timespec="seconds"),
           "sources": {"screener": SCREENER if scr is not None else None, "screener_error": scr_err,
                       "screener_rows": len(scr or []), "calendar_failed_days": [k for k, v in cal.items() if "error" in v]},
           "pre_filter_market_cap_min": pre_min, "names": names, "tickers": tick}
    write_once(path, out)
    errors = sum(1 for v in tick.values() if "error" in v)
    print(f"{wid}: market data for {len(tick)} names ({errors} errors) -> {os.path.relpath(path, ROOT)}")
    return path


def universe(wid, w):
    """v1's S1 filters (D009 §3.1, the D003 rule of the season the window follows), on this window's screen."""
    path = os.path.join(screen_dir(wid), "market.json")
    if not os.path.exists(path):
        return {}
    import s1_screen
    rule = rule_for("D003_universe_screen", w["after_season"])
    s1_screen.RULE = rule
    s1 = rule["s1"]
    when = shadow.committed_at(path)
    out = {}
    for t, m in shadow.load(path)["tickers"].items():
        if "error" in m or s1_screen.ticker_excluded(t):
            continue
        if m.get("quoteType") != s1["quote_type"] or shadow.EXCHANGES.get(m.get("exchange")) not in s1["exchanges"]:
            continue
        if (m.get("currency") or "USD") != "USD" or (m.get("industry") in s1["exclude_industries"]):
            continue
        if not m.get("marketCap") or m["marketCap"] < s1["market_cap_min"]:
            continue
        out[t] = {"industry": m.get("industry"), "sector": m.get("sector"), "marketCap": m["marketCap"],
                  "universe_committed": when.isoformat() if when else None}
    return out


# ---------------------------------------------------------------- events and grading

def events(w, univ, caps=None, sec=None, committed=None):
    """SH-MO: (name, D, session) as listed in the capture taken ON its snapshot session (BMO: D-2 sessions,
    AMC: D-1; the D003 S2 offsets of the season the window follows), D inside the off-season window.
    `caps`, `sec` and `committed` are injectable for tests."""
    snap_off = rule_for("D003_universe_screen", w["after_season"])["s2"]["snapshot_session"]
    caps = shadow.captures() if caps is None else caps
    committed = committed or shadow.committed_at
    out, no_session, seen = [], 0, set()
    for day, p in caps.items():
        c = shadow.load(p)
        for date, v in c["days"].items():
            if not (w["lo"] <= date <= w["hi"]) or not is_session(shadow.d(date)):
                continue
            for row in v.get("rows", []):
                t = row["symbol"]
                if t not in univ:
                    continue
                if row.get("session") not in ("BMO", "AMC"):
                    no_session += 1
                    continue
                snap = shift(shadow.d(date), snap_off[row["session"]]).isoformat()
                if snap != day or (t, date) in seen:
                    continue
                seen.add((t, date))
                try:
                    tm = timing(shadow.d(date), row["session"], shadow.D001)
                except ValueError:
                    continue
                when = committed(p)
                u_when = univ[t]["universe_committed"]
                when = max(when, datetime.datetime.fromisoformat(u_when)) if (when and u_when) else None
                out.append({"track": "SH-M", "window": w["id"], "ticker": t, "date": date, "session": row["session"],
                            "session_source": row.get("session_source"), "timing": tm, "snapshot": snap,
                            "capture": os.path.relpath(p, ROOT).replace(os.sep, "/"),
                            "capture_committed": when.isoformat() if when else None,
                            "exists_before_entry": bool(when and when < shadow.entry_open_dt(tm["entry"]["session"])),
                            **univ[t]})
    sec = sec or Sec(os.path.join(ROOT, "cache", "sec"))
    kept, seen = [], set()
    for ev in sorted(out, key=lambda e: (e["date"], e["ticker"])):   # one event per issuer (CIK) and date
        k = (sec.cik(ev["ticker"]) or ev["ticker"], ev["date"])
        if k in seen:
            continue
        seen.add(k)
        kept.append(ev)
    return kept, {"rows_without_session": no_session, "capture_days": sorted(caps)}


def grade(wid, do_fetch=True):
    rule = load_rule()
    w = window(rule, wid)
    univ = universe(wid, w)
    evs, stat = events(w, univ)
    prices = shadow.Prices(wid)
    if do_fetch:
        needs = {}
        for ev in evs:
            tm = ev["timing"]
            e_s, x_s = tm["entry"]["session"], tm["exit_A"]["session"]
            snap = shift(shadow.d(e_s), -1).isoformat()
            needs.setdefault(ev["ticker"], set()).update({(e_s, "open"), (x_s, "open"), (x_s, f"div:{e_s}"),
                                                          (x_s, f"split:{e_s}"), (snap, "vol60")})
            needs.setdefault("SPY", set()).update({(e_s, "open"), (x_s, "open")})
        shadow.fetch(prices, needs)
    sec = Sec(os.path.join(ROOT, "cache", "sec"))
    subs = {}
    tpath = os.path.join(ROOT, "outcomes", "shadow", wid, "timing.json")
    tstore = shadow.load(tpath) if os.path.exists(tpath) else {}
    rows = []
    for ev in evs:
        try:
            r = shadow.grade_one(ev, prices, sec, subs, tstore, do_fetch)  # graded exactly as SH-M (D009 §1)
        except Exception as exc:  # one bad event never stops the window
            print(f"{TRACK} {ev['ticker']} {ev['date']}: grading failed: {type(exc).__name__}: {exc}")
            r = {**ev, "void": None, "graded": False, "error": f"{type(exc).__name__}: {exc}"}
        r["track"] = TRACK
        rows.append(r)
    write_json(tpath, tstore)
    write_json(os.path.join(ROOT, "outcomes", "shadow", wid, "graded.json"),
               {"window": w, "rule": "D009_shadow_tracks_v2", "graded_by": "pipeline/shadow_offseason.py",
                "graded_et": now_et().isoformat(timespec="seconds"), "sh_mo_universe": len(univ),
                "sh_mo_stats": stat, "events": rows})
    print(f"{wid} {TRACK}: {len(rows)} events, {sum(r['graded'] for r in rows)} graded, "
          f"{sum(1 for r in rows if r['void'])} void")
    return rows


# ---------------------------------------------------------------- statistics (v2 §5)

def year_stats(off_rows, season_rows, clock_start, final=False):
    """H-MY (v2's one registered test, its own family, m = 1): mean net return of every market-wide event
    from v2's clock - v1's graded SH-M of the named seasons with entry on or after clock_start, plus the
    graded SH-MO - is > 0. Same cluster-robust t and restricted wild bootstrap as D009 §5, seed by name.
    Descriptive: H-MO (off-season alone) and the off-minus-in difference."""
    import report
    clean = lambda rs: [e for e in rs if not set(e.get("flags", [])) & {"timing_unverified", "late_8k"}]  # noqa: E731
    g = lambda rs: [e["timing"]["entry"]["session"] for e in rs]  # noqa: E731
    y = lambda rs: [e["exit_A"]["net_return"] for e in rs]  # noqa: E731
    mo = [e for e in off_rows if e.get("graded") and e["track"] == TRACK]
    m = [e for e in season_rows if e.get("graded") and e["track"] == "SH-M"
         and e["timing"]["entry"]["session"] >= clock_start]
    both = m + mo
    res = shadow.mean_test(y(both), g(both), "H-MY")
    res["mde"] = shadow.mde(res)
    p = res.get("p_one_sided")
    p = 1.0 if p is None or p != p else p
    n, dates = res.get("n", 0), res.get("dates", 0) or 0
    if not report.sufficient(n, dates):
        res["status"] = "insufficient"
    elif not final:
        res["status"] = "interim (monitoring only)"
    else:
        res["status"] = ("p < 0.05 (shadow, secondary; v2 family m = 1)" if p < 0.05 else
                         f"no evidence (shadow) - an effect smaller than {res['mde'] * 100:.2f} pts would usually be missed"
                         if res.get("mde") else "no evidence (shadow)")
    sens = {"H-MY without unverified/late timing": shadow.mean_test(y(clean(both)), g(clean(both)), "H-MY-clean")}
    desc = {"H-MO off-season alone (descriptive)": shadow.mean_test(y(mo), g(mo), "H-MO"),
            "off minus in-season (descriptive)": shadow.diff_test(y(both), [1.0 if e["track"] == TRACK else 0.0 for e in both],
                                                                    g(both), "MO-minus-M"),
            "events": {"SH-M in sample": len(m), "SH-MO graded": len(mo),
                       "SH-MO total": sum(1 for e in off_rows if e["track"] == TRACK),
                       "SH-MO void": {v: sum(1 for e in off_rows if e.get("void") == v)
                                      for v in sorted({e.get("void") for e in off_rows if e.get("void")})}}}
    return {"H-MY": res}, sens, desc


def report_(wids, seasons=(), write=False, final=False):
    rule = load_rule()
    clock = rule.get("clock_start_entry_session")
    if not clock:
        raise SystemExit("v2's clock_start_entry_session is not set - it is fixed when v2 is frozen")
    off_rows, season_rows = [], []
    for wid in wids:
        window(rule, wid)
        p = os.path.join(ROOT, "outcomes", "shadow", wid, "graded.json")
        off_rows += shadow.load(p)["events"] if os.path.exists(p) else []
    if any(s.lower().startswith("pilot") for s in seasons):
        raise SystemExit("D009 §6: pilot numbers are never pooled")
    for s in seasons:
        season_rows += shadow.load(os.path.join(ROOT, "outcomes", "shadow", s, "graded.json"))["events"]
    res, sens, desc = year_stats(off_rows, season_rows, clock, final)
    out = {"windows": list(wids), "seasons": list(seasons), "clock_start_entry_session": clock,
           "rule": "D009_shadow_tracks_v2", "run_et": now_et().isoformat(timespec="seconds"),
           "label": "SHADOW - secondary; never a scored track" + ("" if final else "; INTERIM - no verdict"),
           "tests": res, "sensitivity": sens, "descriptive": desc}
    shadow.print_(res, {})
    print(json.dumps(desc, default=str))
    if write:
        write_json(os.path.join(ROOT, "outcomes", "shadow", "reports",
                                f"year_{'+'.join(list(wids) + list(seasons))}_{now_et():%Y-%m-%d}.json"), out)
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["windows"]:
        r = load_rule()
        for wid in r["windows"]:
            print(window(r, wid))
    elif a[:1] == ["screen"]:
        screen(a[1])
        if "--commit" in a:
            shadow.commit(f"Shadow off-season screen {a[1]} {now_et():%Y-%m-%d %H:%M} ET (code, D009 v2)")
    elif a[:1] == ["grade"]:
        grade(a[1], do_fetch="--no-fetch" not in a)
        if "--commit" in a:
            shadow.commit(f"Shadow off-season grade {a[1]} as of {now_et():%Y-%m-%d %H:%M} ET (code, D009 v2)")
    elif a[:1] == ["report"]:
        seas = a[a.index("--with") + 1:] if "--with" in a else []
        seas = [s for s in seas if not s.startswith("--")]
        wl = [x for x in a[1:a.index("--with")] if not x.startswith("--")] if "--with" in a else [x for x in a[1:] if not x.startswith("--")]
        report_(wl, seas, write="--write" in a, final="--final" in a)
    else:
        raise SystemExit(__doc__)
