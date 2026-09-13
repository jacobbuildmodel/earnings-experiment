"""
PRE — EXPECTATIONS-BAR DIAGNOSTIC.  **LOGGED ONLY. NEVER SCORES, GATES, OR SIZES.**
================================================================================
Owner directive 2026-07-29: log this, leave the REV/GG/VEL signs alone.

WHY THIS EXISTS
  The mechanism audit could state no mechanism for the current SIGN of the fundamental terms.
  REV / GG / VEL are PUBLIC information and therefore already in the price, so they cannot
  forecast a SURPRISE. The only mechanism they plausibly carry is the opposite of how they are
  coded:

      A raised pre-print bar makes a given print more likely to DISAPPOINT.

  AMKR is the case study — it BEAT Q2 (EPS 0.70 vs 0.49) and gapped -14.5%, because Q3 guidance
  landed ~4% light against a bar that 6 up-revisions had lifted. The model read those revisions
  as a reason to be MORE long, at maximum weight.

  Two weak, independent lines pointed the same way on the 2026-07 ledger (n=17):
      corr(REV, idio) = -0.30    corr(GG, idio) = -0.24    corr(wash, idio) = +0.08
      REV > 0  (bar raised):  mean -2.26%  (n=7)
      REV <= 0 (bar low):     mean +3.46%  (n=10)
  That is NOT enough to act on, and acting on it would be exactly the overfitting this project
  keeps criticising. So: measure it, do not trade it.

DESIGN RULES — deliberately austere, because the last "diagnostic overlay" (skew, 13 params)
became dead weight that was logged forever and never used:
  1. NO new data sourcing. Everything is computed from inputs already frozen at decision time.
  2. NO invented weights and NO thresholds beyond a sign test. Raw observables are logged;
     the one composite is a plain sum of two signs, so there is nothing to tune.
  3. It CANNOT touch a verdict. There is no code path from this module into a decision.
  4. It carries its own FALSIFIER (see BAR_HYPOTHESIS), so the test cannot quietly drift into
     "whatever the data ends up showing".

THE PRE-REGISTERED HYPOTHESIS AND ITS FALSIFIER — fixed now, before the data exists.
"""
from __future__ import annotations

from typing import Optional

__version__ = "1.0.0"

BAR_HYPOTHESIS = {
    "claim": ("A HIGHER pre-print expectations bar predicts a MORE NEGATIVE idiosyncratic "
              "open gap, because the print must clear a bar that revisions and/or a price "
              "run-up have already lifted."),
    "predicts": "corr(bar, idio_open_pct) < 0",
    "confirm_if": ("n >= 30 scored events AND mean(idio | bar>0) < mean(idio | bar<0) "
                   "AND the sign is stable when the sample is split by date."),
    "refute_if": ("n >= 30 AND the separation is absent or reversed. On refutation the "
                  "current REV/GG/VEL signs are VINDICATED and this module is deleted."),
    "acts_on_verdicts": False,
    "note": ("Until n >= 30 this is a measurement, not a finding. Do NOT flip, cut, or reweight "
             "any component on it. If the bar is confirmed, the change it licenses is a SIGN "
             "change on the fundamental terms — decided by the owner, not applied automatically."),
}


def _sign(x) -> int:
    return 1 if x > 0 else (-1 if x < 0 else 0)


def expectations_bar(j, m, components: Optional[dict] = None,
                     backfilled: bool = False) -> dict:
    """Compute the diagnostic from ALREADY-FROZEN decision-time inputs.

    Returns a flat dict for the ledger. Two independent observables plus their sign-sum:

      rev_balance  — (up - down) / covering_analysts over 30d. How far analysts have moved
                     the bar. This is the RAW ratio, not the bucketed REV score.
      rev_recent   — (up_7d - down_7d). Whether the bar moved RECENTLY, i.e. late enough that
                     the print must clear a freshly-raised number.
      price_run    — stock % since last print MINUS its sector over the same window. The
                     price-side bar: a name that has already run has priced in good news.
      priced_move  — IRM (implied / avg gap). Logged for context only: it sizes the expected
                     move, it says nothing about direction (see the `value` post-mortem).

      bar          — sign(rev_balance) + sign(price_run), in [-2, +2]. A plain sum of two
                     signs: no weights, no thresholds, nothing tunable. THIS is the number the
                     hypothesis is about.

    Any observable that is unavailable is None and is simply excluded from `bar` — the
    diagnostic never fabricates a reading.
    """
    up, dn, cov = j.up_revisions_30d, j.down_revisions_30d, j.covering_analysts
    rev_balance = ((up - dn) / cov) if (cov and up is not None and dn is not None) else None

    u7, d7 = j.up_revisions_7d, j.down_revisions_7d
    rev_recent = (u7 - (d7 or 0)) if u7 is not None else None

    price_run = None
    if (j.stock_pct_since_last_earnings is not None
            and j.sector_etf_pct_same_window is not None):
        price_run = j.stock_pct_since_last_earnings - j.sector_etf_pct_same_window

    priced_move = None
    if m.implied_move and m.avg_abs_open:
        priced_move = round(m.implied_move / m.avg_abs_open, 3)

    parts = [_sign(x) for x in (rev_balance, price_run) if x is not None]
    bar = sum(parts) if parts else None

    return {
        "diagnostic": "expectations_bar",
        "version": __version__,
        "acts_on_verdicts": False,
        "backfilled": backfilled,
        "rev_balance": round(rev_balance, 4) if rev_balance is not None else None,
        "rev_recent": rev_recent,
        "price_run": round(price_run, 2) if price_run is not None else None,
        "priced_move": priced_move,
        "bar": bar,
        "bar_inputs_available": len(parts),
    }


# --------------------------------------------------------------------------- report
def report(ledger_path=None):
    """Score the hypothesis against everything logged so far. Read-only."""
    from pre_ledger import _read, DEFAULT_LEDGER
    import statistics as st
    path = ledger_path or DEFAULT_LEDGER
    rows = _read(path)
    entries = [r for r in rows if r.get("type") == "entry"]
    by_id = {e["id"]: e for e in entries}
    pairs = []
    for r in rows:
        if r.get("type") != "outcome":
            continue
        e = by_id.get(r["entry_id"])
        if not e:
            continue
        eb = (e.get("verdict") or {}).get("expectations_bar")
        if eb and eb.get("bar") is not None:
            pairs.append((e["ticker"], eb["bar"], r["idio_open_pct"], bool(eb.get("backfilled"))))
    fwd = [p for p in pairs if not p[3]]
    back = [p for p in pairs if p[3]]
    L = ["EXPECTATIONS-BAR DIAGNOSTIC — logged only, never traded",
         f"  hypothesis: {BAR_HYPOTHESIS['predicts']}",
         f"  FORWARD n = {len(fwd)} / 30   (only these count — see below)",
         f"  backfilled n = {len(back)}  — CANNOT be evidence: this hypothesis was derived",
         "     from those same outcomes. Shown for shape only, never for confirmation."]
    if pairs:
        hi = [x for _, b, x, _ in pairs if b > 0]
        lo = [x for _, b, x, _ in pairs if b < 0]
        flat = [x for _, b, x, _ in pairs if b == 0]
        for lbl, g in (("bar RAISED (>0)", hi), ("bar NEUTRAL (0)", flat), ("bar LOW (<0)", lo)):
            if g:
                L.append(f"    {lbl:18s} n={len(g):2d}  mean {st.mean(g):+6.2f}%  "
                         f"median {st.median(g):+6.2f}%")
        if hi and lo:
            direction = "CONSISTENT with" if st.mean(hi) < st.mean(lo) else "AGAINST"
            L.append(f"  separation is {direction} the hypothesis "
                     f"(needs n>=30 and a date-split check before it counts)")
    L.append("  REMINDER: this changes no verdict, no size, no threshold. Measurement only.")
    return "\n".join(L)


if __name__ == "__main__":
    print(report())
