"""
PRE — IMPLIED MOVE: derivation, decontamination, and PROVENANCE.
================================================================================
Built 2026-07-29 to close the gap external review #2 found: `implied_move` was the
LEAST-verified input in the system while carrying real decision weight. It had
  * no function anywhere in the codebase (the decontamination existed only as a PROSE
    COMMENT in one dated run script),
  * no C1 bound,
  * no cross-source reconciliation,
  * no record of whether a stored number was raw or adjusted, from which expiry, or on
    what vol estimate,
and it was hand-entered as a bare float. Two contradictions were sitting in the ledger:
  ASML  2026-07-15 : implied_move 6.30 in one entry, 8.36 in another, same event
  NVTS  2026-07-28 : implied_move 5.70 stored, while the transactable straddle was 16.70

THE DECONTAMINATION AND WHY IT WAS WRONG
  No listed expiry sits on the event, so a straddle bought to capture a print also pays for
  N extra days of ordinary vol. The intended correction was
      event_IM = sqrt(IM_raw^2 - daily_var * n_extra_days)
  My first diagnosis was that trailing realized vol is inflated by past earnings gaps, so the
  correction over-subtracts. **That diagnosis was wrong** — measured on NVTS, realized vol
  EXCLUDING earnings days is HIGHER (149%) than including them (145%). The name is simply
  volatile all the time.

  The actual defect is blunter: **the correction was consuming the answer.** On NVTS it removed
  89% of the straddle's variance, leaving 11% and calling the residual a measurement. Trailing
  realized vol is a poor forecast of forward vol (vol mean-reverts hard after a spike), so
  subtracting three days at a spiked rate can wipe out most of a straddle that the market is
  actually charging 16.70% for. Declaring that event "screamingly cheap" (IRM 0.47) was an
  artifact of the adjustment, not a reading of the market.

THE RULE THIS MODULE ENFORCES
      An estimate whose correction is larger than its result is not a measurement.
  If decontamination removes more than DECONTAM_MAX_VAR_FRACTION of the variance, it FAILS
  CLOSED and returns None — the same fail-closed doctrine used everywhere else for a missing
  input. A fabricated small number is worse than no number.

This module MAY fetch (it is a caller-side helper, like pre_postmortem.estimate_beta).
The engine still never fetches.
"""
from __future__ import annotations

import math
from typing import Optional

__version__ = "1.0.0"

# If the decontamination removes more than this fraction of the straddle's VARIANCE, the
# residual is dominated by the assumption rather than by the market price. Refuse it.
DECONTAM_MAX_VAR_FRACTION = 0.50

# C1-style hard bounds. A single-name earnings straddle outside this range is a data error.
IM_MIN, IM_MAX = 0.10, 60.0


def decontaminate(im_raw: float, realized_vol_annual: float, extra_trading_days: int,
                  trading_days_per_year: int = 252) -> dict:
    """Strip N days of ordinary vol from a straddle that expires AFTER the event.

    Returns a provenance dict. `implied_move` is None whenever the correction cannot be
    trusted — callers must then treat IM as UNAVAILABLE rather than substituting a guess.
    """
    out = {
        "implied_move": None,
        "implied_move_raw": round(im_raw, 3),
        "implied_move_basis": None,
        "realized_vol_annual": realized_vol_annual,
        "extra_trading_days": extra_trading_days,
        "variance_removed_pct": None,
        "refused_reason": None,
    }
    if im_raw is None or im_raw <= 0:
        out["refused_reason"] = "no raw straddle"
        return out
    if not extra_trading_days:                      # expiry sits ON the event: nothing to strip
        out["implied_move"] = round(im_raw, 3)
        out["implied_move_basis"] = "RAW"
        out["variance_removed_pct"] = 0.0
        return out
    if not realized_vol_annual or realized_vol_annual <= 0:
        out["refused_reason"] = "no realized-vol estimate; cannot decontaminate"
        return out

    daily_var = (realized_vol_annual / math.sqrt(trading_days_per_year)) ** 2
    removed = daily_var * extra_trading_days
    total = im_raw ** 2
    frac = removed / total
    out["variance_removed_pct"] = round(frac * 100, 1)

    if frac > DECONTAM_MAX_VAR_FRACTION:
        out["refused_reason"] = (
            f"correction would remove {frac*100:.0f}% of the straddle's variance "
            f"(> {DECONTAM_MAX_VAR_FRACTION*100:.0f}%): the adjustment exceeds the answer, "
            f"so the residual is an assumption, not a measurement. FAIL CLOSED.")
        return out

    out["implied_move"] = round(math.sqrt(total - removed), 3)
    out["implied_move_basis"] = "DECONTAMINATED"
    return out


def sanity(im: Optional[float], raw: Optional[float], basis: Optional[str]) -> list:
    """C1-style bounds for implied move + its provenance. Returns FATAL errors only.

    SCOPE NOTE — this was initially written to make an UNDECLARED basis fatal, which broke
    every existing caller at once. That was wrong, and the distinction matters:
      * fail-closed applies to MISSING DATA that would change a decision;
      * it does NOT apply to missing METADATA about data that is present and in range.
    An undeclared basis is a provenance gap -> WARNING (raised by the engine), not fatal.
    Only self-CONTRADICTORY provenance is fatal, because such a row cannot be audited at all.
    """
    e = []
    if im is None:
        return e
    if not (IM_MIN <= im <= IM_MAX):
        e.append(f"C1: implied_move {im} outside [{IM_MIN}, {IM_MAX}]")
    if basis == "DECONTAMINATED":
        if raw is None:
            e.append("C1: DECONTAMINATED implied_move stored with no raw — unauditable")
        elif im > raw + 1e-9:
            e.append(f"C1: decontaminated implied_move {im} exceeds its raw {raw}")
    return e


def provenance_warning(im: Optional[float], basis: Optional[str]) -> Optional[str]:
    """Non-fatal: a usable implied move whose origin was never declared."""
    if im is not None and basis is None:
        return ("implied_move has no declared basis (RAW|DECONTAMINATED) — usable but "
                "UNAUDITABLE; the ASML 6.30-vs-8.36 conflict is exactly this failure")
    return None


# ------------------------------------------------------------------ derivation (fetches)
def straddle_implied_move(ticker: str, event_date: str, asof: Optional[str] = None) -> dict:
    """Read the nearest post-event ATM straddle and return raw IM + full provenance.

    Uses put-call parity to strip intrinsic value off an off-ATM strike (time value / spot),
    which is what an implied move IS. This READS quoted prices — there is no option-pricing
    model here and none is implied.
    """
    import numpy as np, yfinance as yf
    out = {"ticker": ticker, "event_date": event_date, "implied_move_raw": None,
           "expiry": None, "extra_trading_days": None, "strike": None,
           "near_money_oi": None, "source": "yfinance ATM straddle mid, parity-adjusted"}
    tk = yf.Ticker(ticker)
    try:
        spot = float(tk.history(period="1d")["Close"].iloc[-1])
        exps = [x for x in tk.options if x >= event_date]
        if not exps:
            out["refused_reason"] = "no listed expiry on/after the event"
            return out
        ex = exps[0]
        ch = tk.option_chain(ex)
        c, p = ch.calls, ch.puts
        common = sorted(set(c.strike) & set(p.strike), key=lambda x: abs(x - spot))
        if not common:
            out["refused_reason"] = "no strike quoted on both sides"
            return out
        k = common[0]

        def mid(df):
            r = df[df.strike == k].iloc[0]
            b, a = float(r.bid), float(r.ask)
            return (b + a) / 2 if (b > 0 and a > 0) else float(r.lastPrice)
        tv = mid(c) + mid(p) - abs(spot - k)        # time value = straddle - intrinsic
        out["implied_move_raw"] = round(tv / spot * 100, 3)
        out["expiry"] = ex
        out["strike"] = k
        out["strike_offset_pct"] = round(abs(k - spot) / spot * 100, 2)
        out["extra_trading_days"] = int(np.busday_count(event_date, ex))
        near = lambda df: float(df[(df.strike > spot * .85) & (df.strike < spot * 1.15)]
                                .openInterest.sum())
        out["near_money_oi"] = {"calls": near(c), "puts": near(p)}
    except Exception as e:
        out["refused_reason"] = f"fetch error: {e!r}"[:160]
    return out
