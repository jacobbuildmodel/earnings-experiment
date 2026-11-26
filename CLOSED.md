# CLOSED, 26 November 2026

The Earnings Experiment (PRE) is closed by its funder's decision. This repository is archived read-only as the
record. Nothing runs any more: all GitHub Actions workflows and cloud routines were switched off before archiving.
The plain-language summary of the whole journey is `HISTORY.md`.

## Why it closed

- **Selection.** No rule or AI judgement was shown to beat buying every eligible event:
  - PRE v1: 27 blind calls, 14 right;
  - D006: no factor cleared t > 3;
  - D007: none of 20 new signals;
  - D010: neither side of the straddle pays after costs;
  - D014: no first-hour pattern validated.
- **The premium itself.** Season A's final live read, all graded (shadow grade of 2026-11-25 23:21 ET), cluster-robust
  by entry session:

| read | n | sessions | raw mean | net of 0.20% | 95% raw interval, t (G − 1) |
|---|---|---|---|---|---|
| SH-M (primary under D019) | 1,459 | 29 | −0.37% | −0.57% | [−1.26%, +0.52%] |
| SH-W | 271 | 23 | −0.75% | −0.95% | [−2.32%, +0.82%] |

  History's +0.85% raw (D006) lies outside both intervals.
- **D019's Gate 1 bar was a near-tie, not a clear fail.** It required SH-M's upper bound to be at least +0.50%; on this
  computation (CR1, 28 df) it is +0.52%. The registered Gate 1 code was never run. The project was closed on cost and
  evidence, not on the bar:
  - measured paper execution cost ~0.9% a round trip, against the 0.20% assumed;
  - small-account fees on top;
  - D008's money path (250 gated events) could not be reached before mid-2027.
- **The committee record** is in `reviews/2026-11-03_stage1_committee/`: `REPORT.md`, `PRE_QA.md`, `PRE_QA_answers.md`
  and `COMMITTEE_ASSESSMENT.md`. The reframe rule is `registry/D019_reframe_v1.md`.

## What was switched off on 2026-11-26

- **Cloud routines:**
  - `earnings-s2-trigger`;
  - `earnings-t2-cloud`;
  - `earnings-paper-trigger`;
  - `earnings-housekeeping-cloud`;
  - `earnings-d010-backtest`.

  `earnings-t2-models` was already off.
- **GitHub Actions:** all 25 workflows disabled, then the repository archived.
- **Left as they are:**
  - the Alpaca paper accounts (paper money only) and their API keys in this repository's secrets;
  - `GEMINI_API_KEY`.

  Nothing can use these keys once the repository is archived. Revoke them at the providers if wanted.

An offline copy of the full git history (every branch) is kept outside this repository.
