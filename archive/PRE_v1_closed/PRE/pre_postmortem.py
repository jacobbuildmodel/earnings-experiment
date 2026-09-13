"""
PRE post-mortem — score frozen BUY/SHORT calls against the realized earnings gap.
================================================================================
For each ledger entry that is a trade (BUY/SHORT) and has no outcome yet, pull the
OPEN GAP from yfinance:  (open_on_exit_date / close_on_entry_date - 1) * 100
for both the stock and its sector ETF, then log the BETA-STRIPPED outcome:
  idio_open% = stock_gap% - sector_gap%   (the number the model is graded on).

Nothing here fetches until the print has landed. If the exit open isn't in the data
yet, it reports PENDING and moves on. Idempotent: entries already scored are skipped.

Run:  python pre_postmortem.py            # score everything that's ready
      python pre_postmortem.py AEHR       # just one ticker
"""
from __future__ import annotations
import sys
import warnings
warnings.filterwarnings("ignore")

from pre_ledger import _read, record_outcome, stats, render_stats, DEFAULT_LEDGER


def _gap(hist, entry_close_date, exit_open_date):
    """(open_on_exit / close_on_entry - 1)*100, or None if either date missing."""
    import pandas as pd
    h = hist.copy()
    h.index = h.index.tz_localize(None)
    ce = h[h.index <= pd.Timestamp(entry_close_date)]
    oe = h[h.index >= pd.Timestamp(exit_open_date)]
    if len(ce) == 0 or len(oe) == 0:
        return None
    entry_close = float(ce["Close"].iloc[-1])
    exit_open = float(oe["Open"].iloc[0])
    # guard: the exit row must actually be ON/after the exit date (not stale last bar)
    if oe.index[0].date() < pd.Timestamp(exit_open_date).date():
        return None
    return round((exit_open / entry_close - 1) * 100, 2)


def _close_move(hist, entry_close_date, exit_open_date):
    """(close_on_exit / close_on_entry - 1)*100 — the HOLD-TO-CLOSE shadow horizon.
    Measurement only: the live exit remains the first open. Returns None if unavailable."""
    import pandas as pd
    h = hist.copy()
    h.index = h.index.tz_localize(None)
    ce = h[h.index <= pd.Timestamp(entry_close_date)]
    xe = h[h.index >= pd.Timestamp(exit_open_date)]
    if len(ce) == 0 or len(xe) == 0:
        return None
    if xe.index[0].date() < pd.Timestamp(exit_open_date).date():
        return None
    return round((float(xe["Close"].iloc[0]) / float(ce["Close"].iloc[-1]) - 1) * 100, 2)


def estimate_beta(ticker, benchmark, entry_close_date,
                  window=60, gap_days=21, min_obs=30):
    """Market-model beta over a CLEAN PRE-EVENT estimation window (Kothari & Warner).

    beta = Cov(r_stock, r_bench) / Var(r_bench), estimated on daily log returns over
    [entry - gap_days - window, entry - gap_days]. The `gap_days` buffer keeps the
    run-up into THIS print out of the estimate — otherwise the event you are measuring
    contaminates the yardstick you measure it with.

    Returns None if there is not enough clean data; the caller must then fall back to
    beta = 1 and let record_outcome flag the row. Never guesses.
    """
    import numpy as np, pandas as pd, yfinance as yf
    end = pd.Timestamp(entry_close_date) - pd.Timedelta(days=gap_days)
    start = end - pd.Timedelta(days=int(window * 1.6) + 10)      # calendar pad for weekends
    try:
        px = yf.download([ticker, benchmark], start=start.date(), end=end.date(),
                         progress=False, auto_adjust=False)["Close"]
    except Exception:
        return None
    if px is None or len(px) < min_obs or ticker not in px or benchmark not in px:
        return None
    r = np.log(px[[ticker, benchmark]] / px[[ticker, benchmark]].shift(1)).dropna()
    if len(r) < min_obs:
        return None
    var_b = float(r[benchmark].var())
    if var_b <= 0:
        return None
    beta = float(r[ticker].cov(r[benchmark]) / var_b)
    # Sanity clamp: a 1-day-window beta outside [0.2, 3.0] is far more likely a data
    # artifact (splits, thin trading, a bad bar) than a real exposure. Refuse it.
    if not (0.2 <= beta <= 3.0):
        return None
    return round(beta, 3)


def run(only=None, ledger_path=DEFAULT_LEDGER):
    import yfinance as yf
    rows = _read(ledger_path)
    entries = [r for r in rows if r.get("type") == "entry"]
    scored_ids = {r["entry_id"] for r in rows if r.get("type") == "outcome"}

    for e in entries:
        v = e["verdict"]
        if v["action"] not in ("BUY", "SHORT"):
            continue
        if only and e["ticker"] != only:
            continue
        if e["id"] in scored_ids:
            print(f"{e['ticker']:5s} {e['id']}  already scored — skip")
            continue
        ex = v.get("exit") or {}
        entry_d, exit_d, etf = ex.get("entry_close_date"), ex.get("exit_open_date"), ex.get("sector_etf")
        if not (entry_d and exit_d and etf):
            print(f"{e['ticker']:5s} {e['id']}  missing exit spec — skip")
            continue
        try:
            sh = yf.Ticker(e["ticker"]).history(period="1y", auto_adjust=True)
            eh = yf.Ticker(etf).history(period="1y", auto_adjust=True)
            sgap = _gap(sh, entry_d, exit_d)
            egap = _gap(eh, entry_d, exit_d)
            if sgap is None or egap is None:
                print(f"{e['ticker']:5s} {e['id']}  PENDING — {exit_d} open not in data yet")
                continue
            # v1.5.3: estimate beta on a clean pre-event window; fall back to 1 (flagged).
            beta = estimate_beta(e["ticker"], etf, entry_d)
            # same-day CLOSE moves feed the hold-to-close SHADOW (measurement only)
            sclose = _close_move(sh, entry_d, exit_d)
            eclose = _close_move(eh, entry_d, exit_d)
            out = record_outcome(e["id"], stock_open_pct=sgap, etf_open_pct=egap,
                                 stock_close_pct=sclose, etf_close_pct=eclose,
                                 beta=beta, benchmark=etf, classification="NORMAL",
                                 note=f"{v['action']} {v['conviction']}; auto post-mortem",
                                 ledger_path=ledger_path)
            verdict = "CORRECT" if out["idio_sign_correct"] else "WRONG"
            btag = f"b={beta}" if beta is not None else "b=1*"
            print(f"{e['ticker']:5s} {v['action']:5s} {v['conviction']:4s}  "
                  f"stock {sgap:+.1f}%  {etf} {egap:+.1f}%  {btag}  "
                  f"-> idio {out['idio_open_pct']:+.1f}%  [{verdict}]"
                  + (f"   close-shadow {out['idio_close_pct']:+.1f}%"
                     if out.get("idio_close_pct") is not None else ""))
        except Exception as ex_:
            print(f"{e['ticker']:5s} {e['id']}  fetch error: {ex_}")

    print("\n" + render_stats(stats(ledger_path)))


if __name__ == "__main__":
    run(only=sys.argv[1] if len(sys.argv) > 1 else None)
