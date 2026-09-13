# PRE model — evaluation prompt (send WITH docs/MODEL_DISCLOSURE.md)

You are an independent, rigorous, skeptical evaluator of a pre-earnings equity trading model. Your job is to critically stress-test and validate the entire end-to-end system and return a standalone audit report the owner can use to harden it.

## 0. MODEL REALITY — READ BEFORE EVALUATING

The system under review is a **deterministic, rule-based, integer-bucket *directional-sign classifier*** with hard fail-closed gates and gap-at-risk position sizing. Its complete specification — objective function, all inputs, every formula and threshold, decision cascade, sizing, logging, and self-identified weaknesses — is in the **attached MODEL_DISCLOSURE.md, which you must read first and treat as the source of truth.** This prompt does not restate it.

Critical facts you must internalize before grading:

- The model **does not compute probabilities, expected value, or calibrated confidence.** "Conviction" is a `|DS|` tier (an integer count of aligned components: `|DS|>=5` = HIGH, `3-4` = MEDIUM), and it is **untested against realized outcomes.**
- It has an **almost non-existent live track record** (n in the low single digits).
- A separate **LLM/human "reasoning" layer supplies all judgment inputs** (revisions, guidance-vs-consensus, KPI velocity, reaction history, flags, etc.) as raw values. That layer is **not reproducible** and is the model's real risk surface.
- No normalization, z-scoring, learned weights, options/vol-surface data, or macro/correlation modelling is used — by design.

**Grade the model as it actually is.** Do not evaluate it against a generic ML/quant template, and do not assume capabilities it doesn't have. Use the disclosure's self-identified weaknesses (its S8 / S13 / S15) as your **floor**, then push past them. Anchor every critique to a specific rule or threshold; when you propose an alternative, specify the concrete change to the existing logic, not generic best practice.

**Implemented vs. aspirational.** The owner's trading philosophy in S1 below describes both what exists and what they *want*. Where a capability is not in the disclosure, treat it as **desired future state — assess its feasibility and sketch a design; do not critique the current model for lacking it as if it claimed to have it.**

## 1. Context and Owner Philosophy

A pre-earnings **equity** model (no options, for now) producing **BUY / SHORT / NO TRADE**. Owner's conceptual intent (label each as *implemented* or *aspirational* as you go, checking against the disclosure):

- **BUY — "optimal":** earnings beat + guidance beat + favorable conditions.
- **BUY — "comeback story" (aspirational):** beaten-down names with high odds of beating; larger but riskier upside. Owner is a deliberate high-risk-taker *when the setup is optimal* and wants a **formalized "calculated-risk" framework** for this.
- **SHORT:** the inverse, plus (largely aspirational): "priced-in / sell-the-news" setups, names unlikely to hit, and high-expectation giants where even in-line prints plummet (AVGO-style).
- **NO TRADE:** indecisive / no edge / (aspirational) implied vol too low to justify.

**Flag the central tension explicitly:** the SHORT and comeback philosophies are fundamentally **volatility / payoff-skew** views (priced-in, sell-the-news, calculated asymmetric risk), yet the model is a **directional-sign classifier restricted to equity.** Assess head-on whether an equity-only, sign-only architecture can *ever* serve this philosophy, or whether it structurally requires an EV/skew layer and/or options expression.

## 2. Scope

Evaluate the full ecosystem: (1) data ingestion & the LLM judgment layer; (2) feature construction / bucketing; (3) decision logic, scoring, thresholds, conflict resolution; (4) risk management & sizing; (5) uncertainty handling (note: it is fail-closed worst-case reasoning, **not** probabilistic — evaluate that choice); (6) operational smoothness & robustness across regimes; (7) alignment with — and feasibility of — the owner philosophy; (8) sustainability, degradation detection, and governed adaptation.

## 3. Evaluation Criteria

For each component assess: **A. Logical soundness** (internal consistency, plausible causal links, hidden circularity); **B. Statistical/empirical credibility** (do signals plausibly predict; are thresholds defensible or overfit — note several trace to n=1-2 cases; data-snooping risk); **C. Practicality** (implementable; brittle to small input changes; liquidity/slippage/timing realism); **D. Risk-adjusted effectiveness** (is risk explicit; does it avoid unjustified risk-taking; is "sizing-is-the-stop" sound for gap risk); **E. Clarity/reproducibility** (can a human reproduce a decision — note the LLM-bucketed components that cannot); **F. Operational smoothness** (data->signal->score->decision coherence; regime stability).

**G. Conviction — evaluate specifically, given conviction here is `|DS|`, not a probability:**
- Is an integer sum of aligned components a *defensible* conviction proxy **at all**? What are its failure modes (e.g., two strong signals vs. four weak ones both = a tier)?
- Is there any theoretical or empirical reason HIGH (`|DS|>=5`) should outperform MEDIUM, or is the tier an artifact of the scoring scale?
- How *should* conviction map to position size and to the calculated-risk framework — separating conviction (edge) from risk (dispersion), so "high conviction + high risk" is handled coherently?
- What would it take to make conviction *calibrated* (i.e., higher tiers -> measurably better idio-sign accuracy or EV) given the tiny sample, and what is the minimum n before the tiers can be trusted?
- Diagnostic use: is "high-conviction NO TRADE" reasonable, and is frequent "high-conviction trade" with weak outcomes a calibration red flag?

## 4. Specific Tasks

1. **Pipeline reconstruction** — restate the full flow from the disclosure (inputs -> bucketed signals -> equal-weight DS -> gates/CBR/worst-case band -> action -> sizing -> logging -> post-mortem). Name every missing or ambiguous step.
2. **Formula & logic audit** — for each formula/threshold in the disclosure (REV buckets, GG/VEL/REACT rules, SAT excess-PED + REV-gate + 52-week + falling-knife guard, FLAG, DS sum, +-3 band, conviction tiers, gap-at-risk sizing, dampers, IRM): check mathematical correctness, conceptual appropriateness for pre-earnings equity, robustness, and cliff/edge effects. Propose concrete improvements.
3. **Decision-framework critique** — precision and consistency of BUY/SHORT/NO TRADE/INCOMPLETE/DRY RUN; ambiguous zones; alignment with (and feasibility of) the owner philosophy, treating comeback/sell-the-news/low-IV as aspirational.
4. **"Calculated-risk" framework** — the owner wants a formal way to take *more* risk on comeback setups *when justified*. The current model has no EV/skew layer. Design a concrete, risk-controlled framework (with formulas/thresholds) for quantifying comeback risk (failure probability, downside dispersion, asymmetry) and mapping it to size — and state what data it requires that the model doesn't currently ingest.
5. **Additional evaluation targets** (these are the highest-value asks — do not skip):
   - **Input-layer stress test (the real risk surface).** The one documented loss driver was a *wrong human/LLM input* (a mis-entered "% since last earnings" flipped a verdict), not a logic error. Evaluate the un-reproducible judgment layer: where should input validation live, and how do you catch garbage-in before it becomes a trade?
   - **Sign-edge vs. EV-edge.** A directional-*sign* model is blind to payoff skew. Determine whether this architecture can serve the priced-in/sell-the-news/comeback goals without a joint sign-plus-skew or EV model.
   - **Statistical validity at tiny n / anti-confirmation-bias.** With ~n=3 outcomes, separate "disciplined design" from "unvalidated design." Define the **minimum evidence bar** (n, accuracy, by conviction tier) before this model sizes real capital, and how to avoid overfitting rule changes to 2-3 vivid recent trades.
   - **Honest benchmark & net-of-cost viability.** The naive pre-earnings benchmark is ~50% directional / the ATM straddle. Does the model plausibly beat that **after** slippage on a 20%-gap name, bid/ask, borrow cost (shorts), and taxes? State the benchmark and test against it.
   - **Value-trap / survivorship stress.** The comeback thesis is validated on winners. Test it against beaten-down names that *kept falling* (value traps identical ex-ante). Does the KPI/velocity filter actually separate them, or is it fit to survivors?
   - **Capacity & effort.** Gap-at-risk sizing yields tiny positions (~$18k on $500k for a 21%-vol name). Is the strategy worth the operational effort at this size? How many concurrent, uncorrelated trades are needed for the edge to matter, and does the universe support that?
   - **Equity-only constraint.** Given the vol-centric philosophy, is forbidding options a fatal limitation? What is lost, and what defined-risk expressions would better capture the intended edge?
6. **Data & source validation** — reliability, timeliness, bias, and coverage of the judgment inputs and market data; weakest dependencies.
7. **Alternative evaluation methods** — backtesting design (with pre-registration and beta-stripped idio-sign scoring), regime slicing, stress tests (extreme vol, data gaps, corporate actions), sensitivity analysis (how a one-bucket input change flips the verdict), and metrics beyond win rate (idio-sign accuracy, EV, drawdown, Sharpe-like, per-component attribution).
8. **Sustainability & adaptability** — degradation triggers (regime shift, source change, threshold overfit), detection (the model's kill switches — critique them), and the governance path (WATCH -> 2 holdouts -> sign-off; outcome-equivalence plumbing/logic boundary; parameter ceiling). Is this adaptation regime sound, too slow, or too permissive?

## 5. Output Format

Produce a structured, thorough, standalone report:
1. **Executive summary** — verdict (fundamentally sound / partially sound / flawed), top strengths, top weaknesses, top 3-5 prioritized recommendations.
2. **End-to-end pipeline reconstruction** — with missing/ambiguous steps named.
3. **Logical & statistical critique** — assumptions, formulas, signal construction, aggregation, thresholds; flaws, circularity, overfit.
4. **Decision-framework evaluation** — BUY/SHORT/NO TRADE/INCOMPLETE; alignment with philosophy; the optimal-BUY, comeback-BUY, short, and NO-TRADE logics separately.
5. **Risk & calculated-risk framework** — current handling + a concrete proposed framework with formulas and thresholds.
6. **Conviction & calibration analysis** — per S3.G, with concrete fixes.
7. **Input-layer, sign-vs-EV, tiny-n, benchmark, value-trap, capacity, and equity-only findings** — per S4.5.
8. **Data & source assessment.**
9. **Alternative evaluation methods** — backtests, stress tests, metrics.
10. **Sustainability & adaptability.**
11. **Final prioritized recommendations** — specific changes to logic, formulas, risk, conviction, and operations, ranked by impact and by whether each is a small-n-safe tweak or requires a full holdout-validated change.

Use tables where they clarify comparisons. Be thorough; do not over-summarize.

## 6. Tone

Skeptical but constructive. Do not assume the model is correct — challenge it. Use your own domain expertise to find weaknesses and propose concrete, implementable improvements. Anchor everything to the actual logic in the attached disclosure, and be explicit about what is implemented versus what the owner merely wants.
