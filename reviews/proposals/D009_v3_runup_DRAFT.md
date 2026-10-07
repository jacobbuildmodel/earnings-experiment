# D009 · Shadow tracks · v3 — DRAFT: SH-RU, the 20-session run-up into the print

> **DRAFT, not a rule.** It is frozen only after an independent review. Its sample counts only windows
> that **open after the freeze commit**, so nothing it tests exists yet when it is written.
> v1 and v2 stay live and untouched. Everything not listed here is D009 v2 unchanged.

## Why, and where the idea came from (disclosed)

- **Source.** Jacob relayed this on 2026-10-07 from the DRIVE portfolio chat, measured there on its own
  universe: 436 "AI-hardware" prints since 2021.
  - Over the 20 sessions **into** a print they averaged **+3.4% against SPY** (t 2.7), and +8.4% in 2026.
  - In 2026, the reaction day itself averaged **−1.9%**.
  - No holding, account or DRIVE file was read here (rule 9). The numbers were not re-derived and are not
    evidence: they come from data that overlaps this project's 2023–2026 history.
  - **This is a candidate (rule 6).** It is therefore tested only on windows that did not exist when it
    was proposed.
- **Literature (V1):** this is LR01. Aboody, Lehavy & Trueman (2010) find that extreme 12-month winners
  gain +1.58% in the 5 days **before** a print and lose −1.86% in the 5 days after.
- **Why it matters here.** Our trade (D001) enters one session before the print. It skips any run-up and
  holds only the reaction. If the run-up is where the premium sits, the experiment is measuring the wrong
  window for the business question.

## SH-RU — mechanics

- **Universe:** every Season A or Season B candidate of the D003 S1 screen (`candidates.json`), plus
  mid-season additions with their own capture. One event per issuer (D003 v3).
- **Expected date, as known at entry:** the earliest report date that the S1 (or mid-season) calendar
  capture gives the name inside the season window. It is a write-once file, committed before entry.
  **Never the date learned later.**
- **Entry:** the **close** of session `E = D_exp − 21 sessions`. This is the 20 full sessions before
  the session preceding `D_exp`.
- **Exit:** the **close of the last session before the actual report date** `D_act`. That is pre-print
  for both BMO and AMC, so the session is never needed.
  - `D_act` is the company-confirmed date (`confirm.json`), else the date of the Item 2.02 8-K.
  - It is known before the exit, because companies announce dates in advance.
  - If neither exists by `D_exp` + 10 sessions, the event is VOID `no_print_found`, and the voids are
    counted.
- **The event counts only if:**
  - `E` is a session strictly **after the freeze commit** of this rule, and after its calendar capture
    commit
  - `D_act` > `E` + 1
  - otherwise VOID `window_not_open` or `print_before_window`
- **Return:** yfinance daily adjusted close (dividends included, splits adjusted), fetched once after the
  exit. `single_source` is disclosed.
  - **Excess** = stock return − SPY return over the same closes (beta 1).
  - **Net** = excess − 0.20% round trip; descriptive.
- **Clusters:** **AI hardware** = the D003 clusters `semis`, `hardware_networking` and `ai_infra`, fixed
  here. Every other cluster is "rest".
- Outcomes go to `outcomes/shadow/<season>/runup.jsonl`, fenced from T2 like every shadow (D004).

## Hypotheses — one family of exactly two, Holm m = 2, one-sided α = 0.05

| id | hypothesis | sample |
|---|---|---|
| **H-RU** | the calendar-time run-up portfolio earns a mean daily excess return > 0 | all SH-RU events |
| **H-RU-AIH** | the same, for AI-hardware events only | `semis`, `hardware_networking` and `ai_infra` |

**Test.** The windows overlap, so the events are not independent. The test is therefore the
**calendar-time portfolio**:
- Each session `t`, take the equal-weighted mean of the daily excess returns (close `t−1` → close `t`)
  of every event whose window holds `t`.
- Test the mean of that daily series with a **Newey–West HAC t, lag 5**, one-sided.
- Days with no event are skipped.

**Every result also reports:**
- the event-level mean window excess (and net) with its median
- the minimum detectable effect: (1.645 + 0.842) × HAC se
- the result **without the largest 5% of window returns**, a fat-tail check

**Minimums, else "insufficient":** at least 30 events and at least 40 portfolio sessions, pooled. For
H-RU-AIH, also at least 10 events in each season.

**Verdict:**
- Once, on **Seasons A and B pooled**, at the end of Season B (D009 v1 §5 timing).
- Season A's result is interim only.
- Wording is as in D009 v1 §5: never "works", never "no effect".

## What a result can do

- At Gate 1 or Gate 2, a confirmed H-RU or H-RU-AIH may be registered as a strategy hypothesis for a later
  season, as a new version with its own clock.
- It never changes T0, T1, T2 or D001's exit.
- **It does not test the reaction-day claim (−1.9% in 2026).** That claim is already measured live by T0
  and SH-W on the print leg (D005 v2's split of exit A into the pre-print and print legs).

## Known limits (disclosed)

- **Structural sample loss:** each season's screen comes about one session before its first print. So
  only prints at least ~21 sessions after the screen qualify: about Nov 9–20 in Season A, and the later
  part of Season B. Most of each season's early prints are out by design.
- **The expected date can be wrong.** The exit uses the actual date, so the window length varies. This is
  disclosed, and the event-level result is also reported for windows of 15–25 sessions only.
- **Close-to-close prices are not tradable at the open;** this is a shadow measurement.
- **Cluster labels** are D003's Yahoo-industry map, not the DRIVE chat's definition of "AI hardware".

## Implementation

`pipeline/shadow.py` gains a `runup` grade step. It must be written, tested on synthetic data (size of
the HAC test under overlap, and power at a planted drift) and reviewed **before the first SH-RU exit**,
about Nov 9. Its hash is registered then. This file fixes the method.
