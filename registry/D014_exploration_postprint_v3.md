# D014 · v3 — the retail entry: what a moomoo SG account can actually get

> **Frozen 2026-10-13 ET, about 12:40 ET (00:40 SGT on the 14th), while v1's fetch was still running.** No D014 reaction-day number had been read: v1 and v2 had not been analysed, and no return
> had been printed.
> **D014 v1 and v2 are untouched.** v3 adds **no hypothesis test**. It prices v1 and v2 survivors at an
> entry a retail account can reach, and labels whether they survive it.

## 0. Why

- **moomoo SG documents no opening-auction order.** Its US order types are Limit, Market and
  Market-On-Close; conditional, combination and algo orders; no MOO, LOO or OPG.
  - A market order placed pre-market is held and sent to continuous trading.
  - **Source:** moomoo's manual and help centre, checked by the DRIVE chat on 2026-10-14 and passed on by
    Jacob: https://www.moomoo.com/sg/manual/topic-14-376 and https://moomoo.com/sg/support/topic5_84
- **So v1's entry is an upper bound for this account.** v1 enters at the official opening auction print.
- **The exit at the close is reachable** (moomoo lists Market-On-Close), so it stays an auction.

## 1. The retail entry

Two inputs per event:
- **The entry minute:** the first regular 1-minute bar starting at or after the minute of the official
  open `o_t` (v1 §3), and before 09:50 ET.
  - `vw` = its volume-weighted average price, Alpaca's bar field `vw`.
- **The first quote:** the first NBBO quote at or after `o_t`, within 2 minutes.
  - `hs_first` = (ask − bid) / (2 · mid). This is the spread a market order meets as continuous trading
    starts, when spreads are widest.

Prices, with d = side · s the trade's direction (+1 a buy, −1 a short sale):

| price | definition |
|---|---|
| **entry, primary** | E = vw · (1 + d · hs_first): the first minute's average price, worsened by half the first quoted spread |
| exit at minute h | X = mid_h · (1 − d · hs_h), as in v1 |
| exit at the close | the closing auction P_c, with no spread (Market-On-Close) |
| **retail net** | d · (X / E − 1) − fee, with fee = 2 bp and, separately, 13 bp |

Shown beside the primary, descriptive only:
- **(a) upper bound:** v1's auction entry.
- **(b) plain VWAP:** vw, with no spread.
- **(c) the far side:** the first quote's ask for a buy, its bid for a short.

**Missing data:** a missing `vw` or first quote means the retail net is missing for that event, counted.
An open at or after 09:50 has no entry minute and is counted.

## 2. What it decides

For every **group-mean** survivor of v1 (§6) and of v2 (§3), on its TRAIN side:

| label | condition |
|---|---|
| **executable (retail)** | the retail net at 2 bp is > 0 on TRAIN **and** on VALIDATION |
| **executable at small tickets** | the same at 13 bp |
| **auction-only** | anything else |

- An auction-only CANDIDATE is reachable only through a broker that documents opening-auction orders
  (e.g. POEMS or Interactive Brokers). Opening an account there is Jacob's call, and **no new money moves
  before paper results**.
- v1's delayed variant already enters at 09:35 by quote. It is unchanged.
- **Descriptive only**, whatever any verdict: the unconditional v1 cells y_5, y_10, y_30, y_60 and y_c,
  both sides, priced at entries v1, primary, (b) and (c). They show how much of an open-print edge
  survives a first-minute fill.

## 3. Files

- `analysis/d014/fetch_v3.py` reads v1's rows (`o_t`, the ticker, R and voids) and writes
  `raw/events_v3.csv` and `raw/manifest_v3.json`.
- `analysis/d014/run_d014_v3.py` imports v1's and v2's frozen code and writes `results_v3.json` and
  `REPORT_v3.md`.
- `tests/test_d014_v3.py`.
- `.github/workflows/d014-v3.yml`.
- All are hashed in `registry/D014_implementation_v3.sha256` before v1's analyse step runs.
- **Run order:**
  1. v1 fetch → v1 analyse
  2. v2 fetch → v2 analyse
  3. v3 fetch → v3 analyse
