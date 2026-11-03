# PRE's answers to the Stage 1 committee — one round, 2026-11-03

> Answered by a fresh `pre earnings model` chat, Tue 2026-11-03 10:45–11:30 ET, from `PRE_QA.md` (`2b95c1c`).
> check.py PASS at start. Held: D017 §4 (no per-name outcome, no T2-confidence-vs-outcome view), rule 9 (DRIVE not read),
> rule 10 (the PRE v1 archive not read), no hash-listed file edited. No new registry version, no track stopped: those are
> the committee's §12 recommendations to Jacob, and the funding call is his. New computation was limited to P0's addendum,
> counts, execution (signed slippage) and history (`analysis/history/`); no Season A return was computed beyond P0.

## Summary

| # | verdict | one line | evidence |
|---|---|---|---|
| P0 | **CONFIRMED** (wording disputed) | The Stage 1 run missed the 10-30 exits. Not a stale pull: no grade of them existed yet. Fixed; full-cut addendum written. | `4383102`, `a6f7cc6`, `outcomes/reports/stage1_2026-10-30_r2.md` + `_r2_NOTE.md` |
| P1 | **CANNOT ANSWER** (the asked re-run); partial evidence | Not possible with free data for delisted names; the still-listed half is possible. The premium is smallest in the oldest, most survivor-filtered events. | D006 §2; `analysis/history/legs_exploratory.json` |
| P2 | **CONFIRMED** (concession) | History's +0.65% is an upper bound. PRE has no mechanism evidence that reconciles the live reads. (b) cannot be checked: DRIVE is fenced. | D006 §2; r2 P2; CLAUDE.md rule 9 |
| P3a | **CANNOT ANSWER** this round | Needs registration first (a new version: Jacob's call). No capture is lost by waiting: closes are retrievable later. | rule 5; D017 §5; STATE standing rules |
| P3b | **CONFIRMED** | Buys −13 bp, sells +105 bp (20 of 23 adverse), round trip +91 bp. D008 §3's execution bar (≤ 15 bp) is already failed. | `paper/ledger.json`; r2 P4; D008 §3 #4 |
| P4 | answered from counts | SH-M passed 600 graded by 10-30. Gated S0: 250 not before Season C–D (mid-2027); 600 ≈ 2028; 850 ≈ 2029. **D008 Gate 2 #1 cannot be met in Mar 2027.** | gate audit 11-03; D008 §3; RESEARCH_PLAN |
| P5 | partial | Table below. Only per-decision cost and routine counts are recorded, no weekly share per component. | `ops/capacity_peak_2026-11.md` §3; `t2*.json` |
| P6 | **CANNOT ANSWER** (no weekly ledger) | Recorded AI cost per gated event ≈ $0.41 API-equivalent; laptop chats unattributed. | `t2*.json`; `ops/token_efficiency_2026-10.md` |
| P7 | **CONFIRMED** (partly captured) | Pre-print EPS consensus is frozen; the actual and revenue are not, and no surprise is forecast. Not a recorded choice. | `pipeline/factors.py:66-97`; FRAMEWORK (EPS basis rule) |
| P8 | after Gate 1 | Needs per-name outcomes and T2's reasoning against outcomes. | D017 §4 |
| P9 | counts now; mean after Gate 1 | 143 gated with a chain: 32 PASS; `wide_spread` fails 106. | `analysis/d016/gate_audit_seasonA_interim_2026-11-03.md` |
| P10 | answered | No predictor has evidence. One item: Layer-1 actuals, $0. It moves no Gate 2 criterion. | HYPOTHESES §3; P7 |

## Part A — confirmations and disputes

- **A1 (live −1.50%)**: CONFIRMED by PRE's own code, `stage1_2026-10-30_r2.md`. Wording: "stale grade" is not accurate (see P0).
- **A4 and Part C (PRE v1 ledger, AEHR, RBLX…)**: neither confirmed nor disputed. Rule 10 fences `archive/PRE_v1_closed/`.
- **A8 (slippage)**: CONFIRMED, P3b.
- **A9 (8 of 31 PASS, 26%)**: superseded. On all of Season A to date: **32 of 143 with a chain reading (22.4%)**
  (`analysis/d016/gate_audit_seasonA_interim_2026-11-03.md` §A, §C).
- **A15 (no rule ends the project)**: CONFIRMED. D008 §3 ends with "If Gate 2 fails: no real money … the next step is
  decided at Gate 2: another season of paper, the options route (RQ4), or the no-edge verdict". A stop is an option,
  not a rule. D017 §5 only withholds money.
- **REPORT §2 concern 12**: both defects CONFIRMED and still in r2. The health counter reads "T2 missing 0 of 32"
  (`gate1.health`; owed since 11-02, STATE NOW). The P6 cost line reads "T2 none recorded" because `stage1.decisions()`
  looks in `decision.json`, while T2's cost is in `t2.json`: Season A mean $0.100 over 30 decisions. Not fixed here (outside P0).
- **REPORT §2 concern 4 (Gate 2 power)**: CONFIRMED, and worse on counts (P4).

## P0 · The Stage 1 data cut — CONFIRMED in substance; the mechanism is different

**What happened** (git and code, not inference):
- The run (`1537ceb`, Mon 11-02 07:28 ET) read `outcomes/shadow/seasonA/graded.json` at `c2dc357` (graded Fri 10-30 21:52 ET).
- That was the **newest** grade on `main`. The next one, `4d9affc`, is Mon 11-02 18:16 ET, after the run
  (`git log -- outcomes/shadow/seasonA/graded.json`). So it was not a stale pull: the grade of the 10-30 exits did not exist yet.
- **Why:** a session counts as settled only from 06:00 ET the next day (`pipeline/shadow.py`, `settled()`). The grader
  fires on weekday evenings only (`.github/workflows/shadow.yml`, cron `40 22 * * 1-5`). D017 §2 fixed the run for Mon
  morning, the first moment after the weekly reset. Nothing graded between Sat 06:00 ET and the run.
- **What was missing at `c2dc357`** (in the cut, neither graded nor VOID): SH-W 20, SH-M 114 (100 graded later, 14 became
  VOID), gated 5. The committee's 129 → 227 graded 10-29 prints is consistent with this.
- **The real defect is in `stage1.py`.** It dropped the ungraded shadow events without a word. It printed "pending 6" for
  the gated read, and that 6 wrongly included CIFR, whose exit-A open is Mon 11-02, outside the cut.

**Fix and addendum** (D017 §2: a bug fix is a new commit beside the first output; `1537ceb` is untouched):
- `4383102`: stage1 counts each read's in-cut events that are neither graded nor VOID, prints them, and `--write` refuses
  while any remain. `a6f7cc6`: a pending event with no exit session is in the cut only if it entered before the cut day.
  Both are tested (`tests/test_stage1.py`, 11 pass) and were committed before the re-run.
- `outcomes/reports/stage1_2026-10-30_r2.md` (code `a6f7cc6`, 10:58 ET; pending 0 · 0 · 0). It matches the committee exactly:

| read | first output | **r2, full cut** |
|---|---|---|
| SH-W (primary) | n 84 · 8 sessions · net −0.76% · [−2.00%, +0.48%] | **n 104 · 9 sessions · raw −1.30% · net −1.50% · [−3.28%, +0.27%]** |
| S0 gated | n 16 · net −2.31% | **n 21 · 7 sessions · net −5.34% · win 33.3%** |
| SH-M | n 596 · raw −0.08% | **n 696 · 14 sessions · raw −0.18% · net −0.38% · [−0.92%, +0.17%]** |
| T1 / T2 BUYs vs all | +0.42% / −1.64% vs −2.91% / −2.83% | −1.86% / −3.95% vs −5.89% / −5.99% (13 / 11 BUYs; INSUFFICIENT) |

- **The uncomfortable part:** the D017 word is still **INSUFFICIENT only because 9 sessions < 10**. The upper bound, +0.27%,
  is below the +0.65% CONTRADICTS HISTORY line. On that line, D017 §5 would read "no new money", not "fund to Gate 1". The
  printed "evidence supports" row stands only on the session count. The cut is fixed at 10-30, so no later session is added.

## P1 · Survivor bias — the asked re-run: CANNOT ANSWER with free data; what can be said

- **What D006 already does** (D006 §2): companies are today's listed names (2026-09-28 data, `universe.json`). But the $2B
  floor is applied **point-in-time per event**: EDGAR shares × the as-traded close. 806 events below the floor at the
  time were excluded. So names that grew into the universe count only from when they were ≥ $2B. The survivorship is
  disclosed in D006 §2, before results. D005 v2 §7.4 asked for a per-date universe "where possible"; D006 says what was not.
- **What is missing:** firms ≥ $2B at an event that later delisted, were acquired, or shrank below $2B by 2026-09-28.
- **Why the 2023-09-01 re-run is not possible free:** yfinance returns no price history for most delisted tickers. Alpha
  Vantage's free key is 25 calls a day (CLAUDE.md data facts). EDGAR's frames API gives point-in-time shares, but no prices.
  **The still-listed shrinkers are possible:** EDGAR shares × yfinance closes, about one working session of code. That covers
  the firms a bad print pushed below $2B, which is the selection on the outcome that matters most. Acquired names (premium at
  the deal, not at prints) and outright failures at ≥ $2B are the part free data cannot reach. Not run this round (brief scope).
- **Partial evidence, history only** (computed 2026-11-03 for this answer from `legs_exploratory.json`, n 2,771). The
  survivor filter is strongest on the oldest events. If the bias were most of the premium, the oldest events would show the
  largest premium. They show the smallest:

| print date vs the 2026-09-28 selection | n | raw mean | median |
|---|---|---|---|
| > 2 years before (2023-09 → 2024-09) | 810 | **+0.25%** | +0.64% |
| 1–2 years before | 907 | +1.07% | +0.91% |
| < 1 year before | 1,054 | +1.13% | +0.75% |

  By year (the committee's figures, reproduced exactly): 2023 −0.57% (n 209), 2024 +1.02%, 2025 +0.43%, 2026 +1.54%.
  Regime confounds the age split, so this cannot bound the bias below 0.2 pts. It does not support "a bias near the full premium".

## P2 · Why the premium should hold live — CONCEDED: +0.65% is an upper bound

- (a) SH-M on the full cut is raw −0.18%, 95% net [−0.92%, +0.17%] (r2). Its upper bound is below +0.65% net. SH-W's is too.
- (b) The lab study is in the DRIVE repo. Rule 9 forbids reading it, so PRE can neither check nor dispute it.
- (c) The by-year numbers are reproduced (P1). History's mean rests on a regime and a right tail.
- PRE's files hold **no mechanism evidence** that reconciles these. The premium is a literature prior, not a PRE finding
  (FRAMEWORK, References). D006 itself discloses survivorship (§2). Without new data, history's +0.65% is a ceiling.

## P3 · Executability

**(a) MOC → MOC on SH-W and SH-M: CANNOT ANSWER this round.**
- It must be registered as a new secondary before any computation (rule 5). D017 §5 forbids this look from changing a
  registered test, and a new registry version is the committee's §12.3: Jacob's call. The brief rules out Season A
  outcome analysis beyond P0.
- **Capture:** shadow files store only the opens they need. But the closes (the pre-print session and the reaction day) are
  daily bars, retrievable **after the fact** from yfinance (`auto_adjust=False`, as `shadow.py` already fetches). So nothing
  is lost by waiting for registration. `shadow.py` is on the D015 v1 hash list (STATE standing rules), so the code is a new
  script beside it, not an edit. Gated events already carry exit B, the reaction-day close (`gate.json` timing).

**(b) Signed slippage: CONFIRMED** (`paper/ledger.json`, 23 real round trips closed by 10-30, vs the yfinance official open):

| leg | mean | median | adverse |
|---|---|---|---|
| buy at the entry open | −13 bp | −9 bp | 10 of 23 |
| sell at the post-print open | **+105 bp** | +88 bp | **20 of 23** |
| round trip | **+91 bp** (sum of means +92) | +97 bp | 16 of 23 |

- **Also uncomfortable:** D008 §3 criterion 4 (Execution) requires a median |paper fill − official open| ≤ 15 bp. Stage 1
  reports 27.5 bp on the buys alone (r2 P4). On the current record, criterion 4 fails. It also requires mean slippage
  inside the net return, which Stage 1's flat 0.20% does not do.
- **Would a limit or MOC exit avoid it?** Not measured. The paper exits are market orders at the open
  (`ledger.json` strategy: "sell at the exit-A open"). A paper MOC fill would measure the simulator, not the closing auction.
  Limits at the indicative quote may never fill (D011 v3; `ops/incidents/2026-10-13_DPZ_exit.md`).

## P4 · Power against the horizon (counts only)

- **SH-M:** 696 graded by 10-30 on 14 sessions (r2). By count, the 600–850 of RESEARCH_PLAN ("t ≈ 2 needs ~600–850
  events", §4) is met inside Season A, ~850 in the first week of November. But those are not independent: ~50 per session.
  PRE has no registered design effect. The committee's ~2,000 (Seasons A + B, Feb 2027) is its estimate, not PRE's.
- **Gated S0:** 32 PASS of 143 gated so far (22.4%). D003 v5 A4, chosen for Season B, gives 43 of 143 (30.1%) on the same
  chains (gate audit 11-03 §C). Season A has ~290 calendar events (`ops/capacity_peak_2026-11.md` §1). That is ~65 PASS
  under A0, ~87 under A4. One season a quarter:

| cumulative gated events | reached (A0 in A, A4 from B) |
|---|---|
| 250 (D008 Gate 2 #1) | **Season C–D: May–Aug 2027**. A + B ≈ 150 |
| 600 | Season H: Jul–Aug 2028 |
| 850 | Season K: Apr–May 2029 |

- **Finding:** D008 §3 #1 (H-S0 on ≥ 250 graded events, A + B pooled, at Gate 2, Mar 2027) **cannot be met on gated
  events**. RESEARCH_PLAN planned ~150 gated a season (§4 table); the gate passes about half that. RESEARCH_PLAN's Gate 2
  line (§6, the D008 draft) says "T0 or T0-wide", while D008 says H-S0. The two disagree, and this must be settled before Season B.

## P5 · What would you remove — the table the records support

| component | AI allowance (recorded) | laptop time | Gate 2 criterion it serves (D008 §3) |
|---|---|---|---|
| Code steps: calendar, confirm, S2 gates, freeze, grade, SH-W/SH-M, chain capture | 0 (GitHub Actions, public repo) | repairs | #1, #2, #3, #5 |
| Paper shares (T0) | 0 | incidents | #4 Execution, #6 Risk |
| Main T2 (D004 v4) | $0.100 per decision (`t2.json`, n 30); routine `t2-cloud` 28 sessions a week | — | #7 only via H-T2C (A + B pooled). T2 never enters S0 |
| Shadow T2R, T2O, T2G (D013) and T2M/T2E | T2R $0.100, T2O $0.208 per decision (n 32 each); T2G none recorded; routine `t2-models` 28 a week | — | **none** |
| Paper options F and L (D011) | 0 in steady state; `paper-trigger` 14 sessions a week | incidents (DPZ exit 10-13; a halt cleared 11-02, `199b8c4`) | **none**. The options route is one of Gate 2's "next step" choices |
| C1 (D015) | 0 (code capture) | — | **none** (H-C1 is confirmatory test 10, not a D008 criterion) |
| D018 history batch | 0 so far (not registered; HYPOTHESES "(D018 …)") | — | **none**. #7 admits a layer only after its own confirmatory test |
| Laptop chats | **the largest draw** (`capacity_peak` §3) | — | — |

- **Weekly share per component: not recorded.** The one measured bound: all T2 tracks together cost ≤ 2 points of the
  weekly allowance per PASS name (`capacity_peak` §3). At ~9 PASS a week in Season A, that is ≤ ~18 points a week
  (derived). By recorded $, the main T2 is about a quarter of T2 spend; the shadows are the rest.

## P6 · Cost per useful answer — CANNOT ANSWER (no weekly ledger exists)

- Recorded: AI cost per decision, as above. Per gated event: main T2 + T2R + T2O ≈ **$0.41 API-equivalent** (T2G
  unrecorded). That is ≈ $8.6 for the 21 graded gated events in the cut (derived).
- Laptop chats: `ops/token_efficiency_2026-10.md` covers 9 chats, 1,378 calls, Sep 21 – Oct 21, in tokens and not by
  week or task. Cache reads are 97.3% of tokens. Worktree chats are not in its count.
- Code steps: 0 allowance. Measuring the routines' weekly cost is owed (`capacity_peak` §3, "Owed: measure from … the
  routine run logs"). Cost per *useful* answer: no confirmatory answer exists yet, so the denominator is zero.

## P7 · Layer 1 — CONFIRMED missing as an outcome; partly captured as an input

- **Captured at freeze** (gated events): `D_eps_est_current_q` (the pre-print consensus EPS), `D_eps_trend_current_q`, and
  the last four prints' estimate, reported value and surprise (`E_last4_prints`, `pipeline/factors.py:66-97`).
- **Not captured:** this print's actual EPS, consensus and actual revenue, and any surprise forecast. T2 predicts only the
  trade (BUY ⇔ confidence > 0.50, D004 v4 §"Code sets the decision").
- **Deliberate?** No file chooses to drop it. The recorded reason surprise-based items were held back is the EPS basis.
  The same vendor gave ORCL two consensus figures on two bases, and FRAMEWORK ("Two findings that shape the whole design",
  item 3) rules "one EPS basis … validated per source before any history is built". `factors.py` flags it as "EPS basis NOT pinned".
- **Cheapest capture:** one `get_earnings_dates()` call per event after the print, free, already used at the snapshot
  (`factors.py:66`). It returns the same row with "Reported EPS" and "Surprise(%)" against the consensus frozen before.
  Revenue: actuals from EDGAR XBRL (the D004 §4 tags, free); consensus revenue only as yfinance's current-only estimate,
  captured at freeze. `grade.py` is hash-listed (D004 v4), so this is a separate capture script, not a grade change.

## P8 · Failed trades and largest errors — after Gate 1

- This needs per-name outcomes and T2's dossier lines set against outcomes. D017 §4 holds both to Gate 1, and H-T2C's
  test stays clean only if T2's reasoning is not read against outcomes before then (D005 v3).

## P9 · Opportunities rejected — counts now, the mean after Gate 1

- `analysis/d016/gate_audit_seasonA_interim_2026-11-03.md` (counts only; it reads `gate.json` and `option_chain.json`, nothing else):
  - 148 gated so far: 5 failed before the chain (4 `printed_before_entry`, 1 `no_expiry`) and 143 had a chain. 32 PASS.
  - Failing each check: `wide_spread` 106 (the only failure on 46), `thin_oi` 65 (the only failure on 4), `no_quote` 1,
    `low_implied_move` 1. The most common combination is `wide_spread` + `thin_oi` (59).
  - By expiry gap: weeklies (≤ 5 sessions) pass 38.1%, monthlies 10.0%.
- The gated-out mean against S0's: at Gate 1 (D008 §2 secondary; D017 §4).

## P10 · One data item

- **No predictor can be named with evidence.** Every factor batch failed (HYPOTHESES §3: D006, D007, D010, D014). Gate 2's
  verdict is buy-all (D008 §3 #1), so no predictor moves #1–#6. #7 admits a layer only after its own confirmatory test.
- **The one item: Layer-1 actuals (P7).** Cost $0 and one call per event. It moves **no Gate 2 criterion**. What it buys is
  the diagnosis the committee asks for: "wrong about the numbers" vs "wrong about the reaction", for P8 at Gate 1.
- If the aim is a Gate 2 criterion, the lever is sample, not data: D003 v5 A4 (+34% PASS, P4). Even that leaves #1
  unreachable by Mar 2027.
