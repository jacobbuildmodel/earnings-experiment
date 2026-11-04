# Committee Q&A for PRE: Stage 1 review, 2026-11-03

> From the independent investment committee (a separate Claude session working from PRE's files, outside PRE). The
> report is `REPORT.md` in this folder. **Jacob forwards this file to PRE.** Nobody messaged PRE's sessions directly.
>
> **How to answer:** one round, in one fresh `pre earnings model` chat, ≤ 150k tokens. Write the answers into
> `PRE_QA_answers.md` beside this file. **Every answer cites a file, commit or registry section.** An answer with
> no citation counts as "no evidence". Don't run new analysis on Season A outcomes to answer: D017 §4 and §5
> still bind (no per-name outcomes, no T2-confidence-vs-outcome view before Gate 1). If a question can only be
> answered by breaking that firewall, say so and stop. That is a valid answer.

## Part A — already answered from PRE's own files (no reply needed unless PRE disputes one)

| # | question (mandate §12) | answer from the record | source |
|---|---|---|---|
| 1 | Strongest, most repeatable source of advantage? | **None demonstrated.** The one candidate is the broad earnings premium (buy-all), not selection. History: +0.65% net per print (survivor sample). Live: −1.50% net (SH-W, n 104, correct cut; Stage 1 printed −0.76% on a stale grade, see P0). PRE's own words: "the edge is in *method*, not yet in *signal*." | CHARTER §4; D006; stage1_2026-10-30.md |
| 2 | Factors with measured incremental power? | **None.** No D006 factor cleared t > 3; R-LIT failed validation (−0.7 pts); D007's 20 signals: none beat buy-all; the IV spread is no selector (D010 v2); no first-hour pattern validated (D014). | HYPOTHESES §3 |
| 3 | Which are hypotheses, not signals? | All 10 confirmatory tests (H-S0 … H-C1) are untested hypotheses. H-VOL, H-RU, H-XT and H-C1 were found on history, so they are candidates (rule 6). | HYPOTHESES §1 |
| 4 | Evidence that high-conviction trades beat a baseline? | **None.** v2 has no conviction tier; T2's 9 BUYs (−1.64%) vs all (−2.83%) is INSUFFICIENT. PRE v1, the conviction-based forecaster: 27 blind forecasts, 14 right (51.9%, p = 1.00). Its largest win (AEHR, 2026-07-14, +36% at the open) was a **LOW**-conviction BUY. | stage1 P3; archive `doctrine_pre.md`, `PRE/ledger.jsonl` |
| 7 | Earnings surprises, reactions or instrument returns? | **Layer 1 (EPS or revenue surprise) is not predicted or recorded at all.** Layer 2: T2 predicts P(up at exit A), INSUFFICIENT. Layer 3: equity buy-all is negative live so far; options lose after spreads on both sides. | D004 v4; stage1 P2–P4; D010 |
| 8 | Profit left after spreads, slippage and vol crush? | Equity: **none.** Signed paper slippage (committee recompute of the paper ledger): buys −13 bp, sells at the post-print open **+105 bp** (20 of 23 adverse), round trip **+92 bp** against the 0.20% assumed. Options: long straddle +0.82% at mid becomes −1.33% at the fill; short iron fly −1.34% at mid, −4.76% at the fill. History: short −3.22%, long −4.03% per $1 of spot at bid/ask. | stage1 P4; D010 v1 |
| 9 | Independent high-conviction trades a year? | **Zero** with demonstrated edge. Gated PASS events: 8 of 31 in the D016 audit (26%); Season A runs ~6 weeks a quarter. Events cluster heavily: 84 SH-W events fell on 8 sessions. | D016; stage1 |
| 10 | Return per unit of capital at risk? | History: +0.65% net per $1 of notional, against a 9.8% per-event SD (per-event Sharpe 0.066 net). Live: negative. | D006; committee recompute |
| 11 | Worst plausible loss distribution? | History, one print held: p10 −10.2%, p5 −14.8%, p1 −24.2%, worst −48.3%; 1 print in 10 loses ≥ 10%. Short options: worst −41.9% of spot, so above −100% of margin. | committee recompute of `analysis/history/legs_exploratory.json`; D010 v1 |
| 15 | What evidence would end the initiative? | **No rule ends the project.** D017 §5 and D008 only withhold money ("no new money", "no real money"). Nothing says "stop researching". The committee report fixes one. | D017 §5; D008 §3 |

## Part B — open questions, in priority order

Each question says what counts as an answer.

**P0. The Stage 1 data cut.** `stage1.py` (run Mon 11-02 07:28 ET) read the shadow grade committed Fri 10-30 21:52 ET
(`c2dc357`). It omitted the events whose exit-A open was Fri 10-30, which are inside D017 §2's cut: `graded.json` holds
129 graded 10-29 prints at `c2dc357` and 227 at `4d9affc`. The committee's corrected read: SH-W n 104, 9 sessions,
net −1.50%; S0 n 21, −5.34%. *Answer:* confirm or refute from the files, and commit a Stage 1 addendum on the full cut
beside the first output (D017 §2 allows a bug-fix commit; the first output is never replaced).

**P1. The survivor problem in the only positive evidence.** The D006 universe was chosen by *today's* market cap
(`analysis/history/universe.json`: "2026-09-28 market data", ≥ $2B). Firms that shrank below $2B or delisted after bad
prints are missing. That is selection on the outcome, not just "today's listed companies". **Estimate the bias.** For
example, re-run D006's T0 mean on a universe chosen by market cap as of 2023-09-01 (EDGAR shares × the as-traded close
then), keeping delisted names that have prices. *Answer:* the premium on that universe, or "not possible with free data",
and why.

**P2. Why should the premium hold live when three independent reads say it may not?** (a) SH-M, survivor-free and
market-wide: raw −0.08% (n 596, 13 sessions). (b) An independent lab study, 2019–2026 on multi-week holds: a print inside the hold
adds variance in both tails, not mean return (+0.045%, CI [−0.24, +0.34]). (c) History by year: 2023 −0.57%, 2025
+0.43%; the top 5% of events carry 141% of the total return. *Answer:* the specific mechanism and the data that
reconcile these, or the concession that history's +0.65% is an upper bound.

**P3. Executability for Jacob.** His broker (moomoo SG) has no market-on-open orders, charges US$0.99 per order and
penalises first-minute market orders. D001's trade is open-to-open. *Answer:* (a) the live SH-W and SH-M means on a
moomoo-executable definition: close before the print (MOC) → close of the reaction day (MOC, exit B), using only
already-captured prices, registered as a new secondary before computing (the shadow files carry no daily closes, so
say what capture this needs); (b) confirm the committee's signed slippage (+92 bp a round trip, almost all on the sell
side), and whether a limit or MOC exit would avoid it.

**P4. Power vs Jacob's horizon.** RESEARCH_PLAN says t ≈ 2 needs ~600–850 events. On SH-M (~1,300 a season), when is
that reached? On the gated S0 (~30–60 PASS a season), when? *Answer:* dates, from counts only.

**P5. What would you remove?** Name the components to shut down that cost allowance or laptop time and cannot move
a Gate 2 verdict: paper options F and L, the T2G/T2R/T2O/T2M/T2E shadows, the D018 batch, C1. Give the weekly allowance
share each uses. *Answer:* a table: component · allowance or hours a week · the Gate 2 criterion it serves (or "none").

**P6. Cost per useful answer.** From the routine logs and `ops/token_study.py`: tokens (or $-equivalent) per week since
Season A started, split into code steps, cloud T2s and laptop chats. *Answer:* the table, and the cost per graded
gated event.

**P7. Layer 1 is missing.** PRE never records a forecast of the EPS or revenue surprise, so it cannot tell "wrong
about the numbers" from "wrong about the reaction". *Answer:* is that deliberate? If not, the cheapest way to capture
consensus vs actual EPS and revenue per event (a captured fact, not a hypothesis).

**P8. Failed trades and largest errors.** *Answer only after Gate 1, when D017 §4 allows per-name views:* the three
worst T2 BUYs and the three best T2 NO_BUYs, with the dossier line that drove each decision and what in the frozen
snapshot would have changed it.

**P9. Opportunities rejected.** *Counts only, now:* gated-out events by failing check (D016 style) for the full Season A.
*After Gate 1:* the gated-out events' mean against S0's (D008 §2 already reports it as a secondary).

**P10. Data that would materially improve prediction.** One item, with its cost and the Gate 2 criterion it would move.
"More factors" is not an answer: every factor batch so far has failed.

## Part C — the specific requests in the mandate

| request | status |
|---|---|
| Three strongest historical or proposed opportunities | v2: none can be named before Gate 1 without per-name outcomes (D017 §4). v1, from the archive: AEHR 2026-07-14 (+36% at the open, a LOW-conviction BUY), TEM 2026-07-30 (+4.4%), CTSH 2026-07-29 (+4.0%) |
| Three weakest | v1: RBLX 2026-07-30 BUY (−20.1% at the open), AMKR 2026-07-27 BUY (−14.5%), NFLX 2026-07-16 BUY (−11.9%). *The v1 ledger has re-scored duplicate rows, so these are examples, not a recount.* |
| Three incorrect high-conviction calls | v1 closed before a conviction tier could be scored. Its "inverted conviction gradient" was noise on cells of n = 2 and n = 6 (`doctrine_pre.md`). v2 has none. |
| Attractive opportunities the model rejected | P9 |
| What would have changed the decisions | P8 (after Gate 1) |

## Part D — how the committee will assess the answers

- One round. An unsupported explanation is scored as no answer. A claim that moves the decision must cite a file or commit.
- **Answers that would change the decision:** P1 showing the survivor bias is small (< 0.2 pts) **and** P3(a) showing the
  moomoo-executable mean positive on ≥ 10 sessions. Together they would move REFRAME towards a fuller CONTINUE.
- **Answers that would harden it towards TERMINATE:** P1 showing a bias near the full premium, or P3(a) negative. P3(b)
  is already met on the committee's recompute: the signed slippage is +92 bp, not 20.
