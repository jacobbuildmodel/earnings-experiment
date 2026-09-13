# DESIGN PROPOSAL — Convexity / Skew Overlay (STRUCTURAL, escalation-tier)

Status: **DESIGN ONLY — not implemented.** Per Self-Correcting Protocol §4B
(adds a new data stream / changes what the architecture optimizes), this is a
USER-ESCALATION item requiring Jacob's explicit build approval. Written at his
request 2026-06-30.

## The gap it addresses
The PRE model scores **direction** (the sign of the idio move). It is blind to
**payoff skew**. Jacob's thesis: a name already −36% YTD at 52-week lows with
washed-out expectations has a *convex* payoff into earnings — downside capped
(priced for disaster), upside open (any real catalyst re-rates it). The DS can
be ~0 (direction a coin flip) while expected value is positive because the
distribution is skewed up. AVAV was the archetype; the model said NO TRADE.

Direction and convexity are **orthogonal**. A complete system wants both:
DS says *which way*; a skew score says *how asymmetric the bet is*.

## What it would measure (diagnostic first — like IRM, never scored initially)
A `skew_score` in [−2, +2], built from deterministic, already-available inputs:
1. **Drawdown depth** — `below_52w_high_pct` (how much bad news is already in).
2. **Expectations washout** — REV sign + magnitude, PT-cut density, price vs
   consensus target (how low the bar is set).
3. **Downside floor proxy** — IRM (implied move / avg gap) and distance to
   52-week low (how much room is left to fall vs to rise).
4. **Catalyst live-ness** — VEL sign (is a real operating inflection present).

Positive skew (convex-up) = deeply drawn down + washed-out expectations +
limited remaining downside + a live KPI. Negative skew (convex-down) = extended
+ euphoric expectations + priced-for-perfection (the C/GS 52-week-high profile).

## How it would interact with the cascade (three options for Jacob to pick)
- **(A) Diagnostic only** — log `skew_score`, never act on it. Zero verdict
  risk; pure measurement. Recommended first step (outcome-equivalent: new
  forward-only field, no existing verdict moves).
- **(B) Tie-breaker** — only when DS is in the NO-TRADE band (|DS|<3), a strong
  positive skew (+2) permits a *small* (≤0.5 unit) convex starter long. Bounded
  risk; explicitly a different book from the directional trades.
- **(C) Size modifier** — skew scales the unit on trades DS already greenlit.
  Most invasive; changes sizing on live signals.

## Guardrails (non-negotiable if built)
- Skew NEVER overrides a hard gate (G0–G4), a CBR block, or the falling-knife
  logic. It is additive optionality, not a bypass.
- Convex longs are capped tiny (≤0.5 unit) and logged as a distinct strategy
  tag so their accuracy/kill-switches are tracked SEPARATELY from directional
  trades (they will have lower hit-rate but positive skew — mixing them would
  corrupt the directional accuracy stat).
- Parameter cost: +2–3 (drawdown, washout, floor). Forces 2–3 ablation
  nominations against the 30 ceiling → this is a real architectural commitment,
  not a tweak.

## Why it is NOT a micro-patch
It changes what the system optimizes (adds an EV/skew objective alongside
directional sign) and adds a data stream. That is exactly the §4B boundary.
Recommended path: build **(A) diagnostic-only** first, accumulate `skew_score`
alongside outcomes for ~15–20 prints, and only then decide whether (B)/(C)
earns its parameters against real evidence.

## Next step
Awaiting Jacob's call: build the diagnostic-only `skew_score` now, or hold as
design until the [W1] inflection override has run its holdouts.
