# D010 · Exploration batch 2 · v2 — FROZEN 2026-10-13 (ET) · hold-to-expiry, and the call–put IV spread

> **Frozen before any v2 statistic is computed.** What had been seen: D010 v1's report, and the review's
> post-hoc liquid cut, which is in `analysis/d010/REVIEW_2026-10-12.md`. Nothing in that review computed a
> hold-to-expiry return, an implied volatility, or a stock reaction against the call–put spread.
> Data seen without outcomes, on 2026-10-13: every one of v1's 1,249 valid events has a close row on its
> expiry date; the gap from R to expiry runs 1 to 57 days, median 15; the median R date is 2025-10-15; SPY
> is not in `raw/`.
> **EXPLORATION (rule 6).** It confirms nothing. Its job is to choose what Season B registers as
> confirmatory at Gate 1.
> v1 is unchanged: same data, same events, same strike and expiry. v2 adds two families.

## 1. Questions

1. **Y — does holding to expiry change the straddle's sign?**
   - v1 exited at the reaction-day close and paid a second spread there.
   - The live SH-X (D009) and H-XT (D012) hold to expiry and settle at intrinsic, paying one spread.
   - Measured on history, for both sides.
2. **Z — do option prices predict the stock's reaction direction?** The candidate is the call–put
   implied-volatility spread at the same strike (LR12):
   - Cremers & Weinbaum 2010, V1
   - Atilgan 2014, V1
   - Jin, Livnat & Zhang 2012, V1: the signal is strongest just before events
   - Our gates record it live as `B_iv_spread_call_minus_put_atm_LR12`.
   - This is the closest test in the backlog to the core question: which stocks to buy before the print.

## 2. Data and events

- **Events:** D010 v1's `events_valid.csv`, the 1,249 rows, with v1's strike K and expiry.
- **Option quotes:** v1's `raw/opt_p2.csv.gz`, the traded contracts on P.
- **Stock closes:** v1's `raw/prices.csv.gz`, unadjusted yfinance, with splits.
- **SPY:** yfinance daily `Close`, `auto_adjust=False`, 2019-12-01 to 2026-10-01.
  - Fetched once by the v2 code into `raw/spy_v2.csv` with a manifest, before any statistic is computed.
  - A missing SPY close on P or R → that event is VOID `no_spy` for family Z.
- **Splits:** any nonzero split strictly after P and on or before the last date used makes the event VOID
  `split` for that family. That date is the expiry for Y and R for Z.
- **Liquid**, exactly D012's rule: both ATM legs have (ask − bid) / mid ≤ 0.10 on P.
- **Near expiry:** expiry − R ≤ 7 calendar days, the weekly-option structure of the live gates.

## 3. Statistics (per $1 of spot S_P, the unadjusted close on P)

| name | formula |
|---|---|
| `short_hte` | (call bid_P + put bid_P − \|S_exp − K\|) / S_P, where S_exp is the unadjusted close on the expiry date |
| `short_hte_mid` | (call mid_P + put mid_P − \|S_exp − K\|) / S_P (descriptive) |
| `long_hte` | (\|S_exp − K\| − call ask_P − put ask_P) / S_P |
| `ivs` | IV(call mid_P) − IV(put mid_P) at strike K |
| `rx` | (close_R / close_P − 1) − (SPY_R / SPY_P − 1), the reaction-window excess over SPY |

**How `ivs` is computed:**
- Black–Scholes with r = 0 and no dividend.
- T = (expiry − P) in calendar days / 365, with the expiry at the close.
- Solved by Brent's method on [0.001, 20].
- Any of these makes `ivs` missing, and the event leaves family Z (counted):
  - a mid at or below intrinsic
  - a mid at or above the no-arbitrage upper bound
  - no root
- With r and dividends ignored, short-dated put–call differences carry a small level bias. It is common to
  all events, so it moves the regression's intercept, not its slope.

**ivs terciles:** cut points from the family-Z sample itself (it does not use outcomes); tercile 3 is the
richest calls.

## 4. Tests — two families, BH over all 9 together

| id | sample | statistic | H1 (one-sided unless stated) |
|---|---|---|---|
| Y1 | all | `short_hte` | mean > 0 |
| Y2 | liquid | `short_hte` | mean > 0 |
| Y3 | liquid and near | `short_hte` | mean > 0 |
| Y4 | all | `long_hte` | mean > 0 |
| Y5 | liquid | `long_hte` | mean > 0 |
| Z1 | all with `ivs` | slope of `rx` on `ivs` | > 0 |
| Z2 | all with `ivs` | mean `rx`, tercile 3 − tercile 1 | > 0 |
| Z3 | liquid with `ivs` | slope of `rx` on `ivs` | > 0 |
| Z4 | all with `ivs` | mean `rx` in tercile 3 | > 0 (does buying the rich-call names pay?) |

- **Standard errors:** CR0 cluster-robust by R date. Z2 is the slope on a top-tercile dummy, run on
  terciles 1 and 3 only.
- **p:** from t with G − 1 degrees of freedom. An untestable cell has p = 1.
- **Multiple testing:** Benjamini–Hochberg over all 9.
- **Finding rule, unchanged from v1:** q < 0.10 AND |t| > 3 AND the same sign in both halves AND not
  insufficient.
  - The halves are R < 2025-10-15 and R ≥ 2025-10-15. That is the median R date of the valid events,
    taken from dates alone, because v1's year halves are nearly empty before 2024.
- **Insufficient:** n < 30 or fewer than 10 R dates.
- **Reported per test:**
  - n, R dates, mean, median, t, p, q, hit rate
  - worst 1%, CVaR 5%, the largest loss
  - the mean without the 1% largest |statistic|
  - both halves
- **Also reported, descriptive:**
  - for Y: the voids by reason, and `short_hte_mid`
  - for Z: the share of events missing `ivs`

## 5. What it can and cannot do

- It **can** say which of these deserve a place in Season B's confirmatory family at Gate 1:
  - H-XT's structure, holding to expiry
  - the IV-spread signal, as a selector of which names T0 should buy
- It **cannot** confirm anything:
  - The sample is 2024–26-heavy.
  - DoltHub's coverage gaps make the events survivors of the data source.
  - End-of-day quotes are wider than live ones.
- **Expected and disclosed:**
  - Z has modest power. A published effect of ~+1.5% over 2 days, on terciles of ~400, with clustered
    daily noise, gives t of roughly 2–4.
  - Y's liquid cells are small (~170 events).

## 6. Implementation

- `analysis/d010/run_d010_v2.py` reads only `raw/` and `events_valid.csv`, and fetches SPY once. Two runs
  must give a byte-identical `results_v2.json`.
- Output: `analysis/d010/REPORT_v2.md`.
- No AI computes any number.
