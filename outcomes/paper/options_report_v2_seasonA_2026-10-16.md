# D011 paper report views - seasonA - 2026-10-16T21:19 ET

Descriptive, from `registry/D011_report_views_v1.md`. It adds no test and changes no rule. The D011 report of record stays `pipeline/paper_options_report.py`. Every number below is computed by code from the two paper ledgers and the stored real prints; the JSON beside this file holds the splits and every order.

Subsets: **all** = every trade; **v3 only** = `"exec": "v3"`; **without DPZ** = every trade except `seasonA-DPZ-2026-10-13-F`. Status follows rule 7 (under 30 trades or 10 entry dates = insufficient).

## 1. Fill rate (order records only)

### Opens

| account | subset | trades with an open order | filled at attempt 0 | at attempt 1 | open_failed: platform | other failure | pending |
|---|---|---|---|---|---|---|---|
| PX-F | all | 4 | 4 | 0 | 0 | 0 | 0 |
| PX-F | v3_only | 3 | 3 | 0 | 0 | 0 | 0 |
| PX-F | without_DPZ | 3 | 3 | 0 | 0 | 0 | 0 |
| PX-L | all | 3 | 2 | 0 | 1 | 0 | 0 |
| PX-L | v3_only | 3 | 2 | 0 | 1 | 0 | 0 |
| PX-L | without_DPZ | 3 | 2 | 0 | 1 | 0 | 0 |

### Open-fill trigger v1 (first 6 trades per account from snapshot 2026-10-16)

Order: first opening send, then the ledger order the frozen code sent in (one run stamps one time).

| account | counted | attempt 0 | attempt 1 | platform failures | other | pending | sent no order | state |
|---|---|---|---|---|---|---|---|---|
| PX-F | 3 of 6 | 3 | 0 | 0 | 0 | 0 | 0 | open: 3 of 6 decided |
| PX-L | 3 of 6 | 2 | 0 | 1 | 0 | 0 | 0 | open: 3 of 6 decided |

### Closes: the concession step at fill (v3), or unfilled by expiry

The 25% step covers the 6th order sent and every later one (the frozen ladder counts sent orders).

| account | subset | 0% | 5% | 10% | 15% | 20% | 25% | step unknown | unfilled by expiry | rejected | pending | v1 filled | v1 unfilled | other |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PX-F | all | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 1 | 0 |
| PX-F | v3_only | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 |
| PX-F | without_DPZ | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 |
| PX-L | all | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 |
| PX-L | v3_only | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 |
| PX-L | without_DPZ | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 |

## 2. P&L per $1 of spot at the fill and at three prices

Mean, every column over the same trades (those priced at all four). Mid = the middle of each recorded quote; halfway = half-way from the mid to the far side; natural = the far side. The quotes are those recorded when each order was sent.

| account | subset | sample | n | fill | mid | halfway | natural | $ at fill | $ at natural | not priced at all four | entry dates | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PX-F | all | real round trips | 0 | - | - | - | - | - | - | 0 | 0 | insufficient |
| PX-F | all | real, without exit_late | 0 | - | - | - | - | - | - | 0 | 0 | insufficient |
| PX-F | all | all with a result (simulated labelled) | 0 | - | - | - | - | - | - | 0 | 0 | insufficient |
| PX-F | v3_only | real round trips | 0 | - | - | - | - | - | - | 0 | 0 | insufficient |
| PX-F | v3_only | real, without exit_late | 0 | - | - | - | - | - | - | 0 | 0 | insufficient |
| PX-F | v3_only | all with a result (simulated labelled) | 0 | - | - | - | - | - | - | 0 | 0 | insufficient |
| PX-F | without_DPZ | real round trips | 0 | - | - | - | - | - | - | 0 | 0 | insufficient |
| PX-F | without_DPZ | real, without exit_late | 0 | - | - | - | - | - | - | 0 | 0 | insufficient |
| PX-F | without_DPZ | all with a result (simulated labelled) | 0 | - | - | - | - | - | - | 0 | 0 | insufficient |
| PX-L | all | real round trips | 0 | - | - | - | - | - | - | 0 | 0 | insufficient |
| PX-L | all | real, without exit_late | 0 | - | - | - | - | - | - | 0 | 0 | insufficient |
| PX-L | all | all with a result (simulated labelled) | 0 | - | - | - | - | - | - | 0 | 0 | insufficient |
| PX-L | v3_only | real round trips | 0 | - | - | - | - | - | - | 0 | 0 | insufficient |
| PX-L | v3_only | real, without exit_late | 0 | - | - | - | - | - | - | 0 | 0 | insufficient |
| PX-L | v3_only | all with a result (simulated labelled) | 0 | - | - | - | - | - | - | 0 | 0 | insufficient |
| PX-L | without_DPZ | real round trips | 0 | - | - | - | - | - | - | 0 | 0 | insufficient |
| PX-L | without_DPZ | real, without exit_late | 0 | - | - | - | - | - | - | 0 | 0 | insufficient |
| PX-L | without_DPZ | all with a result (simulated labelled) | 0 | - | - | - | - | - | - | 0 | 0 | insufficient |

### Paired (real round trips): each price on both sides

PX-F vs SH-X = paper - SH-X; PX-L vs SH-X = paper + SH-X (opposite sides); PX-F + PX-L = the same event on both accounts. Mean (n).

| pairing | subset | fill | mid | halfway | natural | status |
|---|---|---|---|---|---|---|
| PX-F vs SH-X | all | - (0) | - (0) | - (0) | - (0) | insufficient |
| PX-F vs SH-X | v3_only | - (0) | - (0) | - (0) | - (0) | insufficient |
| PX-F vs SH-X | without_DPZ | - (0) | - (0) | - (0) | - (0) | insufficient |
| PX-L vs SH-X | all | - (0) | - (0) | - (0) | - (0) | insufficient |
| PX-L vs SH-X | v3_only | - (0) | - (0) | - (0) | - (0) | insufficient |
| PX-L vs SH-X | without_DPZ | - (0) | - (0) | - (0) | - (0) | insufficient |
| PX-F + PX-L | all | - (0) | - (0) | - (0) | - (0) | insufficient |
| PX-F + PX-L | v3_only | - (0) | - (0) | - (0) | - (0) | insufficient |
| PX-F + PX-L | without_DPZ | - (0) | - (0) | - (0) | - (0) | insufficient |

## 3. Execution: each filled order against its own quotes

Share of the half-spread paid: 0 = filled at the mid, 1 = at the far side, above 1 = worse than the far side. The quotes are from the send; an order that rested before filling is compared with older quotes.

| account | subset | orders | mean share of half-spread paid | median | mean fill - natural | mean fill - limit |
|---|---|---|---|---|---|---|
| PX-F | all (open) | 4 | 0.96 | 0.97 | -0.178 | -0.178 |
| PX-F | all (close) | 0 | - | - | - | - |
| PX-F | v3_only (open) | 3 | 0.95 | 0.96 | -0.223 | -0.223 |
| PX-F | v3_only (close) | 0 | - | - | - | - |
| PX-F | without_DPZ (open) | 3 | 0.95 | 0.96 | -0.223 | -0.223 |
| PX-F | without_DPZ (close) | 0 | - | - | - | - |
| PX-L | all (open) | 2 | 0.94 | 0.94 | -0.050 | -0.050 |
| PX-L | all (close) | 0 | - | - | - | - |
| PX-L | v3_only (open) | 2 | 0.94 | 0.94 | -0.050 | -0.050 |
| PX-L | v3_only (close) | 0 | - | - | - | - |
| PX-L | without_DPZ (open) | 2 | 0.94 | 0.94 | -0.050 | -0.050 |
| PX-L | without_DPZ (close) | 0 | - | - | - | - |

## 4. Orders against real OPRA prints (Alpaca historical bars and trades)

Trades, not quotes: a check, not a fill model. Missing prints stay missing. Headline = legs with a real trade within 60 s of the fill; prints up to 15 min away are shown apart and are not simultaneous. Worse = the paper fill was worse for us than the print (+).

| account | subset | filled orders (fetched) | legs | trade within 60 s | mean worse, within 60 s | trade within 15 min | mean worse, within 15 min | outside the bars' range | unfilled orders (fetched) | prints reached the limit (not simultaneous) |
|---|---|---|---|---|---|---|---|---|---|---|
| PX-F | all | 4 (1) | 4 | 0 | - | 1 | -0.050 | 1 | 28 (19) | 0 |
| PX-F | v3_only | 3 (0) | 0 | 0 | - | 0 | - | 0 | 0 (0) | 0 |
| PX-F | without_DPZ | 3 (0) | 0 | 0 | - | 0 | - | 0 | 0 (0) | 0 |
| PX-L | all | 2 (0) | 0 | 0 | - | 0 | - | 0 | 2 (0) | 0 |
| PX-L | v3_only | 2 (0) | 0 | 0 | - | 0 | - | 0 | 2 (0) | 0 |
| PX-L | without_DPZ | 2 (0) | 0 | 0 | - | 0 | - | 0 | 2 (0) | 0 |

## 5. Per trade

| account | trade | exec | open | close | P&L/spot fill | mid | halfway | natural | simulated |
|---|---|---|---|---|---|---|---|---|---|
| PX-F | seasonA-DPZ-2026-10-13-F | v1 | filled_attempt_0 | unfilled by expiry (v1) | - | - | - | - | - |
| PX-F | seasonA-NOC-2026-10-20-F | v3 | filled_attempt_0 | pending: no close sent yet | - | - | - | - | - |
| PX-F | seasonA-RTX-2026-10-20-F | v3 | filled_attempt_0 | pending: no close sent yet | - | - | - | - | - |
| PX-F | seasonA-VICR-2026-10-20-F | v3 | filled_attempt_0 | pending: no close sent yet | - | - | - | - | - |
| PX-L | seasonA-NOC-2026-10-20-L | v3 | open_failed: platform | no real position | - | - | - | - | - |
| PX-L | seasonA-RTX-2026-10-20-L | v3 | filled_attempt_0 | pending: no close sent yet | - | - | - | - | - |
| PX-L | seasonA-VICR-2026-10-20-L | v3 | filled_attempt_0 | pending: no close sent yet | - | - | - | - | - |
