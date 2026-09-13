"""
PRE batch runner — the ONE path a live batch should take. GG wired in.
================================================================================
Built 2026-07-30. Replaces the copy-a-dated-run-file workflow, which is what allowed the
2026-07-29 batch to be scored 3.5 hours AFTER its own prints and then voided.

WHAT IT DOES
    1. CLOCK GUARD    refuses to register once the print cutoff has passed. In code, not in
                      my memory. This is the whole reason the module exists.
    2. MARKET PULL    price, gap history, gap_bad_case, liquidity, positioning vs sector ETF.
    3. OPTIONS PULL   straddle -> decontaminated implied move (fails closed), revisions, coverage.
    4. GG             loads a verified guidance file if present; otherwise fetches the EDGAR
                      excerpts so they can be read, and proceeds with GG=None DECLARED.
    5. SCORE          pre_edgescore v1.5.0, then optionally freezes to the ledger.

USAGE
    python pre_batch.py --tickers META,FICO --event-date 2026-10-27 --session amc
    python pre_batch.py --tickers META,FICO --event-date 2026-10-27 --session amc --gg-fetch
    python pre_batch.py --tickers META,FICO --event-date 2026-10-27 --session amc --register

THE GG HANDOFF, and why it is shaped this way
GG cannot be fully automated: guidance prose is not reliably machine-parseable, and a regex
that silently mis-reads a range would inject a fabricated value into the one term built to be
unfabricated (see pre_guidance). So the loop is:

    --gg-fetch   ->  writes gg_inbox_<event_date>.json  (EDGAR excerpts + citations)
    [read it, fill in gg_<event_date>.json]              (numbers transcribed, sources pre-filled)
    normal run   ->  picks that file up automatically and passes GG into the Judgment

If no gg_<event_date>.json exists the batch still runs, with GG=None DECLARED per name — never
silently defaulted to 0, which would read as "guidance is flat" when the truth is "not looked at".
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import yfinance as yf

from pre_engine import Judgment, Market, Truth, Skew, EngineConfig
from pre_edgescore import edge_score, render, register
from pre_guidance import GuidanceRecord, combine, render as gg_render
from pre_impliedmove import decontaminate

__version__ = "1.0.0"

ROOT = Path(__file__).resolve().parent
ET = ZoneInfo("America/New_York")
CFG = EngineConfig(fasttrack=True, watch=False, react_in_ds=False)

# Session cutoffs in EXCHANGE time. A pre-registration must be frozen before these.
CUTOFF = {"amc": time(16, 0), "bmo": time(9, 30)}

DEFAULT_ETF = {"XLK": ("MSFT", "FTNT", "FICO", "CTSH", "IBM", "NOW", "AAPL", "MSTR",
                       "BBAI", "CHKP"),
               "SMH": ("ARM", "QCOM", "LRCX", "KLAC", "AMKR", "INTC", "TSM", "ASML", "NVDA",
                       "PLAB", "AEHR", "NVTS", "ONTO", "COHU", "AVGO"),
               "XLC": ("META", "GOOG", "NFLX", "CHTR", "VZ", "RDDT", "RBLX"),
               "XLF": ("HOOD", "SOFI", "LMND", "V", "SPGI", "PYPL", "COIN"),
               "XLV": ("BSX", "HUM", "AVTR", "UNH", "AZN", "TEM", "SYK", "ABBV"),
               "XLI": ("VRT", "JCI", "VRSK", "GE", "NVT"),
               "IGV": ("CRM", "CRWD", "SNPS", "CDNS", "NTNX", "VEEV", "ADBE", "ADSK",
                       "PANW", "ZS", "DDOG", "MDB", "TEAM", "WDAY", "ORCL"),
               "XLY": ("AMZN", "RIVN"),
               "TAN": ("FSLR",),
               "XLP": ("PG", "KO")}
ETF_OF = {t: e for e, ts in DEFAULT_ETF.items() for t in ts}


# --------------------------------------------------------------- 1. clock guard
def cutoff_utc(event_date: str, session: str) -> datetime:
    d = datetime.strptime(event_date, "%Y-%m-%d").date()
    return datetime.combine(d, CUTOFF[session], tzinfo=ET).astimezone(timezone.utc)


def clock_guard(event_date: str, session: str, registering: bool) -> dict:
    """The guard that would have stopped the 2026-07-29 batch from ever being written.

    A pre-registration is only meaningful if it is frozen BEFORE the event. Enforcing that
    by remembering to check is exactly what failed; so it is enforced here, and --register
    is refused outright once the cutoff has passed.
    """
    now = datetime.now(timezone.utc)
    cut = cutoff_utc(event_date, session)
    left = cut - now
    info = {"now_et": now.astimezone(ET).strftime("%Y-%m-%d %H:%M:%S ET"),
            "cutoff_et": cut.astimezone(ET).strftime("%Y-%m-%d %H:%M:%S ET"),
            "minutes_left": int(left.total_seconds() // 60), "past": now >= cut}
    if info["past"] and registering:
        raise SystemExit(
            f"\nREGISTRATION REFUSED — the {session.upper()} cutoff for {event_date} passed at "
            f"{info['cutoff_et']} and it is now {info['now_et']}.\n"
            f"A verdict produced after its own event is not a pre-registration; it is a "
            f"counterfactual (HANDOFF §14). Run it --dry and label it VOID, or wait for the "
            f"next event.\n")
    if info["past"]:
        print(f"  !! POST-CUTOFF by {abs(info['minutes_left'])} min — dry only, cannot register.")
    else:
        print(f"  clock OK: {info['minutes_left']} min until the {session.upper()} cutoff "
              f"({info['cutoff_et']}).")
    return info


# ------------------------------------------------------------- 2. market inputs
def market_pull(tickers, asof: str | None = None) -> dict:
    etfs = {ETF_OF.get(t, "SPY") for t in tickers}
    px = {e: yf.Ticker(e).history(period="2y", auto_adjust=False) for e in etfs}
    out = {}
    for t in tickers:
        etf = ETF_OF.get(t, "SPY")
        h = yf.Ticker(t).history(period="5y", auto_adjust=False)
        if h.empty:
            print(f"  {t}: NO PRICE HISTORY — skipped"); continue
        dates = [d.date() for d in h.index]
        gaps, used = [], []
        try:
            ed = yf.Ticker(t).get_earnings_dates(limit=40)
            past = ed[ed["Reported EPS"].notna()] if ed is not None else None
        except Exception:
            past = None
        if past is not None:
            for ts in past.index:
                d, amc = ts.date(), (ts.hour + ts.minute / 60.0) >= 12.0
                after = [i for i, dd in enumerate(dates) if (dd > d if amc else dd >= d)]
                if not after or after[0] == 0:
                    continue
                i = after[0]
                c = float(h["Close"].iloc[i - 1])
                if c <= 0:
                    continue
                gaps.append(abs(float(h["Open"].iloc[i]) / c - 1.0) * 100.0)
                used.append(str(d))
                if len(gaps) >= 10:
                    break
        price = float(h["Close"].iloc[-1])
        hi52 = float(h["High"].tail(252).max())
        ped = ep = None
        if used:
            ld = pd.Timestamp(used[0]).date()
            b = [i for i, dd in enumerate(dates) if dd >= ld]
            if b:
                ped = (price / float(h["Close"].iloc[b[0]]) - 1.0) * 100.0
                eh = px[etf]; ed_ = [d.date() for d in eh.index]
                eb = [i for i, dd in enumerate(ed_) if dd >= ld]
                if eb:
                    ep = (float(eh["Close"].iloc[-1]) / float(eh["Close"].iloc[eb[0]]) - 1) * 100
        out[t] = {"price": price, "mean": float(np.mean(gaps)) if gaps else None,
                  "bad": float(np.max(gaps)) if gaps else None, "nq": len(gaps),
                  "dv": float((h["Close"] * h["Volume"]).tail(20).mean()),
                  "sv": float(h["Volume"].tail(20).mean()),
                  "ped": ped, "ep": ep, "blw": (hi52 - price) / hi52 * 100.0,
                  "etf": etf, "gaps": gaps, "lastdate": used[0] if used else None}
    return out


def options_pull(tickers, mkt: dict, asof: str) -> dict:
    out = {}
    for t in tickers:
        tk = yf.Ticker(t); o = {}
        try:
            spot = mkt[t]["price"]
            exps = [x for x in tk.options if x >= asof]
            if exps:
                ex = exps[0]
                ch = tk.option_chain(ex); c, p = ch.calls, ch.puts
                k = sorted(set(c.strike) & set(p.strike), key=lambda x: abs(x - spot))[0]

                def mid(df):
                    r = df[df.strike == k].iloc[0]; b, a = float(r.bid), float(r.ask)
                    return (b + a) / 2 if (b > 0 and a > 0) else float(r.lastPrice)
                o["raw"] = round((mid(c) + mid(p) - abs(spot - k)) / spot * 100, 2)
                o["exp"] = ex; o["xd"] = int(np.busday_count(asof, ex))
                near = lambda df: float(df[(df.strike > spot * .85)
                                          & (df.strike < spot * 1.15)].openInterest.sum())
                o["pc"] = round(near(p) / max(near(c), 1), 2)
        except Exception as e:
            o["err"] = repr(e)[:60]
        try:
            hh = tk.history(period="6mo")
            r = np.log(hh["Close"] / hh["Close"].shift(1)).dropna()
            o["rv"] = round(float(r.tail(63).std() * np.sqrt(252) * 100), 1)
        except Exception:
            o["rv"] = None
        i = tk.info
        o["an"] = i.get("numberOfAnalystOpinions"); o["si"] = i.get("shortPercentOfFloat")
        try:
            er = tk.eps_revisions
            o["u30"] = int(er.loc["0q", "upLast30days"]); o["d30"] = int(er.loc["0q", "downLast30days"])
            o["u7"] = int(er.loc["0q", "upLast7days"]); o["d7"] = int(er.loc["0q", "downLast7Days"])
        except Exception:
            o["u30"] = o["d30"] = o["u7"] = o["d7"] = None
        if o.get("raw") and o.get("rv") is not None:
            dec = decontaminate(o["raw"], o["rv"], o.get("xd", 0))
            o["evtIM"] = dec.get("implied_move"); o["basis"] = dec.get("implied_move_basis")
            o["varRm"] = dec.get("variance_removed_pct")
        out[t] = o
    return out


# ------------------------------------------------------------------------ 3. GG
def gg_inbox(tickers, event_date: str) -> Path:
    """Fetch the EDGAR guidance excerpts so they can be READ and transcribed."""
    from pre_edgar import guidance_pack
    inbox = {}
    for t in tickers:
        try:
            inbox[t] = guidance_pack(t, n=2)
        except Exception as e:
            inbox[t] = {"ticker": t, "releases": [], "notes": [repr(e)[:140]]}
        n = len(inbox[t]["releases"])
        heads = [r["heading"] for r in inbox[t]["releases"]]
        print(f"  {t:6s} {n} release(s)  headings={heads}")
    p = ROOT / f"gg_inbox_{event_date}.json"
    json.dump(inbox, p.open("w"), indent=1)
    print(f"\n  wrote {p.name} — READ the excerpts, then write gg_{event_date}.json")
    print("  schema: {TICKER: [ {metric, period, prior_low, prior_high, new_low, new_high,\n"
          "                      quote, prior_quote, source_url, source_date}, ... ]}\n"
          "  basis/comparison are filled in automatically; polarity comes from `metric`.")
    return p


def load_gg(tickers, event_date: str) -> dict:
    """Read gg_<event_date>.json into verified GG buckets. Absent file => GG None, declared."""
    p = ROOT / f"gg_{event_date}.json"
    if not p.exists():
        print(f"  no {p.name} — GG=None DECLARED for all names (completeness capped at 3/4)")
        return {t: {"GG": None, "gg_basis": None, "status": "NOT_SOURCED",
                    "reasons": [f"no {p.name}; guidance was not looked at for this batch"]}
                for t in tickers}
    raw = json.load(p.open())
    out = {}
    for t in tickers:
        rows = raw.get(t) or []
        if not rows:
            out[t] = {"GG": None, "gg_basis": None, "status": "NOT_SOURCED",
                      "reasons": [f"no guidance rows for {t} in {p.name}"]}
            continue
        recs = [GuidanceRecord(ticker=t, basis=r.get("basis", "COMPANY_GUIDANCE"),
                               comparison=r.get("comparison", "OWN_PRIOR_GUIDANCE"),
                               **{k: v for k, v in r.items()
                                  if k not in ("basis", "comparison")}) for r in rows]
        res = combine(recs, last_earnings_date=rows[0].get("source_date"),
                      event_date=event_date)
        out[t] = res
        print(f"  {t:6s} " + gg_render(res).replace("\n", "\n         "))
    return out


# --------------------------------------------------------------------- 4. score
def load_vel(tickers, event_date: str) -> dict:
    """VEL from SEC XBRL — fully automated (structured facts, no prose to misread).

    Optional vel_overrides_<event_date>.json opts a name into a deferred-revenue PROXY:
        {"TICKER": {"concept": "ContractWithCustomerLiabilityCurrent", "reason": "..."}}
    Never do that for a broker/bank/insurer — see pre_vel.CONCEPT_MEANING_WARNING.
    """
    from pre_vel import vel_for, render as vel_render
    ov_path = ROOT / f"vel_overrides_{event_date}.json"
    ov = json.load(ov_path.open()) if ov_path.exists() else {}
    if ov:
        print(f"  using proxy-concept overrides from {ov_path.name}: {sorted(ov)}")
    out = {}
    for t in tickers:
        o = ov.get(t) or {}
        try:
            r = vel_for(t, event_date, allow_concept=o.get("concept"),
                        allow_reason=o.get("reason", ""))
        except Exception as e:
            from pre_vel import VelResult
            r = VelResult(t, None, None, "UNSOURCED", reasons=[repr(e)[:140]])
        out[t] = r
        print(f"  {t:6s} " + vel_render(r).replace("\n", "\n         "))
    return out


def build_cases(tickers, mkt, opt, gg, capital, vel=None):
    vel = vel or {}
    cases = []
    for t in tickers:
        v, o, g = mkt.get(t), opt.get(t, {}), gg.get(t, {})
        vr = vel.get(t)
        if not v:
            continue
        j = Judgment(up_revisions_30d=o.get("u30"), down_revisions_30d=o.get("d30"),
                     up_revisions_7d=o.get("u7"), down_revisions_7d=o.get("d7"),
                     covering_analysts=o.get("an"), rev_basis="ESTIMATE_REVISIONS",
                     GG=g.get("GG"), gg_basis=g.get("gg_basis"),
                     VEL=(vr.VEL if vr else None),
                     vel_basis=(vr.vel_basis if vr else None),
                     REACT=None, FLAG=0, CBR="CLEAN", G0="CONFIRMED",
                     stock_pct_since_last_earnings=(round(v["ped"], 2) if v["ped"] is not None else None),
                     sector_etf_pct_same_window=(round(v["ep"], 2) if v["ep"] is not None else None),
                     pct_below_52w_high=round(v["blw"], 2))
        m = Market(price=round(v["price"], 2), avg_abs_open=round(v["mean"] or 0, 2),
                   gap_bad_case=round(v["bad"] or 0, 2), confirmed_quarters=v["nq"],
                   dollar_vol_20d=v["dv"], share_vol_20d=v["sv"],
                   implied_move=o.get("evtIM"), implied_move_raw=o.get("raw"),
                   implied_move_basis=o.get("basis"), implied_move_expiry=o.get("exp"),
                   implied_move_extra_days=o.get("xd"),
                   capital=capital, borrow_locate=True, borrow_fee=0.5)
        tr = Truth(stock_pct_since_last_earnings=(round(v["ped"], 2) if v["ped"] is not None else None),
                   pct_below_52w_high=round(v["blw"], 2), price=round(v["price"], 2))
        sk = Skew(realized_vol_3m=o.get("rv"), days_to_event=1,
                  short_interest_pct_float=(o["si"] * 100 if o.get("si") else None),
                  put_call_oi_ratio=o.get("pc"))
        cases.append((t, j, m, tr, sk))
    return cases


def main(argv=None):
    ap = argparse.ArgumentParser(description="PRE batch runner (GG-wired)")
    ap.add_argument("--tickers", required=True, help="comma-separated")
    ap.add_argument("--event-date", required=True, help="YYYY-MM-DD, the PRINT date")
    ap.add_argument("--session", choices=("amc", "bmo"), default="amc")
    ap.add_argument("--capital", type=float, default=18_000.0)
    ap.add_argument("--gg-fetch", action="store_true", help="fetch EDGAR excerpts and stop")
    ap.add_argument("--register", action="store_true", help="freeze to the ledger")
    ap.add_argument("--note", default="")
    a = ap.parse_args(argv)
    tickers = [x.strip().upper() for x in a.tickers.split(",") if x.strip()]

    print("=" * 100)
    print(f"  PRE BATCH — {len(tickers)} names | {a.session.upper()} {a.event_date} | "
          f"engine-side GG wired | book ${a.capital:,.0f}")
    print("=" * 100)
    guard = clock_guard(a.event_date, a.session, a.register)

    if a.gg_fetch:
        print("\n[GG] fetching EDGAR guidance excerpts")
        gg_inbox(tickers, a.event_date)
        return 0

    print("\n[1/4] market pull")
    mkt = market_pull(tickers)
    print("\n[2/4] options / revisions pull")
    opt = options_pull(tickers, mkt, a.event_date)
    print("\n[3/5] GG  (guidance direction — EDGAR prose, human-read)")
    gg = load_gg(tickers, a.event_date)
    print("\n[4/5] VEL (forward-book acceleration — SEC XBRL, automated)")
    vel = load_vel(tickers, a.event_date)

    print("\n[5/5] score")
    cases = build_cases(tickers, mkt, opt, gg, a.capital, vel)
    res = [(t, edge_score(t, j, m, tr, CFG, skew=sk)) for t, j, m, tr, sk in cases]
    order = {"BUY": 0, "SHORT": 1, "NO_TRADE": 2}
    for t, v in sorted(res, key=lambda x: (order[x[1].stance], -abs(x[1].edge_score))):
        print(render(v))
        g, vr = gg.get(t, {}), vel.get(t)
        print(f"      GG {g.get('GG')} [{g.get('status')}]"
              + (f" — {(g.get('detail') or {}).get('how','')[:78]}" if g.get("detail") else ""))
        print(f"      VEL {vr.VEL if vr else None} [{vr.status if vr else 'ABSENT'}]"
              + (f" — book YoY {vr.g_prev:+.1%} -> {vr.g_now:+.1%} ({vr.delta_bps:+,.0f}bp)"
                 if vr and vr.status == "VERIFIED" else ""))
        print("-" * 100)

    # ---- FORECAST: a directional call on EVERY name, always. Never abstains. ----------
    # Owner directive 2026-07-30: on a paper book, abstention protects nothing and teaches
    # nothing. The trade layer above may still say NO_TRADE; this one may not.
    from pre_forecast import forecast as _fc, log_forecast, render as fc_render
    print("\n" + "=" * 100)
    print("  FORECAST LAYER — a stance on every name. Logged to forecasts.jsonl and scored.")
    print("  Separate from the trade verdict; NEVER feeds it.")
    print("=" * 100)
    stance_of = {t: v.stance for t, v in res}
    fcs = []
    for t, j, m, tr, sk in cases:
        v, o, g, vr = mkt[t], opt.get(t, {}), gg.get(t, {}), vel.get(t)
        exc = (j.stock_pct_since_last_earnings - j.sector_etf_pct_same_window
               if (j.stock_pct_since_last_earnings is not None
                   and j.sector_etf_pct_same_window is not None) else None)
        f = _fc(t, expectations=next((x.expectations_momentum for tt, x in res if tt == t), 0.0),
                excess=exc, dd=j.pct_below_52w_high,
                implied_move=m.implied_move, avg_gap=m.avg_abs_open, bad_gap=m.gap_bad_case,
                put_call=sk.put_call_oi_ratio, short_interest=sk.short_interest_pct_float,
                event_date=a.event_date, trade_stance=stance_of.get(t),
                gg=g.get("GG"), vel=(vr.VEL if vr else None))
        f.session = a.session      # so log_forecast can stamp it against the RIGHT cutoff
        fcs.append(f)
        print(fc_render(f))
        log_forecast(f)
    ups = sum(1 for f in fcs if f.direction == "UP")
    print(f"\n  {len(fcs)} forecasts logged ({ups} UP / {len(fcs)-ups} DOWN); "
          f"{sum(1 for f in fcs if f.basis != 'COINFLIP')} carry real signal. "
          f"Score them tomorrow with pre_forecast.score().")

    n_gg = sum(1 for t in tickers if (gg.get(t) or {}).get("status") == "VERIFIED")
    n_vel = sum(1 for t in tickers if (vel.get(t) and vel[t].status == "VERIFIED"))
    n_both = sum(1 for t in tickers
                 if (gg.get(t) or {}).get("status") == "VERIFIED"
                 and (vel.get(t) and vel[t].status == "VERIFIED"))
    print(f"\nGG verified {n_gg}/{len(tickers)} · VEL verified {n_vel}/{len(tickers)} · "
          f"BOTH {n_both}/{len(tickers)} -> those names run at 4/4 completeness "
          f"(confidence 1.00) for the first time.")

    if a.register:
        exit_open = (datetime.strptime(a.event_date, "%Y-%m-%d")
                     + timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"\nREGISTERING (cutoff in {guard['minutes_left']} min) ...")
        for t, j, m, tr, sk in cases:
            rec, v = register(t, j, m, tr, CFG, event_date=a.event_date,
                              entry_close_date=a.event_date, exit_open_date=exit_open,
                              sector_etf=ETF_OF.get(t, "SPY"), skew=sk,
                              note=f"{a.note} | GG={gg.get(t,{}).get('GG')} "
                                   f"[{gg.get(t,{}).get('status')}]".strip(" |"))
            print(f"  {t:6s} {v.stance:9s} {rec['id']}")
    else:
        print("\n(dry — pass --register to freeze these into the ledger)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
