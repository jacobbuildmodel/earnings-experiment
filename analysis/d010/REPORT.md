# D010 v1 — the earnings straddle on history · RESULT

> **EXPLORATION ONLY (rule 6).** Nothing here is confirmed. Confirmation is D009 H-X, live on Season A + B. Spec: `registry/D010_exploration_options_v1.md`, implemented unchanged. Raw data in `raw/`, code `run_d010.py` (deterministic: two runs gave byte-identical `results.json`).

## Headline

- **Selling the straddle at the bid and buying it back at the ask lost money.** X1 mean `short_exec` = **-3.22%** per $1 of spot (t = -19.02, n = 1249, 233 R dates). Hit rate 32.7%, median -1.80%.
- **Buying it lost more.** X2 mean `long_exec` = **-4.03%** (t = -20.14). Both sides lose to spreads: the mid-price short return is only 0.40%, so the whole edge is smaller than the round-trip spread cost.
- Implied move averaged 11.6% of spot vs a realised 7.4% (realised/implied = 0.64 on means, 0.68 mean of ratios): the straddle was priced richer than the move on average, but not by enough to pay the spread.
- **Tail:** worst 1% of short trades = -25.52%, CVaR 5% = -21.22%, largest single loss = -41.93% of spot. Dropping the 13 largest |returns| leaves mean -2.93% (t = -18.40).
- **Findings meeting the rule (q < 0.10 AND |t| > 3 AND same sign in 2019–2022 and 2023–2026): NONE.** The one-sided tests are all in the "selling pays" direction (X2: "buying pays"), so a strongly negative t gives p ≈ 1.

## ⚠ Data coverage — read this before trusting any number

- DoltHub `earnings_calendar` has **no rows before 2020-01-22**, so 2019 has zero events (X6a untestable).
- The DoltHub `option_chain` has **gaps: whole dates missing** (e.g. nothing at all on 2022-02-01) and thin pre-2025 coverage of our names. Of 7107 events, only **1249** had every quote needed. Valid by year: 2020: 4, 2022: 5, 2023: 12, 2024: 142, 2025: 628, 2026: 458.
- So the result is **dominated by 2025–2026 (1086 of 1249 events)**; 2019–2023 has only 21 valid events, so the two-halves test is nearly one-sided in sample. Missing quotes are not random (dates and names the source skipped), so the sample is a survivor of the data source on top of the disclosed universe survivorship.
- Chain extraction kept rows with 0.25 ≤ |delta| ≤ 0.75 (spec §7 allowance); the traded contract's exact quotes on P and Q were pulled without a delta filter. Quotes are end-of-day as published.

## Events and voids (every reason, by year)

Calendar rows excluded: {'bmo_D_not_a_session': 0, 'duplicate_symbol_R': 0, 'no_session_data': 0, 'when_other_or_missing': 211}. Events built: 7107 (2020: 870, 2021: 909, 2022: 967, 2023: 1104, 2024: 1133, 2025: 1197, 2026: 927).

| void reason | total | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|
| crossed | 3 | 0 | 0 | 0 | 0 | 1 | 1 | 1 |
| no_expiry | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 0 |
| no_quote | 5853 | 866 | 909 | 962 | 1090 | 990 | 568 | 468 |
| split | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

`no_quote` breakdown (a data-coverage count, not an economic one): {'P_bid_nonpositive': 10, 'Q_leg_missing': 1749, 'no_P_chain_rows': 4088, 'spot_missing': 6}. `no_P_chain_rows` = no usable chain rows for that symbol on P; `Q_leg_missing` = contract not quoted on the reaction day; `spot_missing` = no yfinance close.

Implied-straddle tercile cut points (full sample): 9.19% and 12.39% of spot.

## All 22 tests (BH-FDR over all 22)

| id | sample | n | R dates | mean | t | p | BH q | hit rate | median | worst 1% | CVaR 5% | largest loss | mean short_mid | mean ratio | mean w/o top 1% | halves (19-22 / 23-26) | finding |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| X1 | all events | 1249 | 233 | -3.22% | -19.02 | 1.000 | 1.000 | 32.7% | -1.80% | -25.52% | -21.22% | -41.93% | 0.40% | 0.68 | -2.93% | -1.73% / -3.23% | no |
| X2 | all events | 1249 | 233 | -4.03% | -20.14 | 1.000 | 1.000 | 18.0% | -3.80% | -21.42% | -17.90% | -29.43% | 0.40% | 0.68 | -3.82% | -1.29% / -4.05% | no |
| X3a | cluster ai_infra (insufficient) | 12 | 12 | -1.86% | -0.73 | 0.759 | 1.000 | 50.0% | 0.03% | -24.68% | -26.50% | -26.50% | 1.47% | 0.51 | 0.37% | n/a / -1.86% | no |
| X3b | cluster consumer | 202 | 118 | -1.95% | -6.19 | 1.000 | 1.000 | 43.6% | -0.60% | -13.83% | -13.01% | -16.28% | 0.77% | 0.66 | -1.75% | 0.60% / -1.97% | no |
| X3c | cluster crypto_proxy (insufficient) | 0 | 0 | n/a | n/a | 1.000 | 1.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a / n/a | no |
| X3d | cluster drones_robotics_space_defense | 101 | 74 | -2.49% | -5.83 | 1.000 | 1.000 | 26.7% | -1.03% | -17.70% | -14.74% | -22.02% | 0.12% | 0.69 | -2.14% | -3.97% / -2.44% | no |
| X3e | cluster hardware_networking | 197 | 109 | -4.25% | -9.13 | 1.000 | 1.000 | 31.0% | -2.62% | -25.66% | -23.53% | -41.93% | 0.18% | 0.67 | -3.94% | 1.15% / -4.28% | no |
| X3f | cluster healthcare_growth | 145 | 89 | -3.49% | -8.05 | 1.000 | 1.000 | 27.6% | -2.22% | -24.17% | -20.05% | -33.79% | -0.16% | 0.76 | -3.11% | -5.62% / -3.48% | no |
| X3g | cluster semis | 244 | 102 | -2.90% | -7.19 | 1.000 | 1.000 | 36.5% | -1.34% | -26.37% | -22.98% | -31.55% | 0.69% | 0.64 | -2.56% | -0.21% / -2.92% | no |
| X3h | cluster software_internet | 348 | 122 | -3.75% | -11.02 | 1.000 | 1.000 | 28.2% | -2.03% | -24.35% | -22.24% | -39.12% | 0.40% | 0.70 | -3.44% | n/a / -3.75% | no |
| X4a | implied tercile 1 | 417 | 171 | -2.66% | -11.34 | 1.000 | 1.000 | 29.0% | -1.70% | -17.31% | -15.06% | -28.62% | -0.32% | 0.75 | -2.42% | -1.38% / -2.67% | no |
| X4b | implied tercile 2 | 416 | 138 | -3.96% | -12.56 | 1.000 | 1.000 | 30.5% | -2.11% | -26.01% | -23.16% | -41.93% | -0.01% | 0.71 | -3.63% | -2.67% / -3.98% | no |
| X4c | implied tercile 3 | 416 | 142 | -3.04% | -9.25 | 1.000 | 1.000 | 38.7% | -1.43% | -26.34% | -23.13% | -39.12% | 1.55% | 0.59 | -2.70% | 0.60% / -3.05% | no |
| X5 | top − bottom tercile (two-sided) | 833 | 211 | -0.39% | -1.02 | 0.307 | 1.000 | – | – | – | – | – | – | – | – | 1.98% / -0.38% | no |
| X6a | year 2019 (insufficient) | 0 | 0 | n/a | n/a | 1.000 | 1.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a / n/a | no |
| X6b | year 2020 (insufficient) | 4 | 2 | -2.26% | -1.02 | 0.753 | 1.000 | 75.0% | 0.60% | -11.05% | -11.41% | -11.41% | -0.60% | 0.60 | 0.78% | -2.26% / n/a | no |
| X6c | year 2021 (insufficient) | 0 | 0 | n/a | n/a | 1.000 | 1.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a / n/a | no |
| X6d | year 2022 (insufficient) | 5 | 4 | -1.31% | -1.22 | 0.845 | 1.000 | 40.0% | -0.91% | -5.48% | -5.62% | -5.62% | 0.09% | 0.65 | -0.23% | -1.31% / n/a | no |
| X6e | year 2023 (insufficient) | 12 | 6 | -2.44% | -2.87 | 0.983 | 1.000 | 25.0% | -1.55% | -8.90% | -8.97% | -8.97% | -0.27% | 0.85 | -1.85% | n/a / -2.44% | no |
| X6f | year 2024 | 142 | 29 | -2.79% | -7.37 | 1.000 | 1.000 | 38.7% | -1.30% | -26.55% | -20.86% | -31.32% | 0.56% | 0.69 | -2.42% | n/a / -2.79% | no |
| X6g | year 2025 | 628 | 114 | -3.06% | -12.50 | 1.000 | 1.000 | 35.4% | -1.47% | -25.19% | -22.02% | -41.93% | 0.36% | 0.70 | -2.75% | n/a / -3.06% | no |
| X6h | year 2026 | 458 | 78 | -3.62% | -13.10 | 1.000 | 1.000 | 27.1% | -2.26% | -23.61% | -20.17% | -39.12% | 0.45% | 0.65 | -3.34% | n/a / -3.62% | no |

Statistic: X2 rows use `long_exec`; all others `short_exec`. Hit rate, median, worst 1%, CVaR 5% and largest loss are for the test's own statistic (for X2 that is `long_exec`). X5 detail: top tercile mean -3.04%, bottom tercile mean -2.66%.

## Choices the spec left open (fixed before looking, stated here)

- **bh**: Benjamini-Hochberg over all 22
- **finding_rule**: q<0.10 and |t|>3 and same sign (as overall) in R 2019-2022 and 2023-2026 and not insufficient
- **insufficient**: n<30 or R dates<10
- **p**: t with G-1 df (one-sided for gt, two-sided X5); untestable = 1.0
- **se**: CR0 cluster-robust by R date
- CVaR 5% = mean of values at or below the 5th percentile; worst 1% = the 1st percentile; "without top 1%" drops ceil(1% × n) events with the largest absolute statistic.
- Untestable cells (n = 0) are reported as missing, carry p = 1 in the BH count, and cannot be findings.

## Margin note (spec §4)

A short straddle needs margin of roughly 15–25% of spot. Returns per dollar of margin are about 4–6× the per-spot figures above — and so are the losses. On X1 that would turn a -3.22% per-spot mean into roughly -12.89% to -19.33% on margin, with the 1%-worst tail at -102% to -153% of margin.

## What it means

On this (gappy, 2025-heavy) sample, **neither side of the end-of-day earnings straddle pays after real bid/ask costs**; the mid-price short edge is near zero. This does not support selling or buying the straddle as a strategy. It is exploration on a source with serious coverage gaps; the live D009 H-X test is the only place it can be confirmed.
