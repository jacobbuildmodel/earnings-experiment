# D001 · Trade mechanics and outcome · v1 — FROZEN 2026-09-16

> **Frozen before any trade.** Rule 2: the primary exit and the WIN definition never change after the
> first trade. A change creates `D00x_outcome_v2` with its own clock; v1 keeps being scored untouched.
> This file's SHA-256 is recorded in `registry/FROZEN.sha256` and checked by `check.py` every session.
> Machine-readable twin: `registry/D001_outcome_v1.json`. If the two ever disagree, this file wins and
> the disagreement is logged as a defect.

## Source — Jacob, 2026-09-16, verbatim

> *"a, (typically yes) but if its that simple everyone will be a perfect at prediction so this is up for
> experiementation what actually cause a price to increase a win to me is basically the share price go
> the desired direction as expected by the model … yes, draft."*

| # | question (FRAMEWORK v0.1 §12) | answer |
|---|---|---|
| 1 | primary exit | **A** — first open after the print |
| 2 | primary outcome = excess return? | **No.** Raw direction: the price went the way the model expected |
| 3 | "bmc" means BMO | **yes** |
| 7 | industry allowlist | **the §10 draft** → frozen separately as `D002_universe_allowlist_v1.md` |

Decided by Claude on 2026-09-16, within Jacob's answer, and recorded here so they cannot drift:
"above" means **above zero** (a cost-adjusted result is a secondary), and **"the open" is the official
opening price** (evidence below).

## 1. Timing

A **session** is a regular NYSE/Nasdaq trading day, 09:30–16:00 US Eastern.

| print | entry | exit A (PRIMARY) | exit B (secondary) | exit C (secondary) |
|---|---|---|---|---|
| **BMO** on session D | open of D−1 | **open of D** | close of D | close of D+5 |
| **AMC** on session D | open of D | **open of D+1** | close of D+1 | close of D+6 |

- **Reaction day** = the first session that trades after the print (BMO: D · AMC: D+1). Exit C is the
  close of the 5th session after the reaction day.
- The date and session come from the frozen universe, confirmed from two sources, one of them the company.
- A print that lands **during** a session (09:30–16:00 ET) is not BMO or AMC → the event is **VOID
  (intraday print)**.

## 2. Prices

- **"The open" = the official opening price**: the daily-bar Open, which is the opening-auction print
  a market-on-open order receives. It is **not** the first trade of the 09:30 one-minute bar.
  *Evidence:* CPRT 2026-09-11. yfinance daily Open is 32.01 and Alpha Vantage `TIME_SERIES_DAILY` open
  is 32.01, while the 09:30 bar opened at 31.76 and traded up to 32.02
  (`analysis/exploratory/2026-09-13_source_probes/13_open_price_CPRT_2026-09-11.txt`).
- **"The close" = the official closing price**: the daily-bar Close.
- **Primary source:** yfinance `history(auto_adjust=False)` — unadjusted Open and Close.
- **Check source:** Alpha Vantage `TIME_SERIES_DAILY` for the same date. They **agree** when they differ
  by ≤ 0.10% or ≤ $0.01. On agreement the event is graded on the primary value. On disagreement, both
  values are stored, the event is flagged `price_dispute`, and it is graded on the primary value. Every
  result is also reported with the `price_dispute` events removed. With no check value within 5 sessions,
  the event is flagged `single_source`.
- Prices are rounded to **4 decimal places** before any comparison, which removes vendor float noise
  (32.009998 → 32.0100).
- **Fetch once, never overwrite.** Each price is stored with its source and fetch time (ET). A later
  correction is a new row that carries a reason. The old row stays.
- No price for an exit (trading halt, delisting) → use the next official open or close, and flag
  `exit_delayed`. No price ever → **VOID (no price)**.

## 3. Corporate actions inside the window

- **Split** between entry and exit → the entry price is divided by the split ratio. Flag `split_adjusted`.
- **Cash dividend** with its ex-date after entry and on or before the exit → the dividend is added to the
  exit price. Flag `dividend_adjusted`.

## 4. The outcome — computed by code, never judged

```
raw_return   = exit_price / entry_price − 1          (per exit; A is primary)

WIN_raw      = raw_return > 0                          ← PRIMARY (exit A)
  BUY    is correct  ⇔  WIN_raw
  NO_BUY is correct  ⇔  not WIN_raw                    (a price exactly unchanged counts against a BUY)

WIN_net      = raw_return > 0.0020                     secondary — a 20 bp round-trip cost
WIN_excess   = raw_return − beta × bench_return > 0    secondary — beat its own sector
```

- **The WIN_excess benchmark** is the FRAMEWORK §2 method: a sector ETF, beta, and leave-one-out when
  the stock is a material weight in that ETF. The ETF mapping, the beta window and the weight threshold
  are frozen **with the universe**, before the first event. Whether WIN_excess explains outcomes better
  than WIN_raw is itself a question for the study. It is never a way to re-score.
- Secondary exits (B, C) and secondary outcomes (net, excess) are recorded on **every** event and always
  **labelled secondary**. None of them can ever be promoted to primary for v1.

## 5. ⚠ The bar to beat is T0, not 50%

A raw price rise includes the **whole market's move** over the holding window: one session plus the
overnight gap. In a rising market most buys "win" whatever the model does. So:

- **T0 hit rate** = the share of all eligible events with WIN_raw. This is the null.
- **Primary comparison:** a track's (T1, T2) **BUY-set hit rate minus the T0 hit rate on the same events**.
  This is the selection lift. A track that beats 50% but not T0 has shown nothing.
- **Also reported:** BUY-set hit rate minus NO_BUY-set hit rate (separation), and NO_BUY accuracy.
- **Mean raw return** of each set is reported beside every hit rate. A rule that wins often but small and
  loses rarely but large is a finding, not a success.
- Rule 7 minimum: under 30 events **and** 10 event-dates, a result is **"insufficient"**.

## 6. VOID — recorded, never silently dropped

An event is VOID, keeps its row, and states its reason when:
- its freeze commit is timestamped **after** the entry open (rule 1)
- the print date or session differs from the frozen one
- the print lands intraday, or no price exists

Void counts are reported beside every result.
