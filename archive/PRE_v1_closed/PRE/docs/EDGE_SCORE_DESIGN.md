# TIER 2 DESIGN — EDGE SCORE + SIZING
**Status: LIVE — `pre_edgescore.py` v1.0.0 is the PRODUCTION scorer (owner-wired 2026-07-29).**
`pre_calcrisk.calc_risk` is demoted to a logged SHADOW cross-check on every decision.
Date 2026-07-29. Replaces GenSpark's §2a formula, which does not work as written.

> ## ⚠️ BACKTEST RESULT — READ FIRST, IT CHANGED THE DESIGN
> Replayed on all 30 frozen ledger entries (17 with outcomes):
> * **Abstention 88% → 56%.** 3 live bets → 11. The over-conservatism complaint is FIXED.
> * **Tiers are reachable** (MAXIMUM 1 / HIGH 3 / STANDARD 2 / EXPLORATORY 5) — unlike
>   GenSpark's multiplicative form, whose top tiers were mathematically unreachable.
> * **BUT conviction rank-ordered returns PERFECTLY INVERSELY:**
>   MAXIMUM −10.15% · HIGH −2.23% · STANDARD +2.20% · EXPLORATORY +1.27%.
> * Tiered sizing lost **$388.89**; flat sizing lost **$91.98** on the *same 8 trades*.
>   The entire difference: the ladder put its biggest bet (1.5%) on AMKR, the worst trade.
>
> **Consequence: §3.4's risk ladder is COMPUTED AND LOGGED BUT DOES NOT SIZE.**
> `SIZE_BY_CONVICTION = False`; flat 0.50% until tier returns rank-order at n≥20/tier.
> Owner directive: **no portfolio caps** — §4 is retained as rationale only, not enforced.

---

## 1. THE PROBLEM THIS SOLVES (the one thing worth fixing)

Jacob's complaint — *"the model is too conservative, everything is NO_TRADE"* — has a precise
cause, and the review named it correctly:

> **The model conflates "I have no edge" with "I am uncertain." They are different states.**

Today, any UNAVAILABLE input widens the worst-case band, the band straddles the threshold, and
the trade dies. That is a **maximin** rule — optimise the worst case — which is right when a
wrong bet is catastrophic and irreversible. On an $18k book with position sizes in the low
hundreds, it is the wrong rule. The cost of never betting is higher than the cost of a small
wrong bet.

**Fix: uncertainty should shrink the position, not kill it.**

---

## 2. WHY GENSPARK'S FORMULA CANNOT BE USED

It proposed `edge = signal × completeness × asymmetry` with tiers at 0.25 / 0.50 / 0.70.
Three fatal defects:

| Defect | Consequence |
|---|---|
| **Multiplicative** — three sub-1.0 numbers | To reach 0.70 you need ~0.9×0.9×0.87. **The top two tiers are unreachable.** Everything collapses into the bottom tier. |
| **`asymmetry = 0` zeroes the product** | A screaming fundamental long with *fairly priced* vol scores **zero edge**. That is MORE restrictive than today — the opposite of the goal. |
| **`asymmetry = max(0, cheapness)`** | Cannot express a short, where you want vol **rich**, not cheap. Underspecified. |

The *principle* is right. The formula is not implementable. Here is one that is.

---

## 3. THE DESIGN

### 3.1 Three independent edge sources, scored in the same units

Each returns a signed score in **[−1, +1]**, where the sign is the direction it argues for.
They are **independent** — that is deliberate, so they can be summed, not multiplied.

**A. DIRECTIONAL EDGE** — the fundamental read (what the model already computes)
```
directional = clamp( sector_weighted(REV + GG + VEL + SAT + FLAG) / 6.0 , -1, +1 )
```
Uses the existing components. `/6.0` normalises the realistic DS range. Sector weights (§5)
multiply the individual components before summing.

**B. VALUE EDGE** — is the event mispriced *relative to this name's own history*
```
value = clamp( (1.0 - IRM) / 0.45 , -1, +1 )        # IRM = implied_move / avg_abs_open
```
IRM 0.55 → +1.0 (very cheap). IRM 1.00 → 0.0 (fair). IRM 1.45 → −1.0 (very rich).
**Signed, so it serves both sides:** positive value favours longs *and* straddles; negative
value is what a sell-the-news short needs. This is what fixes GenSpark's short-blindness.

**C. POSITIONING EDGE** — is the downside already used up (or the upside exhausted)
```
positioning = 0.6*wash + 0.4*vrich_sign          # wash ∈ {-1,0,+1}, vrich ∈ {-1,0,+1}
```

### 3.2 Combine — ADDITIVE with a completeness multiplier

```
raw_edge      = 0.50*directional + 0.30*value + 0.20*positioning      # ∈ [-1, +1]
completeness  = verified_inputs / total_inputs                         # ∈ [0, 1]
confidence    = 0.55 + 0.45*completeness                               # ∈ [0.55, 1.0]   <-- KEY
edge_score    = raw_edge * confidence                                  # ∈ [-1, +1]
```

**The `confidence` floor of 0.55 is the whole design.** Missing inputs shrink the bet by at
most 45% — they never zero it. A strong read on half-known information still trades, at
roughly half size. That is precisely the "uncertain → smaller, not abstain" conversion.

Weights 0.50 / 0.30 / 0.20 are **priors**, not discoveries. They say: fundamentals matter most,
mispricing second, positioning least. Frozen until there is evidence.

### 3.3 Verdict

```
if hard_gate_fail:                      NO_TRADE     # G0/G1/G4 stay binary — these are safety
elif |edge_score| < 0.08:               NO_TRADE     # genuinely no read
elif edge_score >= +0.08:               BUY
elif edge_score <= -0.08 and short_ok:  SHORT
```
where `short_ok = (value < 0) and (positioning <= 0)` — a short still needs the event to be
**richly priced** and the name **not beaten down**. This preserves the v1.3.0 short hurdle:
shorts fight the announcement premium, so they need more than a negative fundamental read.

### 3.4 Conviction and size — the answer to "how do I risk more when I have a reason"

| Tier | `|edge_score|` | Risk budget | Reachable? |
|---|---|---|---|
| **EXPLORATORY** | 0.08 – 0.20 | **0.25%** | very often — *this replaces most current NO_TRADEs* |
| **STANDARD** | 0.20 – 0.35 | **0.60%** | often |
| **HIGH** | 0.35 – 0.55 | **1.00%** | several per quarter |
| **MAXIMUM** | > 0.55 | **1.50%** | rare, a few per year |

**Reachability check (the thing GenSpark got wrong).** A strong-but-not-perfect setup:
directional 0.60, value +0.40, positioning +0.60, completeness 0.75 →
`raw = 0.50(0.60)+0.30(0.40)+0.20(0.60) = 0.54`; `confidence = 0.55+0.45(0.75) = 0.8875`;
**edge = 0.479 → HIGH.** Reachable. A perfect setup lands ~0.75 → MAXIMUM. The tiers work.

Current model: flat 0.5% or nothing. New: **0.25% → 1.50%, a 6× dynamic range** — small money
on thin reads, real money on strong ones. That is the calculated-risk posture you asked for.

### 3.5 Dampers demote, they do not halve
Macro overlap / vol-hot / g2_estimated / fragile / contradicting-richness each drop conviction
**one tier** (not ×0.5 on size). Two dampers = two tiers. This is gentler and more legible.

---

## 4. THE PORTFOLIO CAP — RAISED, DECLINED BY OWNER (2026-07-29), NOT IMPLEMENTED
> Owner ruling: *"no caps. just take the verdict and action as it is. i will do my own risk
> management."* Recorded and respected — verdicts and sizes emit unmodified. The rationale
> below is kept only so the exposure is documented, not because it is enforced.

### (original rationale, not implemented)

**GenSpark's framework has no portfolio-level constraint. Shipping it as written would be
dangerous here**, because it raises per-trade size *and* trade frequency at the same time on a
book whose names all report on the same night and sit in the same sector.

Concrete: on 2026-07-28, six names printed together and **SMH itself gapped −3.25%**. A basket
of semi longs loses together — that is one bet, not six.

```
CAP 1 — per-night      : total gap-at-risk across all positions <= 4.0% of capital
CAP 2 — per-sector     : total gap-at-risk in one sector ETF     <= 2.5% of capital
CAP 3 — per-name       : as per conviction tier (max 1.5%)
If a new trade breaches a cap: size down to fit. If it cannot fit, take the HIGHEST edge_score
and drop the rest. Log every crowd-out.
```

Without this, a "high-conviction semis night" is a 9% single-night drawdown risk on correlated
names. With it, worst case is bounded at ~4%.

---

## 5. SECTOR WEIGHTS (adopted as priors, honestly counted)

Multipliers on components **before** summing into `directional`. Clamped [0.3, 2.0].

| Factor | Semis/Semi-cap | Pharma/Biotech | Fintech/Pmts | Software/SaaS | Industrials | Energy |
|---|---|---|---|---|---|---|
| REV | 0.8 | 0.5 | 1.0 | 1.3 | 0.8 | 0.4 |
| GG | 1.2 | 0.8 | 1.5 | 1.5 | 1.0 | 0.6 |
| VEL | **2.0** | 0.5 | 1.0 | 1.5 | 0.8 | 0.5 |
| SAT | 0.8 | 0.5 | 1.0 | 1.0 | 1.0 | 0.8 |

Rationale is economic, not fitted: semis lead on bookings (VEL 2.0 — this already matches our
own C12 doctrine); SaaS lives and dies on the guide and growth deceleration; pharma prints are
mostly non-events versus trial readouts; energy is a commodity echo.

**Honest accounting:** this is **24 new numbers**. They are unvalidated priors, they are frozen,
and they count against the parameter budget — I will not pretend they are free. If they cannot
be validated, they should be flattened rather than quietly kept.

---

## 6. WHAT THIS CHANGES ON REAL DATA (must run before sign-off)

Backtest-of-decision (not of P&L) on all 30 logged entries: how many NO_TRADEs become live
bets, at what tier, and what would they have returned. **If this converts most of the 07-28
batch into EXPLORATORY longs, it would have LOST money that night** (7 of 11 closed red). That
is the key risk and it must be quantified before this ships, not after.

---

## 7. WHAT I AM *NOT* PROPOSING
- **No straddle pivot.** On our own data, cheap-IRM straddles went 0-for-3 on the gap at the
  price you can actually pay (−22.6 pts of premium). Needs a real feasibility study with live
  quotes and spreads first.
- **No exit change.** Gap-capture stays; Jacob ruled on this. The close shadow keeps accruing.
- **No Bayesian auto-revision yet.** The n-thresholds are unreachable at this trade rate, and
  hit-rate is the wrong objective for fat-tailed gaps — it should be expected return. Needs its
  own design pass.

---

## 8. SIGN-OFF CHECKLIST
- [ ] Owner approves the additive form + 0.55 confidence floor
- [ ] Owner approves the 0.25%–1.50% risk ladder (6× range, up from flat 0.5%)
- [ ] **Owner approves the portfolio caps (4% night / 2.5% sector)** — the safety rail
- [ ] Owner approves sector weights as frozen priors (+24 params, declared)
- [ ] Decision-backtest on the 30 logged entries reviewed **before** go-live
