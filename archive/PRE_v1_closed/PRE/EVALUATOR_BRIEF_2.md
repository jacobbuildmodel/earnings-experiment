# PRE / CATALYST — INDEPENDENT EVALUATION #2
### For a fresh third-party AI reviewer. Paste this entire document. No prior context needed.

---

# PART A — WHAT I NEED FROM YOU (read this first)

You are an independent adversarial reviewer of a pre-earnings trading model. You did not build
it. The model's author is an AI that **built it, grades it, and just rewrote it** — a structural
conflict I am deliberately trying to break. This is the **second** external review; the first
(by a different system) is summarised in §11 so you can see what was already challenged and what
changed as a result.

> ### ⚠️ A WARNING ABOUT YOU SPECIFICALLY
> You are very likely the **same model family as the author** (Claude/Opus). That makes you
> excellent at checking their arithmetic and code — and **weak at attacking their premises**,
> because you share their priors and will find their reasoning persuasive for the same reasons
> they do. **Actively compensate.** When their argument feels obviously right, that is exactly
> the moment to slow down and ask whether you are agreeing because it is true or because you
> would have written the same thing.

## A1 — THE PRIMARY QUESTION (spend most of your effort here)

The model just made a significant self-directed change. I need to know if it is legitimate or
if it is the exact pathology it claims to have cured.

**The situation.** The model produced a "conviction" score (how strong its read is) and a
sizing ladder that bets more on higher conviction. A decision-backtest over 8 scored trades
showed conviction rank-ordering returns **perfectly inversely**:

| Conviction tier | avg return | n |
|---|---|---|
| MAXIMUM | **−10.15%** | 1 |
| HIGH | −2.23% | 3 |
| STANDARD | **+2.20%** | 2 |
| EXPLORATORY | +1.27% | 2 |

**The response.** The author turned conviction-based sizing OFF (`SIZE_BY_CONVICTION = False`),
kept the tier as a logged diagnostic, and switched to flat sizing scaled only by *information
completeness*. Rationale given: "sizing risk by a signal with no demonstrated rank-ordering is
unjustified."

**Q1. Is that a legitimate root-cause fix, or is it symptom-patching on a single vivid loss?**
Note that the MAXIMUM tier has **n = 1** — one trade (AMKR, −10.15%) drives the entire top of
that table. The author's own binding SOP (§9) forbids patching on Type-D/random outcomes and
requires an "Abstraction Test." The author claims the fix passes it. **Check that claim
adversarially.** Specifically:
- Is n = 8 (with n = 1 in the deciding tier) sufficient to justify *any* structural change?
- Is "conviction is inverted" distinguishable from "we had one big loser that happened to score
  high"? What would distinguish them, and can it be tested with what exists?
- Is the CONVICTION (edge magnitude) vs CONFIDENCE (information completeness) distinction the
  author drew a real one, or a post-hoc rationalisation that lets them keep half the design?
- Was the honest response instead: *change nothing, keep accruing evidence*?

## A2 — THE SECOND QUESTION (premise-level; do not skip)

**Q2. The model's strongest-possible directional signal produced its worst loss.**

AMKR scored a **maxed-out fundamental read** — REV +2, GG +1, VEL +1, SAT +2 = 6/6, the
saturation point of the directional scale. Every input the model can see said "strong long."
It gapped **−10.15%** because the earnings release itself guided next-quarter revenue ~4% below
consensus. The deciding variable did not exist in the pre-print observation space.

Neither the first reviewer nor the author has an answer to this. It is not a tuning problem.

- Does a **directional** pre-print model have any recoverable edge, given the dominant price
  driver (forward guidance) is unobservable beforehand?
- If the answer is no: what is the correct object to bet on instead? (The first reviewer said
  "buy straddles." The author tested that on this model's own data and it lost — see §12.3.
  **Do not simply repeat that recommendation; engage with why it failed here.**)
- If the answer is yes: what observable pre-print signal is being missed?

## A3 — THE BROAD SWEEP (this is why you are getting the whole document)

**Q3. Read the entire framework below — architecture, inputs, scoring, gates, decision logic,
sizing, sourcing, verification, the ledger, the learning loop, the code — and tell me what is
wrong with it that NEITHER the first reviewer NOR the author has noticed.**

I want fresh eyes on the whole structure, not just the narrow question. If it broadly makes
sense, say so plainly and I will stop second-guessing it. If there are errors, structural
weaknesses, unexamined assumptions, or better approaches anywhere in the chain — from how data
is sourced, to how correctness is verified, to how decisions are logged and learned from — that
is exactly what I need. Prior reviews have focused on the decision logic; **less attention has
gone to the data layer, the verification layer, and the learning loop.**

## A4 — WHAT NOT TO DO

Do **not** produce another full redesign. The first review proposed one; implementing pieces of
it consumed a week and produced a model whose merit is still unproven. Another ground-up
redesign creates churn, not progress. **Diagnose precisely, then recommend the minimum change
that addresses the diagnosis.** If the right answer is "stop changing things and collect data,"
that is a legitimate and welcome answer.

---

# PART B — FULL CONTEXT

## 1. THE OPERATOR AND MANDATE

- Singapore-based active retail investor. **No coding background** — an AI does all technical
  work from plain-English direction.
- **Real capital ~US$18,000** across three accounts (~10k/5k/3k).
- **A calculated high-risk taker.** His words: *"If there is a logical reason to buy it, I'll buy
  it. I don't mind risking a lot on a read I've reasoned through. I calculate the risk — a
  logical risk — and then I take it."*
- **Standing directives (do not recommend reversing these; they are decided):**
  - **No portfolio-level caps.** He does his own position/risk management. The model emits
    verdicts and sizes unmodified. (Concentration risk was raised once and declined.)
  - **Exit stays gap-capture** (see §2). A hold-to-close alternative was proposed and rejected;
    it is instrumented as a shadow measurement only.
- **His original complaint, which drove the latest rewrite:** the model returned NO_TRADE on
  almost everything — batches of 6–12 names yielding one trade or none. Useless to him.

## 2. WHAT THE MODEL DOES

Captures the price reaction to a single stock's earnings print.

- **Trade mechanic (fixed):** enter the last session **before** the print, exit the **first
  market open after** it. Pure overnight gap capture. AMC print day D → enter D close, exit D+1
  open. BMO print day D → enter D−1 close, exit D open. **Holding period ≈ 18 hours.**
- **Output: exactly three verdicts — BUY / SHORT / NO_TRADE** + conviction + size.

## 3. ARCHITECTURE — THREE STACKED LAYERS (as of 2026-07-29)

```
pre_engine.py    v1.5.3  — sealed sign engine: components -> Decision Score (DS) -> cascade.
                            Owns all hard gates and protections.
        |
pre_calcrisk.py  v1.3.0  — payoff-asymmetry layer. WAS the production scorer;
                            NOW DEMOTED TO A LOGGED SHADOW (still runs, never decides).
        |
pre_edgescore.py v1.0.0  — continuous edge score. **THIS IS NOW THE LIVE SCORER.**
```

**Founding principle (challenge it):**
> The engine **never fetches and never guesses.** All raw judgment values are supplied by the
> caller (the AI reasoning layer). A missing input scores 0 and is flagged UNAVAILABLE. Gates
> fail closed.

**Prime directive: anti-overfitting.** n ≈ 8 real trades. Thresholds are frozen by doctrine.
Nothing is validated.

## 4. INPUTS (all caller-supplied)

**Judgment (the fundamental read):**

| Input | Meaning | Range |
|---|---|---|
| REV | analyst revisions: (up − down) / covering analysts, 30d | −2…+2 |
| GG | guidance / growth direction | −1, 0, +1 |
| VEL | forward trajectory velocity. For **order-driven** names must come from bookings/backlog/orders/guidance, NOT trailing revenue (trailing revenue *inverts* on ramping names) | −1, 0, +1 |
| REACT | post-print reaction — confirmation only, not in DS | −1, 0, +1 |
| FLAG | penalty, subtract-only | −2…0 |
| CBR | earnings quality CLEAN/MANUFACTURED — blocks longs if manufactured | flag |
| SAT | saturation / 52-week position — the "falling-knife guard" | −2…+2 (derived) |

**Provenance fields** (drive verification gates): `order_driven`, `vel_basis`, `gg_basis`,
`rev_basis`, `up_revisions_7d`, `down_revisions_7d`, `guidance_fresh`, per-input `confidence`.

**Market (price-derived, from Yahoo Finance):** `price`, `avg_abs_open` (mean |earnings-day open
gap| over last ~10 confirmed prints), `confirmed_quarters`, `dollar_vol_20d`, `share_vol_20d`,
`implied_move` (ATM straddle, decontaminated — §8), `capital`, `vix`, borrow, `g2_estimated`.

**Skew/positioning (diagnostic, never gates):** `realized_vol_3m`, `days_to_event`, `skew_25d`,
`consensus_pt_upside`, median up/down gaps, `short_interest_pct_float`, `days_to_cover`,
`put_call_oi_ratio`.

## 5. THE SIGN ENGINE (layer 1)

`DS = REV + GG + VEL + SAT + REACT + FLAG`. BUY if DS ≥ +3, SHORT if ≤ −3.
Conviction HIGH if |DS| ≥ 5, MEDIUM if ≥ 3.

**Worst-case band (important — this is the historical abstention engine):** every UNAVAILABLE
input is swung across its full range to produce `DS_floor`/`DS_ceil`. If the band straddles the
threshold, the verdict downgrades to INCOMPLETE → effectively NO_TRADE. **This is a maximin
rule** and was the single largest source of over-abstention.

**Hard gates (fail closed, still binary in all layers):**
- G0 timing: must be T−1 or it is a DRY_RUN (screen only)
- G1 liquidity: $-vol ≥ $25M and our size ≤ 1% of ADV
- G2 gap history: avg gap ≥ 2% and ≥ 4 confirmed quarters
- G3 macro overlap → sizing damper; G4 borrow: shorts need locate, fee ≤ 5%

**Parameter registry (23 scoring params, ceiling 30, all HAND-SET, no ML anywhere):**
```
REV_STRONG .30  REV_MILD .10  REV_MILD_NEG -.10  REV_STRONG_NEG -.30
SAT_SATURATION 20  SAT_VACUUM -10  SAT_52W_NEAR 5  SAT_52W_FAR 25
VEL_UP_BPS 400  VEL_DN_BPS -400
T_BUY +3  T_SHORT -3  HIGH_CUT 5
G1_DOLLAR_VOL_MIN 25M  G1_ADV_FRAC_MAX 1%  G2_GAP_MIN 2%  G2_MIN_QTRS 4  G4_FEE_MAX 5%
VIX_HOT 28  SPY_RV_WOW_HOT 50  SPX_DAY_HOT 1.5  DAMPER_MULT 0.5
RISK_BUDGET 0.5%  HIGH_UNITS 1.5x  ALIGN_MIN 3
```

## 6. THE CALC-RISK LAYER (layer 2 — NOW A SHADOW)

Five reads: **IRM/RICH** (`implied_move / avg_abs_open` — gap-space richness), **VRICH**
(event-implied vol ÷ realized vol — vol-space richness), **WASH** (idio drawdown: excess vs
sector ≤ −15 AND ≥ 20% off high → +1; extended ≥ +15 → −1), **FUND** (`sign(REV+GG+VEL)`,
DEFINED only if ≥2 legs VERIFIED), **DIR** (`sign(DS)`, contradiction flag only).

Decision tree:
```
gate fail                                  -> NO_TRADE
washed + FUND defined + fund < 0           -> NO_TRADE / TRAP
washed + FUND undefined                    -> NO_TRADE
washed + fund >= 0                         -> BUY
rich(-1) + EXTENDED (wash == -1)           -> SHORT   (hurdle raised 2026-07-29, see §11)
else                                       -> NO_TRADE
```
Still computed on every decision and logged as `shadow_calcrisk`, so the demoted scorer's
counterfactual keeps accruing. **It no longer decides anything.**

## 7. THE EDGE SCORE (layer 3 — **THE LIVE SCORER**, v1.0.0)

### 7.1 Why it exists
It was built to fix the over-abstention. The diagnosis (from review #1, accepted): *the model
conflates "I have no edge" with "I am uncertain."* Fix: **uncertainty shrinks the position
rather than killing it.**

### 7.2 The formula as implemented
```python
# three independent, signed edge sources in [-1, +1]
directional = clamp(sector_weighted(REV + GG + VEL + SAT + FLAG) / 6.0, -1, 1)
value       = clamp((1.0 - IRM) / 0.45, -1, 1)          # signed: serves longs AND shorts
positioning = 0.6*wash + 0.4*vrich_sign

raw_edge    = 0.50*directional + 0.30*value + 0.20*positioning
completeness= verified_slots / 5          # slots: REV, GG, VEL, SAT, IRM
confidence  = 0.55 + 0.45*completeness    # <-- FLOOR of 0.55 is the core of the design
edge_score  = raw_edge * confidence
```

### 7.3 Verdict
```python
if hard_gate_fail:                          NO_TRADE
elif abs(edge_score) < 0.08:                NO_TRADE      # dead-band: genuinely no read
elif edge_score >= +0.08:                   BUY
elif edge_score <= -0.08 and short_ok:      SHORT
# short_ok = (value < 0) and (positioning <= 0)
#   -> a short additionally needs the event RICHLY PRICED and the name NOT beaten down,
#      because shorts fight the long-side earnings-announcement premium.
```

### 7.4 Conviction and sizing — **the part Q1 is about**
```python
TIERS = [(0.55,"MAXIMUM",1.50%), (0.35,"HIGH",1.00%),
         (0.20,"STANDARD",0.60%), (0.08,"EXPLORATORY",0.25%)]

SIZE_BY_CONVICTION = False        # <-- the contested decision
FLAT_RISK_BUDGET   = 0.50%

# tier is COMPUTED and LOGGED but does NOT size. Instead:
budget = FLAT_RISK_BUDGET * confidence      # 0.275% .. 0.50%
shares = (budget * capital) / (avg_abs_open/100 * price)
```
The author's stated distinction:
- **CONVICTION** = |edge_score| = "how strong is my read" → inverted in the data → must not size.
- **CONFIDENCE** = information completeness = "how much do I know" → sizes, as risk hygiene.

Dampers (macro overlap, vol-hot, g2_estimated) demote one tier each — but since tiers don't
size, they currently have **no effect on position size at all**. *(Is that an oversight? It is
not flagged anywhere in the code. — worth checking.)*

### 7.5 Sector weights (24 hand-set priors, frozen, declared)
Multipliers applied to components before summing into `directional`, clamped [0.3, 2.0]:

| Factor | Semis | Pharma | Fintech | Software | Industrial | Energy |
|---|---|---|---|---|---|---|
| REV | 0.8 | 0.5 | 1.0 | 1.3 | 0.8 | 0.4 |
| GG | 1.2 | 0.8 | 1.5 | 1.5 | 1.0 | 0.6 |
| VEL | **2.0** | 0.5 | 1.0 | 1.5 | 0.8 | 0.5 |
| SAT | 0.8 | 0.5 | 1.0 | 1.0 | 1.0 | 0.8 |

Rationale is economic, not fitted: semis lead on bookings; SaaS lives on the guide; pharma
prints are mostly non-events vs trial readouts; energy is a commodity echo.

## 8. SOURCING, VERIFICATION, DATA HYGIENE

- **Web-source before fail-closed:** on a covered name with a thin/empty feed, a second web
  source is checked before marking a leg UNAVAILABLE (Yahoo's US revision feed is empty for
  foreign ADRs, etc.).
- **C4 cross-source reconciliation:** judgment values compared against a pinned-source "Truth"
  object; divergence beyond tolerance → INPUT_INVALID (fail closed). Catches bad inputs.
- **C1 sanity bounds** on every numeric input.
- **Implied-move decontamination:** no listed expiry sits exactly on the event, so the raw
  straddle prices the event PLUS extra days of vol. Stripped via
  `event_IM = sqrt(IM_raw² − realized_daily_vol² × trading_days_to_expiry)`. If the only expiry
  is >20 days out, IM is treated as unmeasurable (None). **This prevented several false
  "rich → short" reads.**
- **Perimeter adjustment:** for a spin-off (e.g. a company that spun off a division 3 weeks
  before its print), PED / 52-week-high / revenue-growth are all corrupted; adjusted to a
  constant perimeter before scoring.
- **C12 forward-sourcing:** on order-driven names a `TRAILING_REVENUE` VEL basis is rejected
  outright (VEL discarded, band widened).

## 9. THE LEARNING LOOP

**Ledger** (`pre_ledger.py` v1.5.3), append-only, integrity-hashed:
- **Pre-registration:** before each print the full decision + inputs are frozen with SHA-256.
  No look-ahead in inputs is possible.
- **Outcome:** market-model abnormal return `AR = R_stock − β·R_benchmark`. β is estimated on a
  clean pre-event window (60 days, with a 21-day buffer so the run-up into *this* print doesn't
  contaminate the estimate), sanity-clamped to [0.2, 3.0], falling back to β=1 **flagged**.
  *(β was hard-assumed = 1 until 2026-07-29; real betas are 1.34 AMKR, 1.11 CLS, 1.71 NVTS.)*
- **Hold-to-close shadow:** the same-day close move is recorded in parallel so both exit
  horizons accrue. Live exit unchanged.
- **Kill-switches** (arm at n≥15): idio-sign accuracy <50%, component <50%, tier inversion.
- **Override logging:** any narrative override of a mechanical signal is logged and scored.

**POST-MORTEM SOP (binding, `docs/POSTMORTEM_SOP.md`)** — adopted from review #1:
- **Failure taxonomy, classified BEFORE any fix is proposed:**
  **A** Observable-miss (fixable: fix input/scoring) · **B** Unobservable — information boundary
  (**patching FORBIDDEN**) · **C** Right thesis, wrong expression (fix exit/instrument only) ·
  **D** Random (**patching FORBIDDEN** — it is overfitting by definition)
- **THE ABSTRACTION TEST** — a fix ships only if it passes both: (1) would it have prevented the
  LAST failure of the same type? (2) does it break a previously WINNING trade?
- **Anti-gaming clause:** you may not rescue a fix by asserting a favourable input.
- **The inversion:** when a call is wrong, the FIRST hypothesis is "the model is wrong"; you must
  DISPROVE that before concluding "unlucky."

**What the loop still does NOT do:** it records but does not revise. Thresholds are frozen.
There is no principled mechanism converting accumulated outcomes into updated weights.

## 10. TRACK RECORD (complete and honest)

**Directional bets: 2 wins in 5 (40%), below coin-flip.**

| Call | Conv | idio (market-model) | Note |
|---|---|---|---|
| AEHR BUY | LOW | **+35%** ✅ | record bookings. On honest replay, later gates would have *blocked* it |
| ASML SHORT | LOW | +1.7% ❌ | wrong |
| NFLX BUY | MED | −10.6% ❌ | washout-buy on undefined fundamentals |
| CLS BUY | MED | **+0.02%** ✅ | marginal win on gap; **closed +4.7%** — right thesis, exit caught the dip |
| AMKR BUY | MED | **−10.15%** ❌ | **beat Q2, guided Q3 down.** See Q2. |

**Two findings the author considers most important:**
1. **The model's abstentions have outperformed its bets.** Its NO_TRADEs avoided several bad
   longs; its actual BUYs mostly lost.
2. **The alpha is intraday, not overnight.** Repeatedly the overnight gap is tiny and the real
   move happens during the day (GLW −0.4% gap / −13.5% close; PYPL flat gap / +6.2% close). The
   fixed exit-at-open structurally misses this. **The operator has ruled: keep gap-capture.**

## 11. WHAT CHANGED SINCE REVIEW #1 (so you don't re-tread it)

Review #1 recommended: pivot to buying straddles (#1), replace worst-case-band with edge sizing,
promote hold-to-close, sector matrices, raise the short hurdle, remove a "freshness" gate,
Bayesian learning loop, post-mortem SOP, fix beta.

**Accepted and shipped:**
- ✅ Post-mortem SOP + Abstraction Test (§9) — **binding**
- ✅ Beta fix (§9) — materially changed the record (CLS flipped loss → win)
- ✅ Short hurdle raised (`wash <= 0` → `wash == -1`)
- ✅ **Reverted the author's own "guide-freshness" gate.** The author had shipped it the day
  before; the Abstraction Test showed it failed both limbs (wouldn't have prevented AMKR; blocks
  AEHR, the only winner). The author also admitted to having made its test pass by asserting a
  favourable input — which is why the anti-gaming clause exists.
- ✅ Edge Score built and wired in as production (§7)

**Rejected by the author, with reasons (verify these judgments):**
- ❌ **Straddle pivot.** Tested on this model's own data — see §12.3.
- ❌ **Hold-to-close promotion.** Its justification was a statistic the author later showed to be
  invalid (comparing mean |gap| to mean |close move| conflates *more information* with *more
  elapsed time*; a longer window has larger absolute moves under a pure random walk).
- ❌ **Announcement-premium harvesting as a per-trade signal** — ~10bp/day on $180 positions is
  annihilated by costs.
- ❌ **Bayesian auto-revision as specified** — its n-thresholds (n≥15/config, n≥30/sector×config)
  are unreachable at this trade rate, and it optimises *hit rate*, which is wrong for
  fat-tailed gap returns (40% wins at +15%/−5% beats 60% wins at +2%/−4%).

## 12. THE SPECIFIC NUMBERS TO CHECK

### 12.1 Decision backtest (all 30 frozen ledger entries; 17 with outcomes)
| | live calc-risk | edge score |
|---|---|---|
| Abstention rate | 22/25 = **88%** | 14/25 = **56%** |
| Verdicts | BUY 3, SHORT 0 | BUY 9, SHORT 2 |
| Trades scored | 2 | 8 |
| Winners | 1 | 3 |
| Net P&L ($18k book) | **−$79.01** | **−$78.88** |

Decisions that changed (NO_TRADE → live bet): AEHR, ASML (no outcome yet), INTC (−$10.16),
SAP (**+$47.85**), APLD (**+$35.55**), GLW (−$28.14), NVTS (−$24.72), PYPL (−$7.12).

**The author's own caveat, which you should stress-test:** this P&L is
**hindsight-contaminated** — the scorer was designed with knowledge of these outcomes. Is the
author's claim that "the decision-behaviour numbers are reliable even though the P&L isn't"
actually true? Or is the abstention-rate improvement *also* a product of tuning to this sample?

### 12.2 Variant sweep (robustness, run to test whether the loss is structural)
Every configuration tested lost money. `ex-AMKR` isolates the single large loser:

| variant | trades | net | ex-AMKR |
|---|---|---|---|
| A as-designed (tiered sizing) | 8 | −$388.89 | −$72.34 |
| B cap top tier at 1.0% | 8 | −$283.37 | −$72.34 |
| C flat sector weights | 9 | −$382.26 | −$65.71 |
| D de-weight direction .30/.40/.30 | 8 | −$325.64 | −$114.61 |
| E D + cap | 8 | −$291.46 | −$80.43 |
| F wider dead-band (0.20) | 6 | −$409.82 | −$93.28 |
| **G flat 0.5% sizing** | 8 | **−$91.98** | **+$13.53** |

The author chose G's *principle* (flat sizing). **Is choosing G defensible, or is it selecting
the best-performing variant on a 17-event sample — i.e. overfitting?** The author's defence:
"I'm not choosing it because it won; I'm choosing it because sizing by an unvalidated signal is
unjustified, and the ex-AMKR column shows the variants are indistinguishable anyway." Assess that.

### 12.3 Why the straddle pivot was rejected
Review #1's top recommendation was "buy straddles when implied is cheap vs history (IRM ≤ 0.85)."
Tested on every cheap-IRM name in the ledger, **paying the RAW listed straddle** (the price you
can actually transact, not the decontaminated event-IM):

| Name | raw straddle paid | actual gap | gap P&L | close P&L |
|---|---|---|---|---|
| NVTS | 16.70% | −10.12% | −6.58 | −5.42 |
| GLW | 11.36% | +1.67% | −9.69 | +2.12 |
| PYPL | 7.59% | +1.23% | −6.36 | −1.37 |
| | | **total** | **−22.63** | **−4.67** |

Author's reasoning: (a) you cannot buy the decontaminated price — no expiry sits on the event, so
you pay for extra days and eat the IV crush on them; (b) review #1 never addressed the
**variance risk premium** (earnings options are systematically expensive to buy, which is why
sellers earn); (c) retail options spreads on an $18k account. **Is this reasoning correct?
Is there a version of the volatility trade that does work here?**

## 13. WHAT THE AUTHOR BELIEVES IS STILL BROKEN (their own list)

- No mechanism converts the ledger into revised weights — it records, it doesn't learn.
- Conviction doesn't predict (that is Q1).
- Direction may be unwinnable (that is Q2).
- Positioning/flow inputs exist as fields but **nothing populates them live**.
- The expression layer names an instrument (equity / straddle / put spread) but **prices
  nothing** — no option-pricing model exists anywhere in the repo.
- Dampers demote tiers, but since tiers don't size, dampers currently do nothing.

## 14. CLAIMS THAT MUST NOT BE MADE (the code does not support them)

- ❌ Black-Scholes / option pricing / implied-vol modelling. `implied_move` is an INPUT.
- ❌ That this is an "event study" with statistical significance. It is a market-model abnormal
  return with an estimated beta, no estimation-window test statistic.
- ❌ Any ML / learned weights — every threshold is hand-set.
- ❌ Any backtested edge (n≈8; a full-pipeline historical backtest is impossible because the
  judgment layer cannot be reconstructed at T−1 without look-ahead).
- ❌ Programming proficiency by the operator (AI-assisted from written spec).

---

# PART C — YOUR DELIVERABLE

1. **A direct verdict on Q1** — legitimate fix, or symptom-patching on n=1? If the latter, what
   should have been done instead?
2. **A direct answer on Q2** — does directional pre-print betting have recoverable edge? If not,
   what replaces it, engaging with why the straddle test failed here?
3. **Q3: everything you found in the broad sweep** that neither prior party noticed — especially
   in the **data layer, verification layer, and learning loop**, which have had least scrutiny.
4. **The minimum change set** that addresses your diagnosis. Ranked by impact. Explicitly mark
   which are safe to ship now vs which need forward validation. **"Change nothing and collect
   data" is an acceptable recommendation** if that is the honest answer.
5. **Anything in this document you believe is wrong, overstated, or self-serving.** The author
   wrote it. Assume motivated reasoning and check accordingly.

Be specific, show your reasoning, and do not defer to existing choices. If the honest answer is
"scrap it and do X," say that.
