# D014 · v2 — the first hour after the print: the pre-print state and the sector's week

> **Frozen 2026-10-13 ET, while v1's fetch was still running.** No D014 reaction-day number had been looked
> at: no chunk, no result, no report.
> **D014 v1 is untouched** (rule 5). Its 42 tests, its verdict and its files stand as frozen. This is a
> second, separate family with its own count.
> **EXPLORATION (rule 6).** A survivor is a CANDIDATE, never a finding.

## 0. Origin

- **Source:** a second note from the DRIVE portfolio chat, passed on by Jacob on 2026-10-13. It held ideas
  only, with no holdings, scores or rankings, so rule 9 is not touched.
- **Adopted:** its ideas 1 (the pre-print state), 2 (the sector's week) and 4 (retail costs, as a
  secondary).
- **Deferred:** idea 3 (customer → supplier). It needs a customer–supplier map we can verify, from 10-K
  major-customer disclosures. None exists in the repo, and building one is not cheap. It goes to the
  backlog next to FRAMEWORK F4.

## 1. Events, signal and returns: exactly v1

- The same rows: `analysis/d014/raw/events_intraday.csv.gz`.
- The same voids, the 1% pre-market gap floor, s, y_5, y_30 and y_60, TRAIN and VALIDATION, CR1 by R, and
  rule 7.
- Only v1's frozen functions are used. `run_d014_v2.py` imports `run_d014.py`, so the definitions cannot
  drift.
- **"Beat" = s = +1**, a pre-market gap up: the market's own read of the print at 09:27.
  - The vendor EPS surprise is not required. Requiring it would cut n by about a third, and its basis is
    vendor-defined.
  - The surprise-filtered version is reported as descriptive only.

## 2. New data: `analysis/d014/fetch_v2.py`

- **Source:** Alpaca daily bars, feed sip, `adjustment=split`, 2022-06-01 → 2026-09-30. One request per
  symbol, for every event ticker, every sector ETF below, and SPY.
- **R−1 and R−6:** sessions on SPY's daily calendar, as in v1.

| field | definition |
|---|---|
| `ret5` | the stock's close R−1 / close R−6 − 1: the five sessions before the print. Both closes are before the print for BMO and AMC reporters alike |
| `etf` | the D003 v4 map (`registry/D003_universe_screen_v4.json`): `named` first (MSTR → IBIT), else `industry_map[industry].etf`, with the industry from `analysis/history/universe.json` `clusters[ticker].industry`. An unmapped ticker, or an ETF with no bar in the window (IBIT before 2024), → no `rel5`, excluded from C9 and C10 and counted |
| `rel5` | the ETF's return over the same window minus SPY's |

Missing stays missing. A failed symbol is retried 3 times, then recorded as missing.

## 3. The family: 18 tests on TRAIN, all logged

Horizons are h = 5, 30 and 60. Only events with s = +1 are used.

| block | group | tests |
|---|---|---|
| C7 washed out into the print | ret5 ≤ −8% | mean y_h (3) |
| C8 ran up into the print | ret5 ≥ +8% | mean y_h (3) |
| C7 − C8 | difference of the two means | 3 |
| C9 sector being sold | rel5 < 0 | mean y_h (3) |
| C10 sector being bought | rel5 > 0 | mean y_h (3) |
| C9 − C10 | difference of the two means | 3 |

**The difference tests:**
- They are the regression y = a + b · 1[group A] on the union of the two groups.
- b is the difference.
- Its standard error is CR1, clustered by R.
- **The ±8% thresholds** are the note's own, mirrored for the run-up.
- **Survivor:** |t| > 3 **and** BH q < 0.10 over these 18.
- **VALIDATION:** survivors only, once. It uses a one-sided p in the TRAIN sign, Holm-corrected across the
  survivors. For a group mean, it also requires a net mean > 0 under v1's cost model. A difference is not a
  trade, so it needs the sign and the p only.
- **Verdict:** CANDIDATE or failed validation. If nothing survives TRAIN: "no pre-print-state or
  sector-week pattern clears the bar".

## 4. Secondary (decides nothing): retail ticket costs

- **Small-ticket net:**
  - Every v1 and v2 survivor's net mean on TRAIN and VALIDATION is also reported with a **13 bp** fee in
    place of 2 bp. That is $1.98 on a $1,500 position at $0.99 per order.
  - **The pre-market leg:** v1's entry is the opening auction. It never trades before 09:30, so the note's
    pre-market cost (about twice the regular-hours round trip) does not apply to it.
  - **Whether a retail moomoo account can join the opening auction** (a market- or limit-on-open order)
    is not known here.
  - **v1's delayed variant** (09:35 entry, paying the spread) is the retail-feasible entry. It is reported
    under both fees, whatever its v1 verdict.
- **Descriptive:** the C7 and C8 means with surprise > 0 required as well.

## 5. Files

- `analysis/d014/fetch_v2.py` writes `analysis/d014/raw/events_v2.csv` and `raw/manifest_v2.json`.
- `analysis/d014/run_d014_v2.py` writes `results_v2.json` and `REPORT_v2.md`. It is deterministic.
- `tests/test_d014_v2.py`.
- `.github/workflows/d014-v2.yml` (workflow_dispatch: `fetch`, then `analyse`). It runs after v1's
  analysis.
- All are hashed in `registry/D014_implementation_v2.sha256` before v2's fetch, and before v1's analyse
  step runs.
