"""SH-RU (D009 v3): the 20-session run-up into the print. Code only, no AI; implements registry/
D009_shadow_tracks_v3.md §2-§3 exactly. (D009 v3 §6 names it "shadow.py runup"; it lives in this module so the
frozen SH-W/SH-M/SH-X code in shadow.py is not edited. Registered in D009_implementation_v3.sha256.)

    python pipeline/shadow_runup.py events SEASON                 # E, D_exp, voids - no network beyond git
    python pipeline/shadow_runup.py grade SEASON [--commit]       # fetch + grade every event whose window is due
    python pipeline/shadow_runup.py report SEASON... [--write] [--final]
    python pipeline/shadow_runup.py size-gate [--sims N]          # §3 size gate on synthetic data

Write-once outputs (fenced from T2): outcomes/shadow/<season>/runup_prices.jsonl, runup.jsonl.
Choices §2-§3 leave to the code, fixed here before any X:
- One event per issuer: candidates are deduplicated on CIK (ticker when no CIK), first listed wins.
- D_act from the company: every events/<season>/<T>_<date>/confirm.json, plus event_status.json's calendar_date
  for a non-PENDING status; the EARLIEST such date (a rescheduled print with a stale earlier folder keeps the
  earlier date - the spec's "earlier"). From the SEC: the ET calendar date of the first Item 2.02 8-K (form
  exactly "8-K", not 8-K/A) accepted on or after shift(E, 2); a print at E + 1 with no company date is
  therefore not seen (spec-faithful, disclosed). D_act = the earlier of the two.
- An event is graded once D_act is known (or shift(D_exp, 30) has passed) and it is at least 06:00 ET on
  shift(X, 1). Its prices are fetched then, once.
- Prices: an exception, or an empty stock or SPY series, is a FAILED fetch - nothing is stored, the event is
  retried on the next run. After failures on 10 distinct ET dates the event is VOID price_unavailable (reported
  by cluster; delisted / acquired names land here). Data that arrives but lacks a needed close -> VOID
  price_missing (never filled). SPY is fetched once per run.
- "without the largest 5% of window returns" drops ceil(5% x n) events with the largest (most positive)
  beta-adjusted window excess: the conservative cut for a "> 0" claim.
- The bootstrap seed is int(sha256(test name)) mod 2**32.
- Primary test: the CBB if the registered size gate passed, else KV fixed-b NW (lag 20) - registry/
  D009_v3_size_gate.json, verified against its hash in D009_implementation_v3.sha256 before any report.
- MDE = 2.487 x se, with se the NW (lag 20) se of the daily mean when KV is primary (the CBB se when the CBB
  is). 2.487 uses normal critical values; under fixed-b the true MDE is larger (~2.3 + 0.84 at b ~ 0.35).
- "beta-1 and ETF point estimates not negative" (§3) = the calendar-time portfolio's mean daily beta-1 excess
  and mean daily ETF excess (events with an ETF), both must exist and be >= 0. Event-level means are secondaries.
"""
import datetime
import glob
import hashlib
import json
import math
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ET, ROOT, now_et, write_json  # noqa: E402
from sessions import is_session, shift  # noqa: E402

D = datetime.date.fromisoformat
AIH = ("semis", "hardware_networking", "ai_infra")
WINDOW, BETA_N, BETA_MIN = 20, 250, 120
COST = 0.002
BLOCK, DRAWS = 20, 9999
RULE_FILE = "registry/D009_shadow_tracks_v3.md"


# ---------------------------------------------------------------- dates
def git_date_et(*paths, first=True):
    """ET date of the first (or last) commit touching paths."""
    out = subprocess.run(["git", "log", "--format=%cI", "--", *paths], cwd=ROOT, capture_output=True,
                         text=True).stdout.split()
    if not out:
        return None
    s = out[-1] if first else out[0]
    return datetime.datetime.fromisoformat(s).astimezone(ET).date()


def season_files(season):
    u = os.path.join(ROOT, "universe", season)
    return (json.load(open(os.path.join(u, "candidates.json"), encoding="utf-8")),
            json.load(open(os.path.join(u, "raw", "nasdaq_calendar.json"), encoding="utf-8")),
            os.path.join(u, "raw", "av_calendar.csv"))


def d_exp_from(ticker, nasdaq, av_path, window):
    """§2: earliest Nasdaq date in the window, else earliest AV; both and different -> the earlier."""
    import csv
    lo, hi = window
    nd = sorted(day for day, rows in (nasdaq.get("days") or {}).items()
                if lo <= day <= hi and any((r.get("symbol") or "").upper() == ticker.upper() for r in rows))
    ad = sorted(r["reportDate"] for r in csv.DictReader(open(av_path, encoding="utf-8"))
                if (r.get("symbol") or "").upper() == ticker.upper() and lo <= r.get("reportDate", "") <= hi)
    if nd and ad:
        return min(nd[0], ad[0]), {"nasdaq": nd[0], "alphavantage": ad[0]}
    if nd:
        return nd[0], {"nasdaq": nd[0]}
    if ad:
        return ad[0], {"alphavantage": ad[0]}
    return None, {}


def events(season, freeze_date=None, capture_date=None):
    """Every SH-RU event of a season: the S1 candidates, one per issuer, with D_exp, E and the window_not_open void."""
    cand, nasdaq, av_path = season_files(season)
    window = cand["window"]
    freeze_date = freeze_date or git_date_et(RULE_FILE)
    capture_date = capture_date or git_date_et(f"universe/{season}/raw/nasdaq_calendar.json",
                                               f"universe/{season}/raw/av_calendar.csv")
    out, seen = [], set()
    for c in cand["candidates"]:
        t = c["ticker"]
        issuer = c.get("cik") or t
        if issuer in seen:
            continue
        seen.add(issuer)
        dexp, src = d_exp_from(t, nasdaq, av_path, window)
        ev = {"season": season, "ticker": t, "cluster": c.get("cluster"), "etf": c.get("etf"), "cik": c.get("cik"),
              "aih": c.get("cluster") in AIH, "D_exp": dexp, "D_exp_sources": src, "void": None, "flags": []}
        if not dexp:
            ev["void"] = "no_expected_date"
        else:
            E = shift(D(dexp), -(WINDOW + 1))
            ev["E"] = E.isoformat()
            if not (E > freeze_date and (capture_date is None or E > capture_date)):
                ev["void"] = "window_not_open"
        out.append(ev)
    return out


def company_date(season, ticker, status):
    """Earliest company-confirmed report date for the name in this season, or None."""
    dates = [os.path.basename(os.path.dirname(p)).rsplit("_", 1)[1]
             for p in glob.glob(os.path.join(ROOT, "events", season, f"{ticker}_*", "confirm.json"))]
    st = (status.get("events") or {}).get(ticker) or {}
    if st.get("status") not in (None, "PENDING") and st.get("calendar_date"):
        dates.append(st["calendar_date"])
    return min(dates) if dates else None


def sec_date(sec, cik, after):
    """ET date of the first Item 2.02 8-K accepted on or after `after`, or None. Raises on SEC errors."""
    if not cik:
        return None
    rec = sec.submission(int(cik))["filings"]["recent"]
    hits = []
    for i, form in enumerate(rec["form"]):
        if form == "8-K" and "2.02" in [x.strip() for x in (rec["items"][i] or "").split(",")]:
            x = datetime.datetime.fromisoformat(rec["acceptanceDateTime"][i].replace("Z", "+00:00")).astimezone(ET)
            if x.date() >= after:
                hits.append(x.date())
    return min(hits) if hits else None


def resolve_window(ev, d_act, today):
    """X, or the reason it is not yet known. Mutates ev (void, flags, D_act, X)."""
    E, dexp = D(ev["E"]), D(ev["D_exp"])
    if d_act:
        ev["D_act"] = d_act.isoformat()
        if d_act <= shift(E, 1):
            ev["void"] = "print_before_window"
            return None
        return min(shift(E, WINDOW), shift(d_act, -1))
    if today > shift(dexp, 30):
        ev["flags"].append("print_date_unknown")
        return shift(E, WINDOW)
    return None


# ---------------------------------------------------------------- returns
def daily_returns(closes, dates):
    """{date: r} for consecutive pairs of `dates` (a session list) where both closes exist."""
    out = {}
    for a, b in zip(dates, dates[1:]):
        if closes.get(a) and closes.get(b):
            out[b] = closes[b] / closes[a] - 1
    return out


def sessions_between(a, b):
    """Sessions from a to b inclusive (both sessions)."""
    out, d = [a], a
    while d < b:
        d = shift(d, 1)
        out.append(d)
    return out


def compute(ev, px):
    """§2 returns from stored prices. px = {"stock": {iso: close}, "SPY": {...}, "ETF": {...} or None}."""
    E, X = D(ev["E"]), D(ev["X"])
    s, m, f = px["stock"], px["SPY"], px.get("ETF")
    win = [d.isoformat() for d in sessions_between(E, X)]
    if any(not s.get(d) or not m.get(d) for d in win):
        return {"void": "price_missing"}
    pre = [d.isoformat() for d in sessions_between(shift(E, -(BETA_N + 1)), shift(E, -1))]
    rs, rm = daily_returns(s, pre), daily_returns(m, pre)
    common = sorted(set(rs) & set(rm))
    flags = []
    if len(common) < BETA_MIN:
        beta_raw, beta = None, 1.0
        flags.append("beta_short")
    else:
        y, x = np.array([rs[d] for d in common]), np.array([rm[d] for d in common])
        beta_raw = float(np.cov(x, y, ddof=1)[0, 1] / np.var(x, ddof=1))
        beta = 0.67 * beta_raw + 0.33
    ds, dm = daily_returns(s, win), daily_returns(m, win)
    df = daily_returns(f, win) if f and all(f.get(d) for d in win) else None
    days = [d for d in win[1:]]
    daily = [{"date": d, "r": ds[d], "spy": dm[d], "ba": ds[d] - beta * dm[d], "b1": ds[d] - dm[d],
              "etf": (ds[d] - df[d]) if df else None} for d in days]
    R = s[win[-1]] / s[win[0]] - 1
    RM = m[win[-1]] / m[win[0]] - 1
    RF = (f[win[-1]] / f[win[0]] - 1) if df else None
    out = {"beta_raw": beta_raw, "beta": beta, "n_beta_returns": len(common), "R": R, "R_spy": RM, "R_etf": RF,
           "excess_beta": R - beta * RM, "excess_beta1": R - RM, "excess_etf": (R - RF) if RF is not None else None,
           "net": R - beta * RM - COST, "sessions": len(days), "daily": daily, "flags": flags}
    if not df:
        out["flags"].append("no_etf")
    return out


class FetchFailed(Exception):
    pass


_SPY = {}


def yf_closes(sym, start, end):
    import yfinance as yf
    h = yf.Ticker(sym).history(start=start, end=end, auto_adjust=True)
    if h is None or h.empty:
        return {}
    h.index = h.index.tz_convert(ET) if h.index.tz is not None else h.index
    return {i.date().isoformat(): float(v) for i, v in h["Close"].items() if v == v}


def fetch_prices(ev):
    """Adjusted closes for the stock, SPY (fetched once per run) and the sector ETF. Raises FetchFailed on an
    exception or an empty stock / SPY series: nothing is stored and the event is retried."""
    E, X = D(ev["E"]), D(ev["X"])
    start = shift(E, -(BETA_N + 5)).isoformat()
    end = (X + datetime.timedelta(days=1)).isoformat()
    try:
        if "closes" not in _SPY:
            _SPY["closes"] = yf_closes("SPY", "2024-01-01", (datetime.date.today() + datetime.timedelta(days=1)).isoformat())
        spy = {d: v for d, v in _SPY["closes"].items() if start <= d < end}
        stock = yf_closes(ev["ticker"].replace(".", "-"), start, end)
        etf = yf_closes(ev["etf"], start, end) if ev.get("etf") else None
    except Exception as exc:
        raise FetchFailed(f"{type(exc).__name__}: {exc}")
    if not stock or not spy:
        raise FetchFailed("empty stock or SPY series")
    return {"stock": stock, "SPY": spy, "ETF": etf or None}


# ---------------------------------------------------------------- grading (write-once)
def jsonl(path):
    if not os.path.exists(path):
        return {}
    out = {}
    for line in open(path, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            out[r["key"]] = r
    return out


def append(path, rec):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")


def grade(season, now=None, sec=None, fetch=fetch_prices):
    now = now or now_et()
    today = now.date()
    odir = os.path.join(ROOT, "outcomes", "shadow", season)
    ppath, gpath = os.path.join(odir, "runup_prices.jsonl"), os.path.join(odir, "runup.jsonl")
    prices, graded = jsonl(ppath), jsonl(gpath)
    fpath = os.path.join(odir, "runup_fetch_failures.json")
    failures = json.load(open(fpath, encoding="utf-8")) if os.path.exists(fpath) else {}
    status_p = os.path.join(ROOT, "universe", season, "event_status.json")
    status = json.load(open(status_p, encoding="utf-8")) if os.path.exists(status_p) else {}
    if sec is None:
        from common import Sec
        sec = Sec(os.path.join(ROOT, ".cache", "sec"))
    done = 0
    for ev in events(season):
        key = f"{season}-{ev['ticker']}"
        if key in graded:
            continue
        if ev["void"] == "no_expected_date":
            continue                                   # not an SH-RU event: counted by `events`, never graded
        if ev["void"]:
            append(gpath, {"key": key, **ev, "graded_et": now.isoformat()})
            continue
        E = D(ev["E"])
        if today < shift(E, 2):
            continue
        cdate = company_date(season, ev["ticker"], status)
        try:
            sdate = sec_date(sec, ev.get("cik"), shift(E, 2))
        except Exception as exc:                      # an SEC error decides nothing; retried next run
            print(f"{key}: SEC error {type(exc).__name__} - retried next run")
            continue
        ev["D_act_company"], ev["D_act_sec"] = cdate, sdate.isoformat() if sdate else None
        ds = [x for x in (D(cdate) if cdate else None, sdate) if x]
        X = resolve_window(ev, min(ds) if ds else None, today)
        if ev["void"]:
            append(gpath, {"key": key, **ev, "graded_et": now.isoformat()})
            continue
        if X is None:
            continue
        ev["X"] = X.isoformat()
        if now < datetime.datetime.combine(shift(X, 1), datetime.time(6, 0), ET):
            continue
        if key not in prices:
            try:
                px = fetch(ev)
            except FetchFailed as exc:
                days = sorted(set(failures.get(key, [])) | {today.isoformat()})
                failures[key] = days
                write_json(fpath, failures)
                print(f"{key}: price fetch failed ({exc}) - {len(days)} failed date(s)")
                if len(days) >= 10:
                    append(gpath, {"key": key, **ev, "void": "price_unavailable", "graded_et": now.isoformat()})
                continue
            prices[key] = {"key": key, "fetched_et": now.isoformat(), "source": "yfinance auto_adjust=True",
                           "single_source": True, **px}
            append(ppath, prices[key])
        res = compute(ev, prices[key])
        rec = {"key": key, **ev, **{k: v for k, v in res.items() if k != "flags"}, "graded_et": now.isoformat()}
        rec["flags"] = ev["flags"] + res.get("flags", [])
        if res.get("void"):
            rec["void"] = res["void"]
        append(gpath, rec)
        graded[key] = rec
        done += 1
    print(f"{season} SH-RU: {done} newly graded; {len(jsonl(gpath))} records")
    return done


# ---------------------------------------------------------------- statistics (§3)
def seed(name):
    return int(hashlib.sha256(name.encode()).hexdigest(), 16) % 2 ** 32


def cbb_p(series, name, draws=DRAWS, block=BLOCK):
    """Circular block bootstrap, null imposed by demeaning: p = share of bootstrap means >= observed."""
    y = np.asarray(series, float)
    n = len(y)
    obs = float(y.mean())
    z = y - obs
    rng = np.random.default_rng(seed(name))
    nb = math.ceil(n / block)
    starts = rng.integers(0, n, size=(draws, nb))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(draws, -1)[:, :n] % n
    means = z[idx].mean(axis=1)
    return float((means >= obs).mean()), float(means.std(ddof=1)), obs


def nw_t(series, lag):
    y = np.asarray(series, float)
    n, mu = len(y), y.mean()
    e = y - mu
    s = e @ e / n
    for k in range(1, min(lag, n - 1) + 1):
        s += 2 * (1 - k / (lag + 1)) * (e[k:] @ e[:-k]) / n
    return float(mu / math.sqrt(s / n)) if s > 0 else float("nan")


_KV = {}


def kv_null(M, sims=20000, Tsim=1000, batch=2000):
    """Fixed-b null distribution (Kiefer-Vogelsang) of the Bartlett-NW t with bandwidth fraction b = M/T,
    simulated at T = Tsim with iid N(0,1) data and bandwidth round(b*Tsim). Cached and seeded by b."""
    key = round(M, 4)
    if key not in _KV:
        Ms = max(1, int(round(M * Tsim)))
        rng = np.random.default_rng(seed(f"kv-{key}"))
        k = np.arange(Ms)
        w = np.where(k == 0, 1.0, 2 * (1 - k / Ms))
        out = []
        for _ in range(sims // batch):
            x = rng.standard_normal((batch, Tsim))
            mu = x.mean(axis=1)
            e = x - mu[:, None]
            f = np.fft.rfft(e, n=2 * Tsim, axis=1)
            ac = np.fft.irfft(f * np.conj(f), axis=1)[:, :Ms] / Tsim
            lrv = ac @ w
            out.append(mu / np.sqrt(lrv / Tsim))
        _KV[key] = np.sort(np.concatenate(out))
    return _KV[key]


def kv_p(series, lag=20):
    """One-sided p of the NW t (Bartlett, lag) against its fixed-b null at b = (lag + 1) / T."""
    y = np.asarray(series, float)
    t = nw_t(y, lag)
    if t != t:
        return 1.0, t
    null = kv_null((min(lag, len(y) - 1) + 1) / len(y))
    return float(1 - np.searchsorted(null, t, side="left") / len(null)), t


def nw_se(series, lag):
    y = np.asarray(series, float)
    n = len(y)
    e = y - y.mean()
    s = e @ e / n
    for k in range(1, min(lag, n - 1) + 1):
        s += 2 * (1 - k / (lag + 1)) * (e[k:] @ e[:-k]) / n
    return float(math.sqrt(s / n)) if s > 0 else float("nan")


def portfolio(rows, field="ba"):
    by = {}
    for e in rows:
        for d in e["daily"]:
            if d[field] is not None:
                by.setdefault(d["date"], []).append(d[field])
    days = sorted(by)
    return days, [float(np.mean(by[d])) for d in days]


def alpha_on_spy(rows):
    by = {}
    for e in rows:
        for d in e["daily"]:
            by.setdefault(d["date"], []).append((d["r"], d["spy"]))
    days = sorted(by)
    y = np.array([np.mean([a for a, _ in by[d]]) for d in days])
    x = np.array([by[d][0][1] for d in days])
    if len(days) < 3:
        return None
    X = np.column_stack([np.ones_like(x), x])
    if np.linalg.matrix_rank(X) < 2:                 # SPY constant over the sample: no regression
        return {"alpha_daily": None, "se_nw5": None, "note": "SPY returns have no variation"}
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    u = y - X @ b
    # NW (lag 5) se of the intercept
    n, L = len(y), 5
    S = (X * u[:, None]).T @ (X * u[:, None]) / n
    for k in range(1, min(L, n - 1) + 1):
        G = (X[k:] * u[k:, None]).T @ (X[:-k] * u[:-k, None]) / n
        S += (1 - k / (L + 1)) * (G + G.T)
    Q = np.linalg.inv(X.T @ X / n)
    V = Q @ S @ Q / n
    return {"alpha_daily": float(b[0]), "se_nw5": float(math.sqrt(V[0, 0])) if V[0, 0] > 0 else None}


def event_level(rows, field):
    import report
    v = [(e[field], e["E"]) for e in rows if e.get(field) is not None]
    if len(v) < 3 or len({g for _, g in v}) < 2:
        return {"n": len(v), "mean": float(np.mean([x for x, _ in v])) if v else None}
    y, g = np.array([x for x, _ in v]), np.array([g for _, g in v])
    b, se, t = report.ols_k(y, np.ones((len(y), 1)), g, 0)
    return {"n": len(v), "mean": float(b), "median": float(np.median(y)), "t_clustered_E": float(t)}


def one_test(rows, name, seasons):
    days, ser = portfolio(rows)
    out = {"n": len(rows), "sessions": len(days), "E_dates": len({e["E"] for e in rows}),
           "by_season": {s: sum(1 for e in rows if e["season"] == s) for s in seasons}}
    if len(ser) < 3:
        out.update(note="too few", p=1.0)
        return out
    p_cbb, se_cbb, obs = cbb_p(ser, name)
    p_kv, _ = kv_p(ser, 20)
    primary = primary_test()
    p = p_kv if primary == "kv" else p_cbb
    se = nw_se(ser, 20) if primary == "kv" else se_cbb
    _, s1 = portfolio(rows, "b1")
    _, se_ = portfolio(rows, "etf")
    out.update(mean_daily=obs, primary=primary, p_cbb=p_cbb, p_kv_fixed_b=p_kv, se_cbb=se_cbb, se_nw20=nw_se(ser, 20),
               mde=2.487 * se if se == se else None, nw_t_lag5=nw_t(ser, 5), nw_t_lag20=nw_t(ser, 20),
               portfolio_mean_daily_beta1=float(np.mean(s1)) if s1 else None,
               portfolio_mean_daily_etf=float(np.mean(se_)) if se_ else None,
               alpha_on_spy=alpha_on_spy(rows),
               event_beta=event_level(rows, "excess_beta"), event_beta1=event_level(rows, "excess_beta1"),
               event_etf=event_level(rows, "excess_etf"), event_net=event_level(rows, "net"))
    k = math.ceil(0.05 * len(rows))
    trimmed = sorted(rows, key=lambda e: e["excess_beta"])[:len(rows) - k]
    _, ser_t = portfolio(trimmed)
    if len(ser_t) >= 3:
        pt, _, ot = cbb_p(ser_t, name + "-trim5")  # noqa: F841
        out["without_top_5pct"] = {"dropped": k, "mean_daily": ot, "p_cbb": pt, "p_kv_fixed_b": kv_p(ser_t, 20)[0]}
    out["p"] = p
    return out


SIZE_GATE = os.path.join("registry", "D009_v3_size_gate.json")


def primary_test():
    """§3: the CBB is primary only if the frozen size-gate result says it passed; otherwise KV fixed-b NW."""
    p = os.path.join(ROOT, SIZE_GATE)
    impl = os.path.join(ROOT, "registry", "D009_implementation_v3.sha256")
    if not os.path.exists(p) or not os.path.exists(impl):
        raise SystemExit("D009 v3 §3: no registered size-gate result - nothing can be reported")
    want = [ln.split()[0] for ln in open(impl, encoding="utf-8")
            if ln.strip() and not ln.startswith("#") and ln.split()[-1].replace("\\", "/") == SIZE_GATE.replace("\\", "/")]
    got = hashlib.sha256(open(p, "rb").read().replace(b"\r\n", b"\n")).hexdigest()
    if want != [got]:
        raise SystemExit("D009 v3 §3: the size-gate file does not match its registered hash")
    return "cbb" if json.load(open(p, encoding="utf-8"))["passed"] else "kv"


def sufficient(r, aih, seasons, pooled):
    ok = r["n"] >= 30 and r.get("sessions", 0) >= 40 and r.get("E_dates", 0) >= 10
    if aih:
        ok = ok and all(r["by_season"].get(s, 0) >= 10 for s in seasons)
    return ok


def report_(seasons, write=False, final=False):
    import report
    if any(s.lower().startswith("pilot") for s in seasons):
        raise SystemExit("D009 §6: the pilot is never part of SH-RU")
    rows, voids = [], {}
    for s in seasons:
        for r in jsonl(os.path.join(ROOT, "outcomes", "shadow", s, "runup.jsonl")).values():
            if r.get("void"):
                voids.setdefault(r["void"], {}).setdefault(r.get("cluster") or "none", 0)
                voids[r["void"]][r.get("cluster") or "none"] += 1
            elif r.get("daily"):
                rows.append(r)
    res = {"H-RU": one_test(rows, "H-RU", seasons), "H-RU-AIH": one_test([e for e in rows if e["aih"]], "H-RU-AIH", seasons)}
    adj = report.holm({k: res[k].get("p", 1.0) for k in res})
    for k, r in res.items():
        r["p_holm"] = adj[k]
        if not sufficient(r, k == "H-RU-AIH", seasons, len(seasons) > 1):
            r["status"] = "insufficient"
        elif not final:
            r["status"] = "interim (monitoring only)"
        else:
            b1, et = r.get("portfolio_mean_daily_beta1"), r.get("portfolio_mean_daily_etf")
            sig = adj[k] < 0.05 and b1 is not None and b1 >= 0 and et is not None and et >= 0
            r["status"] = ("p < 0.05 (shadow, secondary; D009 v3 family m = 2) - late-window reporters only" if sig else
                           f"no evidence (shadow) - an effect smaller than {r['mde'] * 100:.3f} pts a day would usually "
                           "be missed - late-window reporters only" if r.get("mde") else
                           "no evidence (shadow) - late-window reporters only")
    unknown = [e for e in rows if "print_date_unknown" in e.get("flags", [])]
    out = {"seasons": seasons, "rule": "D009_shadow_tracks_v3 §3", "run_et": now_et().isoformat(timespec="seconds"),
           "label": "SHADOW - secondary" + ("" if final else "; INTERIM - no verdict"), "tests": res,
           "without_print_date_unknown": {
               "H-RU": one_test([e for e in rows if e not in unknown], "H-RU-known", seasons),
               "H-RU-AIH": one_test([e for e in rows if e not in unknown and e["aih"]], "H-RU-AIH-known", seasons)}
           if unknown else None,
           "no_expected_date": {s: sum(1 for e in events(s) if e["void"] == "no_expected_date") for s in seasons},
           "voids_by_cluster": voids, "beta_short": sum("beta_short" in e.get("flags", []) for e in rows),
           "no_etf": sum("no_etf" in e.get("flags", []) for e in rows)}
    for k, r in res.items():
        print(f"{k}: n={r['n']} sessions={r.get('sessions')} p_cbb={r.get('p_cbb')} holm={r['p_holm']:.3f} {r['status']}")
    if write:
        write_json(os.path.join(ROOT, "outcomes", "shadow", "reports",
                                f"runup_{'+'.join(seasons)}_{now_et():%Y-%m-%d}.json"), out)
    return out


# ---------------------------------------------------------------- size gate (§3)
def size_gate(sims=2000, ns=(30, 45, 60), season="seasonA", out_path=None, draws=DRAWS):
    """Synthetic null data with SH-RU's overlap: E dates resampled from the season's open windows, two seasons
    pooled (the second offset by 65 sessions), daily excess returns = a common factor (sd 1%) + idiosyncratic t(5)
    noise (sd 2.5%), mean 0. Size = rejection rate of the CBB at nominal 5%."""
    evs = [e for e in events(season) if not e["void"]]
    pattern = sorted({e["E"] for e in evs})
    if not pattern:
        raise SystemExit("no open SH-RU windows to take the overlap from")
    base = D(pattern[0])
    offs = [len(sessions_between(base, D(x))) - 1 for x in pattern]
    rng = np.random.default_rng(seed("size-gate"))
    res = {}
    res_kv = {}
    cases = [(n, True) for n in ns] + [(30, False)]       # pooled A + B, plus one season alone (short T)
    for n, pooled in cases:
        rej = rej_kv = 0
        for i in range(sims):
            starts = [rng.choice(offs) + (65 if (pooled and j % 2) else 0) for j in range(n)]
            T = max(starts) + WINDOW + 1
            common = rng.normal(0, 0.01, T)
            tot, cnt = np.zeros(T), np.zeros(T)
            for s in starts:
                idio = rng.standard_t(5, WINDOW) * 0.025 / math.sqrt(5 / 3)
                tot[s + 1:s + 1 + WINDOW] += common[s + 1:s + 1 + WINDOW] + idio
                cnt[s + 1:s + 1 + WINDOW] += 1
            ser = tot[cnt > 0] / cnt[cnt > 0]
            p, _, _ = cbb_p(ser, f"size-{n}-{pooled}-{i}", draws=draws)
            rej += p < 0.05
            rej_kv += kv_p(ser, 20)[0] < 0.05
        lab = f"{n}{'' if pooled else '_one_season'}"
        res[lab] = rej / sims
        res_kv[lab] = rej_kv / sims
    passed = all(v <= 0.07 for v in res.values())
    out = {"rule": "D009 v3 §3 size gate", "run_et": now_et().isoformat(timespec="seconds"), "season_pattern": season,
           "open_E_dates": pattern, "sims_per_n": sims, "bootstrap_draws_per_sim": draws,
           "design": "E dates resampled from the season's open windows; pooled = two seasons, the second offset by "
                     "65 sessions; daily excess = common N(0, 1%) + idiosyncratic t(5) scaled to 2.5%, mean 0. "
                     "Disclosed: iid noise, no volatility clustering or autocorrelation",
           "size_at_nominal_5pct": res, "threshold": 0.07, "passed": passed,
           "kv_fixed_b_size_at_nominal_5pct": res_kv, "kv_null": "simulated fixed-b, T 1000, 20000 draws, seed by b",
           "primary": "circular block bootstrap" if passed else "KV fixed-b NW (lag 20)"}
    print(json.dumps(out))
    if out_path:
        write_json(out_path, out)
    return out


def commit(msg):
    from freeze import git, push_all
    git("add", os.path.join("outcomes", "shadow"))
    if not git("diff", "--cached", "--name-only"):
        print("nothing new to commit")
        return
    git("commit", "-q", "-m", msg + "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
    print(f"pushed: {push_all()}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["events"]:
        evs = events(a[1])
        from collections import Counter
        print(Counter(e["void"] for e in evs))
        for e in evs:
            if not e["void"]:
                print(e["ticker"], e["cluster"], "D_exp", e["D_exp"], "E", e["E"], "AIH" if e["aih"] else "")
    elif a[:1] == ["grade"]:
        for s in a[1:]:
            if not s.startswith("--"):
                grade(s)
        if "--commit" in a:
            commit(f"SH-RU grade as of {now_et():%Y-%m-%d %H:%M} ET (code, D009 v3)")
    elif a[:1] == ["report"]:
        report_([x for x in a[1:] if not x.startswith("--")], "--write" in a, "--final" in a)
    elif a[:1] == ["size-gate"]:
        n = int(a[a.index("--sims") + 1]) if "--sims" in a else 2000
        size_gate(n, out_path=os.path.join(ROOT, "registry", "D009_v3_size_gate.json") if "--write" in a else None)
    else:
        raise SystemExit(__doc__)
