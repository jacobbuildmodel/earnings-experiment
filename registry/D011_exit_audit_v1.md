# D011 · exit audit · v1 — the on-time counterfactual next to every paper exit (descriptive, decides nothing)

> **Frozen 2026-10-14 ET**, after the DPZ incident (`ops/incidents/2026-10-13_DPZ_exit.md`).
> **Disclosed:** it was designed after seeing DPZ's first close attempt and the Oct 14 retry. It changes
> nothing in D011 v1 or v2, in their report (implementation v3), or in any result. It adds no test.

## Why

D011's report treats a trade as an on-time exit when its FIRST close order was sent inside the primary window
(14:30–15:00 ET), whenever that order, or a later one, filled. On 2026-10-13 the DPZ close was sent at 14:46
and did not fill. The position stayed open into the next day, and the stock fell about 4% more. **The
frozen report would count that trade as on time.** This audit makes the cost of a late or failed exit
visible, and Jacob asked for exactly that: evaluate each trade as though the exit had happened.

## Definitions (`pipeline/paper_exit_audit.py`)

These cover every trade in both ledgers (PX-F and PX-L) whose opening order filled and whose close was sent.
Conventions are the frozen D011 ones: per unit, debit positive, P&L = −(open net + close net).

| field | definition |
|---|---|
| on-time counterfactual, natural | P&L had the FIRST close filled at its own limit (the natural) when sent |
| on-time counterfactual, mid | the same, at the mid of the quotes recorded with that first close |
| exit spread cost | mid counterfactual − natural counterfactual |
| close filled | the fill time of the close (ET), `filled_same_day`, `filled_by_1500` |
| actual | `result.pnl_per_unit` from the frozen code (simulated legs labelled) |
| **delay cost** | actual − the natural counterfactual (negative = the late or failed exit cost money) |

Each is also shown per $1 of the gate spot.

## Use

- **Reported next to every D011 report**, labelled descriptive.
- **The PX-F and PX-L headline results stay the frozen ones.**
- If the delay cost is material across trades, the remedy is a NEW execution version for trades created
  after its freeze (rule 5), never a re-grading of past trades.
