# D010 · Exploration batch 2 · v1 — FROZEN 2026-10-08 (ET) · the earnings straddle on history, 2019–2026

> **Frozen before any option price is pulled.** Only schema and coverage were probed: table and column
> names, and which expirations exist for one ticker on one date.
> **This is EXPLORATION (rule 6).** It cannot confirm anything. Its confirmation is already registered
> live: D009 H-X, the exact short straddle on Season A + B. A D010 finding is a candidate and the
> motivation for that track.
> Machine-readable twin: `D010_exploration_options_v1.json`. This file wins on any disagreement.

## 1. Question

Jacob's purpose: what makes money around earnings. Two published facts disagree on how big the edge is:
- pre-announcement straddles earned **+3.34%** (Gao, Xing & Zhang 2018, V1): buyers underpay
- retail option buyers lose around earnings (de Silva, Smith & So 2025, *Review of Finance*; the size is
  V2 only): buyers overpay

**On our universe, after real bid/ask costs, does selling (or buying) the earnings straddle make money,
and where?**

## 2. Data (DoltHub `post-no-preference`, free)

- `options.option_chain`: date, act_symbol, expiration, strike, call_put, bid, ask, vol and delta.
  It holds about the three nearest expirations, weeklies included. Quotes are end-of-day, as published.
- `earnings.earnings_calendar`: act_symbol, date, `when` ("Before market open" / "After market close").
- **Underlying close:** yfinance daily `Close`, unadjusted, for strike checks and for scaling. Adjusted
  closes are used only for the stock leg.
- Each value keeps its source tier. A missing fetch is recorded as missing, never filled.

## 3. Events

- **Universe:** the 329 tickers of `analysis/history/universe.json` (D006).
  - **Survivorship disclosed:** these are names listed today, so the sample excludes companies that
    were delisted.
- **Period:** report dates from **2019-01-01 to 2026-09-18**, which is D006's history end. Season A
  stays out of sample.
- **An event** is one `earnings_calendar` row whose `when` is BMO or AMC. Rows with any other `when`,
  or none, are excluded and counted.
  - **R, the reaction session:** BMO → D; AMC → the next NYSE session after D.
  - **P, the pre session:** the last NYSE session before R. Its close is the entry.
  - **Q = R**, the exit at R's close.
- **Expiry:** the first listed expiration **strictly after R** in P's chain. If none exists, the event
  is VOID `no_expiry`.
- **Strike:** in P's chain for that expiry, the strike whose **call delta is closest to +0.50**. Ties
  take the lower strike. The same strike is used for the put.
- **Quotes needed:** call and put bid and ask, at that strike and expiry, on P **and** on Q.
  - Any missing quote, or a zero or negative bid on P → VOID `no_quote`.
  - Ask < bid on either date → VOID `crossed`.
  - Every void is counted by reason and by year.
- **Spot S_P:** the yfinance unadjusted close on P. A split between P and Q → VOID `split`.

## 4. Returns (per $1 of spot, so every event is on one scale)

| name | formula | meaning |
|---|---|---|
| `short_exec` | (callbid_P + putbid_P − callask_Q − putask_Q) / S_P | **primary**: sell at the bid, buy back at the ask |
| `long_exec` | (callbid_Q + putbid_Q − callask_P − putask_P) / S_P | buy the straddle, pay both spreads |
| `short_mid` | (mid_P − mid_Q) / S_P | no spread, an upper bound |
| `implied` | mid_P / S_P | straddle price as a % of spot |
| `realized` | \|S_Q − S_P\| / S_P | the move |
| `ratio` | realized / implied | descriptive |

**Disclosed:**
- A short straddle needs margin, roughly 15–25% of spot. Returns per dollar of margin are about 4–6×
  larger, and so are the losses.
- The left tail is fat, so every result reports it.

## 5. Tests — exploration family, all counted (rule 7)

The statistic is the mean, with a t clustered by **R date**. Each test is one-sided in the stated
direction (pre-stated, below), with BH-FDR across all of them.

**A finding needs all three:**
- BH q < 0.10
- |t| > 3
- the same sign in **both halves**: R in 2019–2022 and R in 2023–2026

| id | sample | statistic | direction |
|---|---|---|---|
| X1 | all events | mean `short_exec` | > 0 |
| X2 | all events | mean `long_exec` | > 0 (expected < 0) |
| X3a–h | each of the 8 D006 clusters | mean `short_exec` | > 0 |
| X4a–c | terciles of `implied` (cut points from the full sample, stated in the output) | mean `short_exec` | > 0 |
| X5 | top `implied` tercile minus bottom, on `short_exec` | difference | ≠ 0, two-sided |
| X6a–h | each calendar year 2019–2026 | mean `short_exec` | > 0 |

That is **22 tests**, the count for BH.

**Always reported beside each test:**
- n and the number of R dates
- the hit rate (`short_exec` > 0)
- the median
- the worst 1% and the CVaR at 5%
- the largest single loss
- `short_mid` and the `ratio`
- the result without the 1% largest absolute returns

## 6. What it can and cannot do

- **It cannot confirm.** D009 H-X (live, Season A + B) is the confirmation.
- A finding may motivate a new registered shadow or strategy version for a later season, with its own
  clock (rule 5).
- **It never touches T0, T1 or T2,** and its outcomes are never shown to T2.
  - Output goes to `analysis/d010/`, which is added to the T2 sparse-checkout fence with this freeze.

## 7. Implementation and who runs it

- **Who:** a claude.ai cloud session (Jacob's cloud credit, network Full), on branch
  `claude/d010-backtest`.
- **Code:** `analysis/d010/run_d010.py` implements §2–§5 exactly. It is reviewed on the laptop before
  merge.
- **Data access, in order:**
  1. `dolt clone` if the disk allows
  2. otherwise the SQL API **one date at a time for all universe symbols** (`WHERE date = … AND
     act_symbol IN (…)`, the primary-key prefix)
- **Raw extracts are saved** (`analysis/d010/raw/`), so the result is reproducible.
- The first run is the run. Re-running the same code on the same raw data must reproduce the numbers
  exactly. **No parameter is changed after a result is seen.** A change is a D010 v2.
