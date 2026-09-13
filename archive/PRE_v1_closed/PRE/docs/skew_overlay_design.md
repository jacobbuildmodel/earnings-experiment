# STRUCTURAL design — EV/skew overlay & calculated-risk framework

**Tier:** STRUCTURAL. Requires explicit owner approval to build. **Not** in `pre_engine.py`.
This is the design only; nothing here changes a verdict today.

## Why it's structural, not a tweak
The owner's three named archetypes — **comeback**, **sell-the-news**, **AVGO-style in-line-and-plummet** —
are **payoff-skew** bets. On exactly these setups, direction and EV are decorrelated: a sign-only classifier
either abstains ("direction unclear") or fires for the wrong reason (it can't see the payoff). No threshold
move fixes this. It requires (a) a new data stream (options surface + reaction-magnitude history) and (b) a
change to *what the system optimizes* (sign → sign-conditioned-on-skew). Both are the definition of STRUCTURAL.

## Two-stage architecture (sealed core untouched)
1. The sign classifier runs first, exactly as today.
2. A **skew overlay** runs second on *separate* inputs. It may **veto** or (later) **upgrade**. It never
   touches DS, never enables a trade the sealed core refused (except the explicit Stage-3 calculated-risk path,
   which is owner-gated and sizes *down*).

## Sub-scores (∈ {−1,0,+1}) — thresholds are priors to calibrate forward, not discoveries
```
RICH  (vol richness):
  vol_ratio = implied_move / max(realized_vol·√(days/252), avg_abs_open)
  RICH = -1 if vol_ratio ≥ 1.30   # event priced rich → sell-the-news bias
         +1 if vol_ratio ≤ 0.75   # priced cheap → long-vol bias
POS   (positioning):
  POS  = -1 if 25Δ_skew high AND consensus_price_target_upside > +15%
         +1 if 25Δ_skew low  AND price_target_upside < 0%
PAYOFF (asymmetry, needs ≥3 beats & ≥3 misses of magnitude history):
  PAYOFF = +1 if median_up_gap/median_down_gap ≥ 1.8
           -1 if median_down_gap/median_up_gap ≥ 1.8
SKEW = clamp(RICH + POS + PAYOFF, -2, +2)
```

## Staged gating (governance-matched, each stage earns the next on its OWN forward sample)
- **Stage 1 — diagnostic — ✅ BUILT & LIVE (pre_engine.py v1.4.0):** `score_skew()` logs SKEW on every
  decision with **no effect on action, DS, or sizing** (asserted verdict-invariant in `pre_selftest.py` §8).
  Every event without SKEW data is a missed observation of a signal we know we need.
- **Stage 2 — veto only (n≥10 with SKEW logged; conservative → fast-track-eligible):**
  `BUY ∧ SKEW≤−2 → NO_TRADE`; `SHORT ∧ SKEW≥+2 → NO_TRADE`. Directly addresses the AEHR/NKE priced-in misfire.
- **Stage 3 — calculated-risk upgrade (n≥25; owner approval required):**
  on `|DS|∈{1,2}` with SKEW & PAYOFF strongly aligned → `CALCULATED_RISK_BUY/SHORT`.
  **Sizing = 0.5 units, gap-at-risk 0.25% of capital.** A payoff bet is *smaller and more numerous*, not bigger.

## Data required that PRE does NOT ingest
ATM straddle price · 25-delta skew · ATM open interest · 3-month realized vol · consensus price-target upside ·
per-name reaction-**magnitude** history (current REACT stores sign only). Minimum viable subset: **straddle +
25Δ skew + realized vol**. Until these exist, this framework cannot even start Stage 1.

## Companion: defined-risk options (S2)
Long put / long call / put spread / call spread as new actions triggered by the overlay (Stage 3), with
per-Greek exposure logged and P&L scored against defined max-loss. **No short straddles** until n≥50 and the
overlay has proven predictive. Equity-only path stays the default.
