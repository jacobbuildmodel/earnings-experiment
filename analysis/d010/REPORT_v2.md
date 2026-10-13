# D010 v2 — hold-to-expiry and the call–put IV spread · RESULT (exploration only)

> **Spec:** `registry/D010_exploration_options_v2.md`, frozen 2026-10-13 (`458cd3f`) before any v2 number.
> **Code:** `run_d010_v2.py`, deterministic: two runs give byte-identical `results_v2.json` and
> `results_v2_scalefix.json`. SPY was fetched once into `raw/spy_v2.csv`.
> **EXPLORATION (rule 6).** Nothing here is confirmed. It informs what Season B registers at Gate 1.

## ⚠ A data defect, found after the run, and the disclosed correction

- **The defect:** yfinance's `auto_adjust=False` Close is still **adjusted retroactively for later splits and
  spin-offs**. For 16 of 1,249 events, spot and strike sit on different scales:
  - APH ×8 (strike / spot ≈ 2.0)
  - KLAC ×4 (≈ 10)
  - WDC ×3 (≈ 1.34, the SanDisk spin-off)
  - ANET ×1 (≈ 4)
- **What it breaks:** hold-to-expiry compares the stock's close with the strike, so these events produce
  returns of hundreds of percent. **The as-frozen Y results are invalid.**
  - v1 is barely touched. Its X1 is −3.22% with these events and −3.27% without them, because v1's
    statistics are ratios of option quotes.
  - Family Z is untouched: all 16 events already fall out as `no_iv`, since their mids cannot be priced
    on the wrong scale.
- **The correction (post hoc, disclosed):** drop events whose strike / spot on P is outside [0.8, 1.25]. The
  criterion uses no outcome. Same tests, same BH over 9 → `results_v2_scalefix.json`.
  - A preview of the corrected Y means was seen before this report was written. That is fine for
    exploration, but it is stated here.
- **The live pipeline is not affected:** the gates use same-day quotes, and SH-RU uses only return ratios.
- **Lesson for any future history study:** check strike / spot before trusting any price-level formula.

## Results (scale-fixed; the as-frozen table is in `results_v2.json`)

| id | sample | n | R dates | mean | t | BH q | halves (R < / ≥ 2025-10-15) | finding |
|---|---|---|---|---|---|---|---|---|
| Y1 | short, hold to expiry, all | 1,233 | 233 | **−0.80%** | −2.88 | 1.00 | −1.00% / −0.60% | no |
| Y2 | short, hold to expiry, liquid | 160 | 109 | −0.51% | −0.46 | 1.00 | −0.10% / −1.57% | no |
| Y3 | short, liquid and expiry ≤ 7 d after R | 12 | 12 | −2.14% | −0.84 | 1.00 | | insufficient |
| Y4 | long, hold to expiry, all | 1,233 | 233 | **−2.85%** | **−9.28** | 1.00 | −2.06% / −3.63% | no |
| Y5 | long, hold to expiry, liquid | 160 | 109 | −0.16% | −0.15 | 1.00 | −0.51% / +0.71% | no |
| Z1 | slope of reaction excess on IV spread | 1,226 | 232 | +0.017 per unit | 0.94 | 0.52 | + / − | no |
| Z2 | richest-call third − cheapest-call third | 1,226 | 197 | +0.77 pts | 1.20 | 0.52 | +1.31 / +0.17 | no |
| Z3 | slope, liquid | 160 | 109 | — | 0.32 | 0.84 | + / − | no |
| Z4 | richest-call third: mean reaction excess | 409 | 147 | **+1.98%** | **4.15** | **0.000** | +1.73% / +2.20% | **yes, by the frozen rule** |

- Mid-price, hold-to-expiry short: **+1.03% all, −0.17% liquid** (descriptive).
- `ivs` is missing for 1.8% of events.
- Every Y test is one-sided "> 0", so a strongly negative t carries q ≈ 1.

## What it means

1. **Holding to expiry does not rescue the short straddle.**
   - On all events: −0.80% after one spread, against −3.22% after two in v1. The second spread cost about
     2.4 pts, but the trade is still negative.
   - On liquid names, ≈ 0 (−0.5%).
   - Compare the review's liquid cut, which exited at the reaction-day close: +1.13% at mid. **Whatever
     edge exists sits in the volatility crush at the print, and holding on for the median 15 days after it
     gives it back.**
   - The structure SH-X and H-XT hold, expiry ≤ 7 days after R, has only 12 liquid events in this history:
     insufficient. History cannot price it. Only the live record can.
2. **Buying straddles loses again** (−2.85%, t −9.3, both halves). That is consistent with v1 and with
   de Silva, Smith & So.
3. **The call–put IV spread is no selector here.**
   - The comparisons that isolate it (Z1 slope, Z2 top − bottom) are not significant.
   - Z4 passes the frozen finding rule, but mostly because **all** events rose. The mean reaction-session
     excess over SPY is +1.46% for all, +1.21% / +1.20% / +1.98% by tercile. The richest-call third adds
     about +0.5–0.8 pts over the rest, and that is not significant.
   - **The honest reading of Z4: the earnings-session premium is large in this sample. That is RQ1's
     question, and the IV spread adds little.**
   - Caveat: the sample is today's listed names (survivorship) in a strong 2024–26 market, so the +1.46%
     is surely inflated.

## For Gate 1 (Season B's confirmatory family)

- **H-XT** is unaffected. It is live and tests its own structure, and history could not test it.
  - **D011's paper butterfly exits on the reaction day**, the structure that history favours (+1.13% at
    mid, liquid). It deserves a look as a registered shadow statistic at Gate 1: an SH-X variant with
    exit at the R close.
- **LR12 (IV spread):** keep recording it live. Do not make it Season B's "best option signal" on this
  evidence.
- **T0, the premium:** history is consistent with a positive reaction-session premium. The live record
  stays the judge.
