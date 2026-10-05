# CHARTER — why this experiment exists, what counts as getting better, where the edge is

> Written 2026-09-21 at Jacob's request, after web research (sources at the end). **Read this before
> choosing between options or proposing an improvement.** The rules in CLAUDE.md say what must never
> happen. This file says what the experiment is *for*, and so which way to push.
>
> Revise it at every season end. Never in the middle of a measurement, and never to justify a result.

## 1. Purpose

**To find out, honestly, whether any repeatable edge exists in buying stocks just before their
earnings print, and for which kinds of business. Then to hand that knowledge, with its uncertainty
attached, to the portfolio model.**

- It is a **measuring instrument first** and a trading system second. Its product is *knowledge that
  can be trusted*: what works, what doesn't, how big, how sure. A negative result, well measured, is a
  full success. It stops real money following a false belief.
- **The question it answers:** does selection, by a mechanical rule (T1) or by AI judgment (T2), beat
  buying everything (T0)? Buy-everything is the opponent, not 50%.

## 2. The end goal, and the picture one year from now (Sep 2027)

**End goal:** a small set of **confirmed, versioned decision aids**. Each has:
- a live, timestamped, independently verifiable track record
- a known effect size
- known conditions: which clusters and stages, and when it works
- a calibrated probability per event

The portfolio model can lean on these without trusting anyone's word.

**Sep 2027, if things go right:**
- **Coverage.** Pilot, plus Seasons A–D (Oct–Nov 2026, Jan–Feb, Apr–May and Jul–Aug 2027): roughly
  400–600 graded events, pooled under pre-registered versions. At 400 events a ~6-point lift is
  detectable (D005 §7); at one season it takes ~12.
- **A verdict on T2.** Does AI judgment beat buy-everything and the rule, and are its probabilities
  calibrated (Brier skill, confidence test)? This will be one of the first clean, post-training-cutoff
  records of an LLM's pre-earnings judgment.
- **Rule v1.** Confirmed or rejected on data it never saw.
- **Cluster and stage priors.** For example: "mature consumer names clearing a 4% implied move: base
  rate X, what moved them was Y". Descriptive until each clears the rule 7 minimum.
- **An audit trail an outsider can verify alone:** hashes, RFC 3161 timestamps, tool-call logs.

**If things go "wrong":** a well-powered "no edge found", which is itself worth money. The failure to
avoid is **"we don't know"**: too few events, a broken record, or changed rules.

## 3. Philosophy — what marks this experiment

1. **Measure before believing.** A pattern is a candidate until it holds on data it wasn't found in.
2. **The null is buy-everything.** A rising market makes everyone look smart.
3. **Freeze, then look.** Every decision is fixed and timestamped before the price that grades it
   exists.
4. **Negative knowledge is a product.** "This doesn't work, and here is how sure we are" gets reported
   with the same care as a win.
5. **Small honest edges beat large fake ones.** Beware anything that looks too good. It is usually
   leakage, overfitting or luck. Most published edges shrink after publication.
6. **Change by versioning, never by editing.** An improvement is a new version with its own clock. The
   old one keeps being scored beside it.
7. **Never comfortable.** A reliable, safe system is the floor, not the goal. Each season must end with
   something tested that could make the next one better (§6).
8. **Explore in the shadows.** New ideas run as **shadow tracks**: registered, frozen and graded like
   the rest, labelled exploratory, and never allowed to touch the scored tracks until confirmed.

## 4. The edge — where this experiment can beat what is out there

What the research shows about the field, and what we do instead:

| weakness out there | what we do |
|---|---|
| **Most "AI beats the market" evidence is contaminated.** LLMs memorise the future they are tested on: look-ahead survives anonymisation (Glasserman & Lin), Llama 2 "predicts" Covid in 2019 calls (Sarkar & Vafa), predictive power collapses after the training cutoff (Gao, Jiang & Yan). The best-known "GPT-4 beats analysts at earnings" paper (Kim, Muhn & Nikolaev 2024) was withdrawn in Feb 2025 | **Forward-only, post-cutoff, pre-registered.** Every T2 decision is made live, after the model's training cutoff, frozen and timestamped before the print. Our T2 record cannot be memorised. That is rare, and it is the core asset |
| Backtests re-run until they look good | Frozen rules, counted tests (BH, Holm), fixed verdict wording, power disclosed |
| Big funds need capacity | We don't. Mid-caps ($2–10B) with thin coverage, where small, non-scalable edges survive, are fair game |
| One model for all stocks | **Business-type conditioning** (cluster × stage, partial pooling). The same factor can mean opposite things for a hypergrowth name and a mature one |
| Options data costs money historically | **We capture every chain forward, free.** Within a year we own a point-in-time earnings-options dataset nobody sold us: implied move, skew, term structure, open interest |
| Straddles overprice earnings moves on average (about −8% per announcement; Xing & co.) | Implied move is a *measured* factor. We test whether it says anything about **direction** once its known size bias is removed (two-expiry event move, concave IV curves) |
| LLM forecasts are badly calibrated when used once | **Calibration is scored** (Brier, log loss, calibration table). Ensembles and outside-view anchoring are candidate improvements (§6); the forecasting literature shows they help (Halawi et al. 2024; Schoenegger et al. 2024) |

**The honest limit:** the edge is in *method*, not yet in *signal*. Whether a signal exists is exactly
what we are measuring.

## 5. Role in the ecosystem — a one-way valve to the portfolio model

- This experiment is the **research lab upstream** of Jacob's portfolio model. Knowledge flows
  **one way: experiment → portfolio.** The experiment never reads holdings (rule 9). If it did, wanting
  an answer would bend the answer.
- **What it exports**, and only once a finding clears its status:

  | product | what it is | allowed from |
  |---|---|---|
  | **Event signal** | for each upcoming print: T2's calibrated probability, and the T1 rule's call once rule v1 is confirmed | only after the track's lift is confirmed; until then, marked exploratory |
  | **Priors per business type** | base rate, typical move size, what historically decided the move | descriptive; always with n and "insufficient" where it applies |
  | **Negative knowledge** | which factors and ideas were tested and failed, and how sure we are | as soon as measured — it prevents overconfidence |
  | **Risk context** | expected move size (implied, and the event-specific part), days to print, whether this print is a coin flip | any time; it is measurement, not prediction |

- **The export format** (when the first finding clears): a versioned `exports/findings_<date>.md` with
  effect sizes, intervals, sample sizes and status. The portfolio side reads it; nothing is read back.

## 6. What "improving" means — and how to push it

**An improvement raises one of these. Anything else is decoration.**

1. **Power:** more graded, clean events per season. This is the binding constraint (both external
   evaluators agreed); nothing else matters if the sample cannot answer the question.
2. **Truthfulness:** fewer ways for the record to be wrong — leakage, voids, missing T2, disputes,
   unverified timing.
3. **Signal:** lift and return lift over T0 on data the idea never saw.
4. **Calibration:** T2's Brier skill and confidence-test slope.
5. **Speed to verdict:** time from idea to a trustworthy answer.

**Health numbers**, reported each season:
- missed windows = 0
- T2 missing < 5%
- VOID < 5%
- `single_source` = 0 once the key is live
- fence breaches = 0

**Research cadence (never comfortable):** at every season end, and whenever stuck:
- Search papers, GitHub and products for what others do better.
- Write down at least three candidate improvements, each with expected value, cost and risk.
- Test at least one as a shadow track in the next season.
- Record what was tried and what happened.

**Improvement backlog** — each becomes a new version or a registered shadow track, never an edit:

| # | idea | why (evidence) | lever | status |
|---|---|---|---|---|
| I1 | **Grow the sample**: widen the D002 allowlist (e.g. Consumer Electronics, Scientific & Technical Instruments, Diagnostics) and/or lower the implied-move gate to 3% | power is the binding constraint; one season detects only ~12 pts | 1 | **Decision for Jacob before the Season B screen**, using Season A's event *count* (not outcomes) |
| I2 | **T2 ensemble shadow track (T2e):** 3–5 independent runs or models, trimmed mean | ensembles rival human crowds and improve calibration (Schoenegger 2024; Halawi 2024) | 4, 3 | **done 2026-10-05 as shadows (D004 v4): T2G = Gemini 3.8 Flash (free tier), T2E = mean(T2, T2G)** |
| I3 | **Outside view first:** give T2 the stock's own past earnings reactions and the season base rate before any story | superforecasting practice; LLMs improve when shown a base rate (+17–28% in Schoenegger) | 4 | **done: D004 v3 change 4** (frozen 2026-09-29) |
| I4 | **Structured bull/bear debate inside T2** (multi-role agents) | TradingAgents-style role debate; our three theses are a start | 3, 4 | shadow candidate |
| I5 | **Implied move vs own history (B3), concave IV curve** as factors | concave IV predicts larger moves (Review of Finance 2025); the straddle premium is documented | 3 | add to factors before rule v0 |
| I6 | **Point-in-time history store** for the rule v0 study (Qlib-style PIT data) | D005 v2 §7 requires point-in-time factors | 2, 3 | **done: `pipeline/history_factors.py`**, SEC `filed` dates + bar calendar (D006) |
| I7 | **Leak test for T2:** a date-only recall probe on each event (Lookahead Propensity) | Gao, Jiang & Yan 2025 | 2 | **done: D004 v3 change 5** — `t2.leak_probe` on every Season A event |
| I8 | **Rate-limit resilience:** API-key fallback for the AI step | the account hit its session limit on 2026-09-21; **on 2026-10-02 the subscription's WEEKLY limit was exhausted (HTTP 429, every model) by Jacob's own chats**, so T2 shares a budget with them | 2 | **solved without paying, 2026-10-05: D004 v4** (code-built dossier + one isolated call, ~38× cheaper, overnight queue). The pilot's agentic API-key fallback stays wired but inert |
| I9 | **OpenBB** as a second data layer for estimates and calendars | one interface to many free providers; a second source for fields where we have one | 2 | probe when a factor needs it |
| I10 | **Shadow tracks for power** (D009): T0-wide, market-wide (~1,300 events/season), exact short straddle | entry sessions, not events, bind power above ~25 events/session; the gated track alone has expected t ~0.8 a season | 1, 5 | **done: D009 v1** (2026-10-02) |
| I11 | **Year-round market-wide shadow**: grade off-season sessions too | ~60% of off-season weekdays carry a print >= $2B; ~+25% information a year | 1 | candidate for D009 v2 (before Season B) |
| I12 | **Gate 2 on a powered sample**: D008's H-S0 on gated events has expected t ~1.1 after A+B | power analysis 2026-10-02 | 1 | decide at Gate 1 whether D008 v2 pools SH-W/SH-M evidence (registered before Season B) |

## 7. How this charter decides things — worked example

**The payroll rule for D003 v2.** Two options: an SEC-SIC filter, or naming ADP and PAYX.
- **Power (§6.1):** the SIC filter would also remove AKAM, FICO, ROP, AFRM, HOOD and COIN. That is
  fewer events, lost for no reason D002 gives.
- **Truthfulness (§6.2):** SIC codes are stale and misassign firms. A mechanical-looking rule that
  measures the wrong thing is worse than an explicit, documented judgment.
- **Philosophy (§3.6, rule 8):** naming two firms is judgment. But D002's own text says "payroll", and
  D002 already names MSTR. The judgment is written down, fixed before the calendar, and cannot drift.

→ **Name ADP and PAYX.** The charter picks the option that keeps the sample large and honest.

## Sources consulted 2026-09-21

- [Glasserman & Lin, look-ahead bias in GPT sentiment](https://arxiv.org/abs/2309.17322) ·
  [Sarkar & Vafa, lookahead bias in pretrained LMs](https://www.semanticscholar.org/paper/Lookahead-Bias-in-Pretrained-Language-Models-Sarkar-Vafa/e5097ccd4477c454e0df52945cef4ba74d255b91) ·
  [Gao, Jiang & Yan, detecting lookahead bias](https://arxiv.org/abs/2512.23847) ·
  [Kelly et al., point-in-time language models (NBER)](https://www.nber.org/system/files/working_papers/w35247/w35247.pdf)
- [Kim, Muhn & Nikolaev, financial statement analysis with LLMs (withdrawn Feb 2025)](https://arxiv.org/abs/2407.17866)
- [Halawi et al. 2024, approaching human-level forecasting](https://arxiv.org/abs/2402.18563) ·
  [Schoenegger et al. 2024, wisdom of the silicon crowd](https://www.science.org/doi/10.1126/sciadv.adp1528) ·
  [Pitfalls in evaluating LM forecasters](https://arxiv.org/pdf/2506.00723)
- [Xing & co., straddles around earnings announcements](https://www.ruf.rice.edu/~yxing/straddle_201305_03.pdf) ·
  [Dubinsky et al., option pricing of earnings announcement risk](https://www.stern.nyu.edu/sites/default/files/assets/documents/NYU%20conference%20Johannes%20final.pdf) ·
  [Pricing event risk: concave IV curves, Review of Finance](https://academic.oup.com/rof/article/29/4/963/8079062)
- [LLM embeddings of earnings calls, out-of-sample (SSRN 2026)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6510327)
- Tools: [TradingAgents](https://github.com/tauricresearch/tradingagents) ·
  [Microsoft Qlib](https://github.com/microsoft/qlib) · [OpenBB](https://github.com/OpenBB-finance/OpenBB)
