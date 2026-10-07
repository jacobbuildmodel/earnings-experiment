# D009 · Shadow tracks · v3 — FROZEN 2026-10-07 (ET) · SH-RU, the 20-session run-up into the print

> v1 and v2 stay live and untouched. v3 adds one shadow track and its own family. Everything not listed
> here is D009 v2 unchanged.
> **Nothing v3 tests exists yet:** an event counts only if its entry close comes at least one full
> session after this file's freeze commit.
> Draft and review: `reviews/proposals/D009_v3_runup_DRAFT.md`. An independent review (Sonnet) said
> FREEZE WITH FIXES, with 2 critical, 6 should-fix and 3 minor findings. All are applied below.
> The rule is written so that the code has no discretion.

## 1. Why, and where it came from (disclosed)

- **Source.** Jacob relayed it on 2026-10-07 from the DRIVE portfolio chat, which measured its own
  universe: 436 "AI-hardware" prints since 2021.
  - +3.4% against SPY over the 20 sessions into the print (t 2.7), and +8.4% in 2026
  - a −1.9% reaction day in 2026
  - No holding, account or DRIVE file was read (rule 9). The numbers are a **candidate, not evidence**
    (rule 6): they come from data that overlaps this project's history, against a beta-1 benchmark in a
    rally year.
- **Literature (V1):** LR01. Aboody, Lehavy & Trueman (2010) find +1.58% in the 5 days before a print
  and −1.86% in the 5 days after, for extreme 12-month winners.
- **Why it matters.** D001 enters one session before the print, so it holds the reaction and skips any
  run-up.

## 2. SH-RU — mechanics (no discretion left to code)

- **Sessions** are NYSE sessions from `pipeline/sessions.py`, half-days included. `shift(d, n)` is
  that file's.
- **Universe:** the S1 screen's `candidates.json` for `seasonA` and `seasonB`.
  - One event per issuer per season (D003 v3).
  - **Mid-season additions are excluded** from the tests and reported descriptively.
- **D_exp, the expected report date known at entry:**
  - Read only from that season's S1 capture files: `raw/nasdaq_calendar.json` and `raw/av_calendar.csv`.
    Later re-pulls are ignored.
  - Take the name's dates inside the season window from each source.
  - Use the earliest Nasdaq date. If Nasdaq has none, use the earliest Alpha Vantage date. If both have
    one and they differ, use the **earlier** of the two.
- **E, the entry session:** `E = shift(D_exp, −21)`. The entry is the **close of E**.
  - The event counts only if the date of E is **strictly later** than the ET date of this file's freeze
    commit, and later than the S1 capture's commit date. Otherwise it is VOID `window_not_open`.
- **D_act, the actual report date:**
  1. the company-confirmed date in `events/<season>/<T>_<date>/confirm.json` or `event_status.json`
  2. else the date of the first Item 2.02 8-K accepted on or after `shift(E, 2)`

  If both exist and differ, use the earlier.
- **Window and exit:** the exit is the **close of** `X = min(shift(E, 20), shift(D_act, −1))`. The
  window is truncated, never voided, for an early or late print.
  - VOID `print_before_window` only if `D_act ≤ shift(E, 1)`. Voids are counted and reported by cluster.
  - **No D_act** by `shift(D_exp, 30)`: `X = shift(E, 20)`, flagged `print_date_unknown`. The event is
    included and also reported without.
- **Prices:**
  - yfinance daily **adjusted** close (`auto_adjust=True`), for the stock, SPY and the sector ETF.
  - Fetched once, at or after 06:00 ET on the session after X. Stored write-once in
    `outcomes/shadow/<season>/runup_prices.jsonl`. Later vendor revisions are ignored.
  - `single_source` is disclosed.
- **Excess returns.** Over (close E, close X], and day by day for the portfolio:
  - **Primary — beta-adjusted:** `r − β·r_SPY`.
    - β is the OLS slope of 250 daily stock returns on SPY, ending at the close of `shift(E, −1)`, shrunk
      to `0.67·β + 0.33`.
    - With fewer than 120 returns, β = 1, flagged `beta_short`.
  - **Secondaries, mandatory:** beta-1 (`r − r_SPY`), and sector ETF (`r − r_ETF`) from D003 §8's map.
    No ETF → not computed, and counted.
  - Net = event-level excess − 0.20%. It is descriptive, and for small caps the real cost is higher.
- **AI hardware** is the D003 clusters `semis`, `hardware_networking` and `ai_infra`, fixed here.
- Outcomes go to `outcomes/shadow/<season>/runup.jsonl`, fenced from T2 (D004).

## 3. Hypotheses — one family of exactly two, Holm m = 2, one-sided α = 0.05

| id | hypothesis | sample |
|---|---|---|
| **H-RU** | the calendar-time portfolio's mean daily **beta-adjusted** excess return > 0 | all SH-RU events, Seasons A + B pooled |
| **H-RU-AIH** | the same | AI-hardware events only |

- **The portfolio.** Each session `t` in (E, X] of any event, take the equal-weighted mean of that day's
  beta-adjusted excess returns (close `t−1` → close `t`) across the events holding `t`. Days with no event
  are skipped.
- **Primary inference: the circular block bootstrap** of that daily series.
  - Block length 20, 9,999 draws, seed `sha256("H-RU")` or `sha256("H-RU-AIH")`.
  - The series is demeaned to impose the null.
  - p = the share of bootstrap means ≥ the observed mean.
- **Secondaries, always printed:**
  - the Newey–West t at lag 5 and at lag 20
  - the event-level mean (beta-adjusted, beta-1, ETF, net) with its median, and a t clustered by E date
  - the portfolio's regression alpha on SPY
  - the result without the largest 5% of window returns
- **Size gate.** Before the first X, a synthetic check at 30, 45 and 60 events with this overlap must show
  bootstrap size ≤ 7% at a nominal 5%. If it fails, the KV fixed-b NW (lag 20) replaces the bootstrap as
  primary. That swap is decided on synthetic data only.
- **Significance requires both:**
  - Holm-adjusted p < 0.05 on the beta-adjusted series
  - a beta-1 point estimate and an ETF point estimate that are not negative, reported beside it
- **Minimums, else "insufficient":**
  - at least 30 events, 40 portfolio sessions and 10 distinct E dates, pooled
  - for H-RU-AIH, also at least 10 events in each season
- **Every result reports its MDE:** (1.645 + 0.842) × se.
- **Dependence, disclosed:**
  - An issuer in both seasons gives two events, non-overlapping in time.
  - Holm over nested hypotheses (AIH ⊂ all) is conservative.
  - For BMO prints, SH-RU's last day can touch T0's entry session. SH-RU and T0 are never pooled.
- **D009 v1 §1's print-timing checks do not apply:** SH-RU exits before the print.

## 4. Verdict

- **Once**, on Seasons A + B pooled.
- **When:** the later of D009 v1 §5's Season B end and the last SH-RU exit + 2 sessions.
- Season A gives an interim only.
- **Wording:**
  - "p < 0.05 (shadow, secondary; D009 v3 family m = 2) — late-window reporters only", or
  - "no evidence (shadow) — an effect smaller than <MDE> would usually be missed — late-window reporters
    only", or
  - "insufficient"
  - Never "works", never "no effect".
- **Expected outcome, stated now.** Only prints at least ~21 sessions after a season's screen qualify.
  In Season A that is about Nov 9–20, and the big AI-hardware reporters mostly fall outside it.
  - The reviewer's rough figures: AI-hardware window sd ~12%; at n = 40, se ~1.9% and MDE ~4.7%, above
    the claimed effect.
  - **"Insufficient" is the expected result for H-RU-AIH.** H-RU has more events, but its power is also
    modest.
  - This is a **monitoring shadow**. A null here does not refute the source claim, because the
    populations differ.

## 5. What a result can do

- At a Gate, it may support registering a run-up strategy as a new version with its own clock.
- It never changes T0, T1, T2 or D001's exit.
- The −1.9% reaction-day claim is already measured live: T0 and SH-W on D005 v2's print leg.

## 6. Implementation

- `pipeline/shadow.py runup` will implement §2–§3 exactly.
- **Before the first X** (no earlier than Nov 9, 2026), the following are registered in
  `D009_implementation_v3.sha256`:
  - its hash
  - a golden fixture (`tests/fixtures/runup_*`): a synthetic calendar and prices → E, D_exp, D_act, X and
    returns
  - the size-gate result
- **No SH-RU code change after its hash is registered.** A change creates D009 v4.
- If the code is not registered before the first X, every event whose window has completed by then is
  reported as descriptive only, and the tests use only later windows.
