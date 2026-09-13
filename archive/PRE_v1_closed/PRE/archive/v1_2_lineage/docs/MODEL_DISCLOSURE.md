# PRE v1.2 — FULL MODEL DISCLOSURE (audit-ready introspection)

> Scope note, read first. This document describes the **actual implemented system**
> (`pre_engine.py`), not an idealized quant model. The PRE model is **deliberately
> NOT** a machine-learned, weighted-sum, probability/EV engine. It is a
> **deterministic, rule-based, integer-bucket directional-sign classifier wrapped
> in hard fail-closed gates and gap-at-risk sizing.** Where your evaluation template
> assumes z-scores, learned weights, options-flow, or EV modelling, the honest
> answer is usually "not used — here is what is used instead, and why." Those
> deliberate omissions are documented in §8 and §13; they are the most important
> part of this disclosure.

---

## 0. Architecture in one paragraph

Two hard-separated layers. (1) A **REASONING layer** (an LLM) turns messy public
data into a small set of **named RAW values with source + timestamp** — it never
scores. (2) A **deterministic ENGINE** (`pre_engine.py`, the "sealed core") does
every bucket, compare, sum, gate, sizing, log, and post-mortem — it never fetches
or guesses. A missing input scores 0 and is flagged UNAVAILABLE; gates fail closed.
The human ("Jacob") initiates and signs off. The verdict is never the LLM's.

---

## 1. Objective and output definition

### 1.1 Objective function
The model does **not** maximize expected return or a fitted risk-adjusted metric.
Its objective is:

> **Maximize cumulative idiosyncratic-SIGN accuracy on pre-earnings directional
> events that survive a fail-closed screen, while sizing every position so a single
> earnings gap risks ≤ ~0.5%–0.75% of capital.**

Two consequences: (a) it optimizes being **directionally right on the beta-stripped
open move**, not P&L magnitude; (b) it is **selection-first** — most candidates are
rejected (NO TRADE). The design prior is that a small number of high-discipline,
asymmetry-backed trades beats a large number of predicted-EV trades on small-n data.

### 1.2 Decision definitions and triggers
Let `DS` = direction score (integer, §4). Let CBR ∈ {CLEAN, MANUFACTURED}.

| Action | Trigger (strict cascade order) |
|---|---|
| **NO TRADE** | any hard gate fails after worst-case test; OR DS inside (−3, +3); OR long-blocked with no short |
| **DRY RUN** | G0 says not T−1 (out of entry window) — screen shown but not tradeable |
| **INCOMPLETE** | a missing/UNAVAILABLE input could flip the verdict across a ±3 band (worst-case test, §5) |
| **BUY SHARES** | DS ≥ +3 AND CBR = CLEAN AND all gates pass |
| **SHORT SHARES** | DS ≤ −3 AND G4 (borrow) passes AND all gates pass |

Thresholds: execution band = **±3**. Conviction: **|DS| ≥ 5 → HIGH**, **|DS| ∈ {3,4}
→ MEDIUM**, else NONE. There is deliberately **no LOW tier** — sub-MEDIUM is NO TRADE
by construction.

---

## 2. Input variables and data dependencies

Inputs split into **ENGINE market data** (numeric, caller-supplied) and **REASONING
judgment inputs** (LLM-extracted RAW values). The engine treats all as given; it
validates none against the world.

### 2.1 Judgment inputs (LLM-supplied RAW; the weak link — see §8)
| Input | What it is | Why it matters | Directional impact |
|---|---|---|---|
| **G0** | earnings date + session, dual-sourced (IR + independent calendar) | wrong date = wrong/void trade | gate only (fail-closed) |
| **REV** raw | # up-revisions, # down-revisions, # covering analysts (30d) | revisions proxy pre-print drift in expectations | + = upside underpriced |
| **GG** raw | last issued guidance RANGE vs current consensus (revenue; EPS fallback) | sandbag/stretch detection | ≤midpoint bullish |
| **VEL** raw | the correct per-name KPI (SaaS cRPO, semis DC rev, banks NII, retail comps, EV deliveries, defense backlog…) current vs prior Q | operating momentum the tape underweights | accel = bullish |
| **SAT ETF** | the correct sector benchmark for excess-PED | isolates idiosyncratic run-up/down | context for SAT |
| **REACT** | last 4 confirmed prints: beat/miss + open direction | how the tape *treats* this name's beats | sell-the-news detection |
| **FLAG** | pre-announce / exec exit / KPI redefinition / insider sells | discrete red flags | subtract-only |
| **CBR** C1/C2/C3 | M&A-inflation, per-share erosion, guide-basis checks | detects manufactured beats | binary long-block |

### 2.2 Market data (numeric, caller-supplied)
price; 20d avg dollar volume; 20d avg share volume; `avg_abs_open` (avg absolute
earnings-day open gap % over last ≥4 quarters); confirmed_quarters; implied_move;
stock % since last earnings; sector-ETF % same window; % within/below 52-wk high;
VIX; SPY 5d realized-vol WoW; entry-day SPX move; macro-calendar overlap
(FOMC/CPI/NFP); borrow locate + fee; capital; open book (weekly gross/net units,
concurrent, per-sector).

### 2.3 Inputs deliberately NOT used
EPS/rev estimate **dispersion**; **implied-vol surface / skew / open interest** (only
`implied_move` is used, and only for the IRM *diagnostic* + sizing — never scored);
absolute valuation multiples (P/E, EV/EBITDA); balance-sheet ratios; retail-sentiment
proxies; explicit institutional positioning; macro factor betas (rates/FX/commodities).
See §13.

---

## 3. Feature engineering and transformations

There is **no normalization, z-scoring, percentile-ranking, or min-max scaling.**
Raw values map through **fixed threshold step-functions into small integers.** This
is a deliberate anti-overfit / reproducibility choice (§8).

- REV: continuous ratio → 5-way bucket {−2,−1,0,+1,+2}.
- GG, VEL, REACT: the LLM hands a pre-bucketed {−1,0,+1} per fixed spec rules (the
  engine passes them through; it does not re-derive from raw ranges — a known
  reproducibility soft spot, see §8).
- SAT: two continuous inputs → two 3-way sub-buckets → summed → clamped [−2,+2],
  gated by REV sign.
- FLAG: additive negatives, clamped [−2, 0].

No derived indicators, moving averages, or momentum lookbacks beyond the single
"stock % since last earnings" window used by SAT.

---

## 4. Decision logic framework (step-by-step)

**Step 1 — signal generation.** Compute six components:
```
REV, GG, VEL, SAT, REACT, FLAG   (each a small integer)
```

**Step 2 — signal weighting.** Weights are **fixed and equal (all 1.0).** No learned
or dynamic weights. The direction score is an **unweighted sum**:
```
DS = REV + GG + VEL + SAT + REACT + FLAG        # practical range ≈ [-6, +6]
```

**Step 3 — conflict resolution.** There is no soft conflict blending. Conflicts net
arithmetically in the sum, with three structural exceptions:
- **REV-gate on SAT(a):** a saturation/vacuum ±1 only fires if it agrees with REV's
  sign (else 0). Prevents fading a strong tape with positive revisions, or catching
  a knife with negative ones.
- **Falling-knife guard on SAT(b):** the "cheap, >25% below high" +1 only fires if
  REV ≥ 0.
- **CBR long-block:** overrides DS entirely for the long side.

**Step 4 — final scoring.** DS is the scalar. Conviction tier from |DS|.

**Step 5 — map to action.** Strict cascade (first match wins):
```
if   G0 UNAVAILABLE/UNRESOLVED         -> NO TRADE
elif G0 == DRY_RUN (not T-1)           -> DRY RUN
elif any hard gate FAIL (worst-case)   -> NO TRADE
elif DS >= +3 and CBR == CLEAN         -> BUY   (worst-case flip test may downgrade to INCOMPLETE)
elif DS >= +3 and CBR != CLEAN         -> NO TRADE (long blocked)
elif DS <= -3 and G4 pass              -> SHORT  (worst-case flip test may downgrade to INCOMPLETE)
elif DS <= -3 and not G4               -> NO TRADE (short blocked)
elif unavailable inputs could reach ±3 -> INCOMPLETE
else                                   -> NO TRADE
```

---

## 5. Probabilistic thinking and uncertainty handling

**The model does not assign probabilities or compute EV.** Uncertainty is handled by
**fail-closed worst-case reasoning**, not Bayesian updating:

- **Missing data** → component scores 0, flagged UNAVAILABLE.
- **Could-it-flip test** (the core uncertainty rule): each UNAVAILABLE judgment
  input has a known reachable range (GG,VEL,REACT ∈ [−1,+1]; FLAG ∈ [−2,0]). Compute
  `DS_floor` (all unavailable at their worst) and `DS_ceil` (all at their best). If a
  BUY's `DS_floor < +3`, or a SHORT's `DS_ceil > −3`, the verdict is **INCOMPLETE**,
  not a trade. A verdict only stands if it survives the worst-case resolution.
- **ESTIMATED inputs** (G2 <4 confirmed quarters) may never be the deciding margin —
  removing them must not flip the verdict, else NO TRADE.
- **Low-confidence setups** collapse to NO TRADE by the ±3 band + no-LOW-tier rule.

This is the honest boundary: PRE is a **sign classifier with a fail-closed abstention
region**, not a probabilistic forecaster. (The absence of an EV/skew layer is the
single biggest capability gap — §13, and `docs/convexity_overlay_design.md`.)

---

## 6. Risk management layer (applied BEFORE the decision)

Risk gates run first and can veto any signal:
- **G1 liquidity:** 20d avg $ volume ≥ $25M **AND** position ≤ 1% of 20d avg share
  volume. Fail → NO TRADE.
- **G2 gap-history:** `avg_abs_open ≥ 2.0%` over ≥ 4 confirmed quarters. Names that
  don't move on earnings are rejected (no event edge to trade).
- **G3 macro overlap:** FOMC/CPI/NFP between entry and exit → **×0.5 size damper**
  (not a veto).
- **G4 borrow (shorts only):** locate confirmed AND fee ≤ 5% annualized, else short
  side blocked.
- **Volatility damper:** VIX > 28 OR SPY 5d realized vol +50% WoW OR entry-day |SPX|
  > 1.5% → **×0.5 size**.
- **Sizing IS the stop.** There is no stop-loss — you cannot stop through an overnight
  gap. Risk is controlled entirely ex-ante by position size (§14.D).

Signals are overridden by risk when: any gate fails; CBR flags a manufactured beat
(long veto); an ESTIMATED input is load-bearing.

---

## 7. Edge identification

**Core edge = disciplined fail-closed selection + a few specific behavioral/structural
asymmetries** — not superior point-prediction. Concretely:
1. **Abstention.** The model trades rarely and only when multiple independent
   components align and no gate/CBR objects. Most "edge" is in the trades **not** taken.
2. **Priced-in / saturation logic (SAT + REV-gate).** Fades over-loved names and
   refuses to catch falling knives, cross-checked against revision direction.
3. **Manufactured-beat detection (CBR).** Blocks longs on M&A-inflated or
   per-share-eroding "beats."
4. **Gap-at-risk sizing.** Normalizes risk across wildly different volatilities so no
   single event dominates.
5. **Frozen pre-registration + beta-stripped post-mortem.** Removes hindsight bias and
   scores on idiosyncratic sign, enabling honest kill-switch feedback.

**Strengthened by:** clean single-name events; verifiable KPI (VEL) and revisions;
confirmed gap history; no corporate-action noise. **Weakened/invalidated by:** thin
coverage (REV denominator tiny); parabolic names (SAT(b) quirk, §8); heavy M&A;
macro-dominated tapes; anything where the judgment inputs can't be verified.

---

## 8. Failure modes and weaknesses (explicit and critical)

1. **Garbage-in on judgment inputs is the dominant risk.** The engine is only as good
   as the LLM-supplied RAW values. Documented live failure: an **AEHR** run where a
   wrong "stock % since last earnings" (−10% guessed vs +190% actual) flipped SAT +1→+2
   and the verdict INCOMPLETE→BUY. The logic was correct; the input was not. There is
   **no input-plausibility validation** in the engine.
2. **No EV / payoff-skew layer.** The model scores directional *sign* only. It cannot
   see "catalysts already priced in / sell-the-news" convexity. It will mis-rate
   events where direction is a coin-flip but payoff is skewed. (Biggest structural gap.)
3. **SAT(b) parabolic-pullback quirk.** ">25% below 52-wk high → cheap +1" mis-reads a
   pullback in a parabolic name (e.g. a stock up 200% then off 40% from a 3-week-old
   spike) as a "vacuum" buy. Known, flagged, not yet fixed.
4. **Coarse integer buckets.** Hard thresholds create cliff effects (R=0.099→0 vs
   0.101→+1) and discard magnitude. Deliberate anti-overfit tradeoff, but genuinely
   lossy.
5. **GG/VEL/REACT are LLM-pre-bucketed**, so those three components are **not fully
   reproducible** from raw values inside the engine — a hole in the "engine does all
   scoring" claim.
6. **Small-n / thin-coverage fragility.** REV = (up−down)/covering with ~3–4 analysts
   is noisy and can swing a verdict on one rating change.
7. **Regime dependency.** Purely bottom-up, single-name; no macro/factor/correlation
   awareness. In macro-driven or correlated selloffs the idiosyncratic thesis is
   swamped (taxonomy D: beta contamination).
8. **Single-event, single-name scope.** No cross-position correlation model; caps are
   crude counts (weekly gross/net units, concurrent, per-sector).
9. **Data lag.** Judgment inputs are point-in-time web scrapes; revisions/positioning
   can be stale vs. the true T−1 state.
10. **Overfit surface = thresholds, not weights.** The parameters most at risk of
    fitting to past cases are the bucket cutoffs (e.g. SAT ±20/−10, the REV-gate) —
    some were set from n=2 cases (ACN, MU). Governed by WATCH → 2-holdout → sign-off
    and a parameter ceiling (30; currently 23), but the risk is real.

---

## 9. Backtesting and validation logic (conceptual)

Evaluated **only on beta-stripped idiosyncratic sign**, over pre-registered (frozen,
integrity-hashed) entries. Unregistered runs are excluded from stats in both
directions.

Metrics that matter, in priority:
- **Idio-sign accuracy** = correct / n_outcome (THE number). Kill switch: **<50% at
  n ≥ 15 → PAUSE.**
- **Per-component standalone hit rate** (does each component's own sign match realized
  idio sign, among nonzero contributions). Kill switch: **<50% at n_nonzero ≥ 20 →
  ablation candidate.**
- **Type-B (saturation-misread) rate** in last 10 outcomes; **>2/10 → recalibrate SAT.**
- **Calibration:** idio-sign hit and mean |idio| by conviction tier (expect HIGH >
  MEDIUM); mean IRM and |idio| split by IRM median.
- Raw P&L logged **separately** — never the accuracy metric.

**A statistically valid edge** = idio-sign accuracy sustained > 50% (materially, not
marginally) at n ≥ 15–20, with no component acting as a net drag at n ≥ 20, and Type-B
contained. ANOMALY-classified outcomes (exogenous shocks) are **frozen out** of all
tuning stats so a court ruling / M&A / geopolitical gap can't distort calibration.

---

## 10. Adaptability and learning

- **Fixed (sealed core):** all arithmetic, gate logic, the cascade, sizing, fail-closed
  behavior. Never weakened by an amendment.
- **Adaptive (governed):** bucket thresholds, the component set (via ablation), new
  WATCH rules — but **only** through: name a failure case (ticker+date+taxonomy) →
  WATCH → **2 independent, non-anomaly holdout confirmations** → human sign-off.
- **Plumbing vs logic (outcome-equivalence rule):** a change is auto-appliable only if
  re-running the full historical log reproduces **byte-identical** component values and
  verdicts; anything that moves a logged value/verdict is "logic" and needs the holdout
  path. Frozen records are never re-hashed; new schema is forward-only.
- **Degradation signals:** any tripped kill switch; rising Type-B; a component's
  standalone hit decaying below 50% at n ≥ 20; widening gap between conviction tiers
  inverting (HIGH underperforming MEDIUM).

---

## 11. Example walkthrough (full)

**Input (RAW):** AEHR, earnings T (AMC). Judgment: REV up=2/down=0/cov=4; VEL=+1
(bookings accelerating); GG,REACT = UNAVAILABLE; FLAG=0; CBR C1/C2/C3 all PASS; G0
confirmed. Market: price=$76; avg_abs_open=21.05% (8 qtrs); stock +190% since last
earnings; sector +30% same window; 40% below 52-wk high; capital $500k; empty book;
no macro overlap; VIX 18.

**Transform → components:**
- REV: R=(2−0)/4=+0.50 ≥ 0.30 → **+2**
- VEL: **+1** (passed in)
- GG, REACT: UNAVAILABLE → **0** (flagged)
- SAT: excess = 190−30 = +160 ≥ +20 → implied −1 (saturation); REV=+2 not <0 →
  REV-gate **blocks** it → SAT(a)=0. 40% below high (>25%) with REV ≥ 0 → SAT(b)=+1.
  SAT = **+1**.
- FLAG: **0**
- **DS = +2 +1 +0 +1 +0 +0 = +4**

**Gates:** G1 pass; G2 pass (21.05%, 8 qtrs, CONFIRMED); CBR CLEAN; G0 confirmed.

**Worst-case flip test:** DS_floor = 4 + GG(−1) + REACT(−1) = **+2 < +3** → the
verdict could flip if the unavailable inputs come in negative → **INCOMPLETE.**

**Decision: INCOMPLETE** (not BUY). **Why correct:** a +4 that only clears the band if
two unverified inputs cooperate is not a fail-closed trade; and the single positive
holding SAT up is the known parabolic-pullback quirk. (This is the *corrected* AEHR
result; the earlier BUY came from a bad PED input — see §8.1.)

---

## 12. Self-evaluation checklist (per decision)

- [ ] **Data completeness:** are REV, GG, VEL, SAT-ETF, REACT, FLAG, CBR, G0 all
  present with source + timestamp? Which are UNAVAILABLE/ESTIMATED?
- [ ] **Input plausibility:** is "stock % since last earnings" sign-checked against the
  actual chart? (the AEHR failure lives here)
- [ ] **Signal alignment:** do ≥ 2 components independently agree with the verdict, or
  is it carried by one fragile component (e.g. thin-coverage REV, or SAT(b))?
- [ ] **Gate validation:** G1/G2 pass on the *sized* position; G0 dual-sourced; G3/vol
  dampers applied; G4 for shorts.
- [ ] **CBR:** clean, or long-blocked?
- [ ] **Worst-case survival:** does the verdict hold with all UNAVAILABLE inputs at
  their most adverse? If not → INCOMPLETE.
- [ ] **ESTIMATED margin:** is any ESTIMATED input the deciding margin? If yes → NO TRADE.
- [ ] **Confidence:** |DS| ≥ 5 HIGH / 3–4 MEDIUM; below → NO TRADE.
- [ ] **Skew sanity (manual, until overlay exists):** are the catalysts already public
  / priced in? Is this a coin-flip-with-fat-tails where sign-edge ≠ EV-edge?

---

## 13. Missing capabilities (honest and explicit)

**Data I don't reliably have / don't ingest:** live options surface (IV term structure,
skew, open interest, dealer gamma); real-time order flow / dark-pool prints; true
institutional 13F-lag-free positioning; borrow-availability depth beyond a yes/no+fee;
intraday tape; estimate **dispersion**; management-tone/NLP from transcripts;
supply-chain / alt-data.

**Models I don't implement:** any ML/statistical learner (no regression, GBM, NN);
probability calibration; a payoff/EV or **convexity/skew** model (designed, not built —
`docs/convexity_overlay_design.md`); a portfolio/correlation/risk-parity layer;
vol-surface pricing to judge whether the event is rich/cheap (currently only the crude
IRM diagnostic); regime detection.

**Operational limits:** judgment inputs are point-in-time and human/LLM-mediated (lag +
error surface); no automated execution; single-name single-event scope; the three
LLM-bucketed components (GG/VEL/REACT) aren't reproducible from raw inside the engine.

**Highest-value additions, ranked:** (1) an EV/skew overlay so sign-edge isn't confused
with trade-edge; (2) engine-side input-plausibility validation (would have caught the
AEHR error); (3) move GG/VEL/REACT bucketing into the engine from raw ranges for full
reproducibility; (4) a vol-richness read (realized-vs-implied) to flag priced-in setups
and enable defined-risk expressions.

---

## 14. Full formulas and mathematical logic

### A. Signal definitions

**REV (analyst revision score)**
```
R = (up_revisions_30d - down_revisions_30d) / covering_analysts      # covering>0 else UNAVAILABLE→0
REV =  +2 if R >= 0.30
       +1 if 0.10 <= R < 0.30
        0 if -0.10 < R < 0.10
       -1 if -0.30 < R <= -0.10
       -2 if R <= -0.30
# example: up=2,down=0,cov=4 -> R=0.50 -> REV=+2
```

**GG (guide-vs-consensus), VEL (KPI velocity), REACT (reaction history)** — each is a
RAW {−1,0,+1} produced by the LLM per fixed spec rules, passed through by the engine
(None → 0, UNAVAILABLE):
```
GG   = +1 if consensus <= guide_midpoint ; 0 if midpoint..high ; -1 if > guide_high ; 0 if no guide
VEL  = +1 if reported_PMM_YoY - prior_Q_PMM_YoY >= +400bps ; -1 if <= -400bps ; else 0
REACT= +1 if beats opened up in >=3 of last 4 ; -1 if beats opened flat/down in >=2 of 4 ; else 0
```

**SAT (saturation), two parts, clamp [−2,+2]:**
```
excess_PED = stock_pct_since_last_earnings - sector_etf_pct_same_window
# (a) with canonical REV-gate:
if   excess_PED >= +20:  a = -1 if REV < 0 else 0          # saturation needs REV<0
elif excess_PED <= -10:  a = +1 if REV > 0 else 0          # vacuum needs REV>0  (W1 override: or VEL>=+1 & deeply_beaten)
else:                    a = 0
# (b) 52-week, falling-knife guard:
if   pct_within_52w_high <= 5:   b = -1
elif pct_below_52w_high  > 25:   b = +1 if REV >= 0 else 0  # (W1 override: or VEL>=+1)
else:                            b = 0
SAT = clamp(a + b, -2, +2)
```

**FLAG (subtract-only, clamp [−2,0]):**
```
FLAG = clamp( sum of: (-2 pre-announce)(-1 CEO/CFO change <90d)(-1 KPI redef)
                      (-1 sales-lead exit <60d, enterprise name)(-1 holder exit >1% float 30d), -2, 0)
```

**IRM (diagnostic only, never scored):**
```
IRM = implied_move_pct / avg_abs_open_pct        # >1 = event richly priced vs realized history
```

### B. Aggregation and weighting
```
DS = REV + GG + VEL + SAT + REACT + FLAG          # weights all = 1.0, FIXED, not learned
```
**No normalization is applied** (no z-score, percentile, or min-max). Inputs are mapped
by fixed threshold step-functions (§A). This is intentional; see §8.

### C. Decision thresholds and rules
```
T_buy = +3 ; T_short = -3 ; HIGH if |DS|>=5 ; MEDIUM if 3<=|DS|<=4
# strict cascade (first match wins):
if g0 in {None, "UNRESOLVED"}:                 action = NO_TRADE
elif g0 == "DRY_RUN":                          action = DRY_RUN
elif not (G1 and G2):                          action = NO_TRADE            # gates fail closed
elif DS >= T_buy and CBR == "CLEAN":           action = BUY   (or INCOMPLETE if DS_floor < 3)
elif DS >= T_buy and CBR != "CLEAN":           action = NO_TRADE            # long blocked
elif DS <= T_short and G4:                      action = SHORT (or INCOMPLETE if DS_ceil > -3)
elif DS <= T_short and not G4:                  action = NO_TRADE            # short blocked
elif unavailable and (DS_floor <= -3 or DS_ceil >= 3): action = INCOMPLETE
else:                                          action = NO_TRADE
# where, over UNAVAILABLE judgment inputs with ranges GG,VEL,REACT∈[-1,1], FLAG∈[-2,0]:
DS_floor = DS + sum(min_range); DS_ceil = DS + sum(max_range)
# hard overrides: G2 ESTIMATED (<4 qtrs) and a would-be trade -> NO_TRADE (estimated cannot be deciding margin)
```

### D. Risk adjustments and sizing
```
base_unit_shares = (0.005 * capital) / ((avg_abs_open/100) * price)   # 1 unit ≈ 0.5% capital at risk per avg gap
raw_units        = 1.5 if conviction=="HIGH" else 1.0
damper_mult      = (0.5 if G3_macro_overlap else 1.0)
                 * (0.5 if (VIX>28 or SPY_5d_realvol_WoW>50 or abs(SPX_day)>1.5) else 1.0)
final_units      = raw_units * damper_mult
shares           = floor(base_unit_shares * final_units)
gap_at_risk_$    = shares * price * (avg_abs_open/100)                # ≈ 0.5%*final_units of capital
# portfolio caps (informational; caller enforces): weekly gross Σunits<=6, weekly net |Σsigned|<=4, concurrent<=5, per-sector<=2
```
There is **no `f(volatility)` multiplier on the score** — volatility enters through
`avg_abs_open` in the *denominator of size* (higher vol → smaller position) and through
the discrete ×0.5 dampers, not through a continuous score penalty.

### E. Probability and expected value
**Not computed.** The model outputs a discrete action, not `P_up`, `P_down`, or `EV`.
The nearest thing to an uncertainty estimate is the worst-case band `[DS_floor, DS_ceil]`
(§C). Building `EV = P_up·AvgGain − P_down·AvgLoss` requires the skew overlay in §13 —
this is the explicit boundary of the current model.

### F. Conflicts and overrides
No `α·EarningsScore + β·PriceScore` blending — components net at equal weight in DS.
Structured overrides only:
```
REV-gate:        SAT(a) ±1 fires only if sign agrees with REV, else 0
falling-knife:   SAT(b) +1 fires only if REV >= 0
CBR long-block:  if CBR != CLEAN -> BUY path disabled regardless of DS
G-gates:         any hard-gate FAIL -> NO_TRADE regardless of DS
ESTIMATED:       G2 estimated + would-trade -> NO_TRADE
worst-case:      trade only if it survives DS_floor/DS_ceil resolution, else INCOMPLETE
```

### G. Full end-to-end chain
```
1. RAW inputs (LLM: REV counts, GG, VEL, SAT-ETF, REACT, FLAG, CBR, G0 ; market data)
2. -> components: REV,GG,VEL,SAT,REACT,FLAG                       (§A, fixed step-functions)
3. -> DS = Σ components (equal weight)                            (§B)
4. -> gates G0..G4 + CBR + worst-case band [DS_floor,DS_ceil]     (§C, §F)
5. -> action ∈ {BUY,SHORT,NO TRADE,INCOMPLETE,DRY RUN}           (§C cascade)
6. if trade: conviction -> units -> dampers -> shares, gap_at_risk (§D)
7. -> freeze pre-registration (integrity_hash) to log
8. post-event: idio_open% = stock_open% - etf_open% ; idio_sign_correct ; classification
   (NORMAL/ANOMALY) ; attribution -> kill-switch monitor (§9)
```

> **Heuristic/rule-based disclosure (as required):** the non-formulaic parts are (i) the
> LLM's extraction and pre-bucketing of GG/VEL/REACT/CBR/G0/FLAG from messy sources —
> each governed by the fixed prose rules in §A/§2, to be implemented exactly as written;
> (ii) the ANOMALY classification (a human/LLM judgment that an outcome was driven by an
> exogenous shock detached from earnings fundamentals — freeze it from stats); (iii) the
> taxonomy A–F assignment in post-mortem. All three are decision rules, not learned
> functions, and are specified precisely enough to code as lookup/conditional logic.

---

## 15. What I am flagging FOR the evaluator (open questions)

1. **The EV/skew gap is the #1 thing to fix.** Sign-edge ≠ trade-edge. A directional
   classifier will keep mis-rating priced-in / sell-the-news setups (the AEHR and NKE
   post-mortems both showed this). Is the proposed convexity overlay
   (`docs/convexity_overlay_design.md`) the right shape, or should sign + skew be one
   joint model?
2. **Input reliability > model logic.** The one real loss driver so far was a wrong
   human/LLM input (AEHR PED), not a logic error. Where should validation live — engine
   plausibility checks, a second-LLM cross-check, or forced dual-sourcing of every SAT
   input?
3. **Integer buckets vs continuous scoring.** Is the anti-overfit benefit of hard
   buckets worth the cliff effects and lost magnitude at this (small) sample size?
4. **Threshold provenance.** Several cutoffs (SAT ±20/−10, REV-gate, the ±3 band) trace
   to n=1–2 cases. Which are defensible priors vs. latent overfit? What n makes each
   trustworthy?
5. **The SAT(b) parabolic quirk** (a pullback in a +200% name reads as "cheap"): fix by
   requiring excess-PED agreement, or by capping SAT(b) when excess-PED is extreme?
6. **Scope.** Single-name, single-event, no correlation model. Is that an acceptable
   permanent boundary, or a gap to close before scaling capital?

*Everything above reflects `pre_engine.py` as of v1.2.2. The sealed core is
reproducible and auditable; the judgment layer is not, and that asymmetry is the
model's real risk surface.*
