# RESEARCH PLAN — from experiment to real money

> Written 2026-09-30. `CHARTER.md` says *why* and what counts as improving. This file says **where we
> are going, by when, and what must be true before real money goes in**. Treat it as a PhD programme:
> - Jacob is the funder and the committee: he decides, fetches and pays.
> - The research earns its way through pre-registered gates.
> - "Graduation" is a strategy we are entitled to trust with money.
>
> Revise it at each gate, never mid-season.

## 1. The end in mind

**Graduation = a rules-based, automated earnings strategy running with real money.**
- It has a live, timestamped, pre-registered record that beat its benchmark after costs, in at least
  two seasons it was never fitted on.
- It has a sizing rule and a kill switch fixed before the first dollar.

**Or, just as final:** a well-measured "no edge worth trading", plus the negative knowledge that stops
the portfolio chasing one. Either way, no more "we don't know".

## 2. What we know on 2026-09-30

History, 2023-09 → 2026-09: 2,771 prints, 329 companies, the D001 trade (entry open → first open after
the print).

| finding | number | status |
|---|---|---|
| Buying every eligible print wins | 54.0% of events; mean **+0.85%**; median +0.75% | real in history: clustered t 3.6 by entry date |
| Over the S&P 500 in the same window | **+0.73%** per event | not market beta |
| After a 0.2% round-trip cost | +0.65% | survives costs |
| Where it lives | **+0.79% overnight reaction**, ~0 in the session before | an earnings effect, not a run-up |
| Payoff shape | average win +7.5%, average loss −6.9% | a small tilt on a big coin |
| Regime | 4 of 13 quarters negative (2023Q4 −0.5%, 2025Q1 −0.4%, 2025Q4 −0.2%) | candidate conditioner |
| Busy vs quiet days | +1.02% on dates with ≥ 10 prints; +0.45% otherwise | candidate |
| Clusters (excess over the S&P) | hardware +1.3%, consumer +1.2%, software +0.8%, semis +0.3%, **healthcare −0.5%** | candidates |
| Selection by 10 free factors (T1 rule v0) | lift −0.2 / −0.7 pts | **failed** |

**The uncomfortable conclusion.** The most likely graduate is **not clever stock-picking**. It is
**harvesting the earnings premium broadly and intelligently**: buy many prints, sized by risk, and
skip the conditions where the premium disappears. Selection (T1, new signals, options, AI) has to earn
its way on top of that base.

**The caveats that stop us trading it today:**
- survivorship: today's companies only
- no option gate in history
- a bull market (2023–26)
- the live, post-publication premium is unmeasured

## 3. Research questions (the chapters)

| # | question | measured by | proven when |
|---|---|---|---|
| RQ1 | Is the earnings premium real and harvestable **live, after costs**, in our universe? | T0, plus a T0-wide shadow (§5) | one-sided p < 0.05 on live data, pooled over the confirmatory seasons |
| RQ2 | **When** does it vanish (regime, cluster, season timing, busy days)? | D007 exploration on history, then confirmatory live | holds out of sample (rule 6) |
| RQ3 | Can **selection** beat buying everything? | T1, D007 signals | lift > 0 and return lift ≥ 0, Holm-corrected (D005 v2) |
| RQ4 | Do **option prices** carry direction, and when is the move overpriced? | live chains (and history, if bought, §7) | same bar |
| RQ5 | Does a post-cutoff **AI** add information, and is it calibrated? | T2, its confidence test, Brier score | same bar; the calibration slope reported |
| RQ6 | How do we **size and execute**? | paper trades at the official open; implied-move risk sizing | fills within 15 bp of the official open |

## 4. Timeline and gates

| phase | dates | what happens | gate at the end |
|---|---|---|---|
| **0. Finish the pilot** | now → Oct 9 | NKE, PENG, LEVI, APLD live; pipeline proven | — |
| **1. Prepare Season A** | now → Oct 11 | D007 exploration batch pre-registered, then run on history · D008 graduation criteria frozen · live option features + straddle shadow + T0-wide shadow added | **before any Season A outcome exists** |
| **2. Season A** | Oct 12 → Nov 20 | exploratory, live; ~150 gated + ~300 shadow events | **Gate 1 (early Dec):** Season A report; register Season B's confirmatory family (T0 premium, the best conditioner, T2 confidence, the best option signal) |
| **3. Season B** | Jan → Feb 2027 | confirmatory, plus **paper trading** of the candidate strategy with real order types | **Gate 2, the qualifying exam (Mar 2027):** pre-registered verdict, pooled A+B |
| **4. Season C** | Apr → May 2027 | if Gate 2 passes: **small real money**, same rules, kill switch live | **Gate 3:** did live money match paper and research? |
| **5. Season D** | Jul → Aug 2027 | scale decision | **Defense (Sep 2027):** final report; export to the portfolio model (CHARTER §5) |

**Power sets the pace.**
- History's per-event Sharpe is 0.087. Confirming the premium live at t ≈ 2 needs ~600–850 events.
- At ~150 gated events a season that is four seasons. **Hence the T0-wide shadow (§5)**, which roughly
  doubles live n at no cost.

## 5. Work streams and what each needs

| stream | next concrete step | cost |
|---|---|---|
| **T0-wide shadow** | grade every S1 candidate with a confirmed date, gate or no gate, as a secondary track. Doubles RQ1's power | free |
| **D007 exploration** | pre-register, then test on history: FINRA 5-day short-sale pressure · peer read-through (same-cluster reactions in the prior 10 days) · regime (VIX level/trend, S&P 20-day) · Wikipedia attention spike · early vs late reporter · busy-day effect · semis mechanism. BH + t > 3; survivors become Season B hypotheses | free |
| **Options** | at every snapshot, record the implied/realised volatility ratio, term-structure slope, call−put implied-volatility spread, skew, and the **short-straddle shadow P&L** (implied move vs realised move) | free (forward) or ~$40 (history, §7) |
| **T2 (AI)** | D004 v3 is live: base-rate prior, leak probe. Next: a T2 ensemble shadow (CHARTER I2), once cost is known | model usage |
| **Execution** | a paper-trading ledger: market-on-open buy on the entry day, market-on-open sell at exit A; equal-risk sizing = risk budget ÷ implied move | free |
| **Infrastructure** | cloud trigger (done), health numbers every season: missed windows 0 · T2 missing < 5% · VOID < 5% | credits |

## 6. Graduation criteria — draft of D008 (frozen before any Season A outcome; Jacob sets the money limits)

**To pass Gate 2 and put real money in**, all of these, pre-registered:
1. **Evidence:**
   - at least 2 live seasons, at least 250 graded events and at least 40 entry dates (T0 or T0-wide)
   - the strategy's live mean return after a 0.2% round-trip cost is > 0, one-sided p < 0.05, clustered
     by entry date
   - the same sign as history, and not negative in both seasons
2. **Selection layers** (a filter, T1, a signal, T2) enter the strategy only if each passes its own
   Holm-corrected confirmatory test. Otherwise the strategy is the plain premium harvest.
3. **Execution:** paper fills within a median of 15 bp of the official open over at least 50 trades.
4. **Risk:**
   - The worst simulated season under the sizing rule must stay within Jacob's pre-set loss limit.
   - The per-event risk budget is fixed in advance.
5. **Kill switch** (live money), any one of:
   - live P&L more than 2 standard deviations below expectation after 50 trades
   - any trade not frozen before the open
   - two health numbers breached in one season

   Stop, report, go back to paper.

## 7. What the funder is asked for (Jacob)

| ask | why | when |
|---|---|---|
| **~$40 for one month of historical option chains** (ThetaData; pricing to be re-checked) | turns RQ4 from "wait a year" into a backtest of 3 years of pre-earnings chains for our universe; the single highest-leverage spend | before Gate 1 |
| **A paper-trading account that supports market-on-open orders** (e.g. Interactive Brokers paper) | RQ6: real order mechanics before real money | before Season B (Jan 2027) |
| **The real-money sleeve and loss limit** | D008 must fix them before the first live trade | before Gate 2 (Mar 2027) |
| **Widen the universe? (CHARTER I1)** | power | before the Season B screen |
| **Ideas and attention** | each idea becomes a registered test, never an ad-hoc look | always |

## 8. Risks to the programme, and the answer to each

| risk | answer |
|---|---|
| Too few events to decide | T0-wide shadow; allowlist decision; pool seasons |
| The premium was a 2023–26 bull-market artifact | regime conditioner (D007); live seasons across conditions; the kill switch |
| Pattern-hunting (many ideas, chance hits) | every batch pre-registered; BH + t > 3; confirmation only out of sample |
| AI look-ahead | T2 only live, after its cutoff; leak probe; no AI scoring of historical text |
| Infrastructure failure loses events | cloud trigger + laptop backup; per-event T2 jobs; health numbers |
| Data vendors break (yfinance, IR sites) | second sources in the pipeline; failures recorded, never filled |
| Real-money behaviour differs from paper | Gate 3 compares them; small sleeve first |
