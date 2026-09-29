# History study — result (D006 v1, run 2026-09-29 after the freeze)

> Pre-pilot history, 2022-09 → 2026-09-18. **Exploratory.** Every number below comes from the
> frozen procedure; nothing here was tuned after seeing it. Search log: `search_log.json`.

## Verdict

**No selection rule built from these ten free factors beats buying every event.**
- No factor clears the rule 7 bar on TRAIN (lift > 0, t > 3, BH q < 0.10), so R-SEL does not exist.
- **Rule v0 = R-LIT, FAILED VALIDATION**: hit-rate lift -0.2 pts on TRAIN (t -0.13) and -0.7 pts on VALIDATION (t -0.45).
- As D006 §5.7 pre-committed, it is frozen anyway and scored live in Season A as a zero-snooping track.
- **The opponent is strong.** Buy-everything won 54.1% of TRAIN events and 54.2% of VALIDATION events. The mean exit-A return was +0.66% and +1.16%: the announcement premium, before costs.

## Step 4 — univariate screen, TRAIN (10 tests)

| factor | lift, pts | t | one-sided p | BH q | BUY share | return lift, pts |
|---|---|---|---|---|---|---|
| H1 | +2.95 | 2.56 | 0.0063 | 0.063 | 0.46 | +0.145 |
| H2 | +2.06 | 1.63 | 0.0565 | 0.283 | 0.47 | -0.103 |
| H3 | -1.93 | -1.40 | 0.9161 | 0.962 | 0.47 | -0.388 |
| H4 | -0.14 | -0.10 | 0.5379 | 0.897 | 0.48 | -0.414 |
| H5 | +0.59 | 0.60 | 0.2652 | 0.583 | 0.53 | +0.361 |
| H6 | -0.74 | -0.71 | 0.7573 | 0.947 | 0.50 | +0.042 |
| H7 | -1.29 | -0.65 | 0.7364 | 0.947 | 0.29 | -0.088 |
| H8 | +0.92 | 0.71 | 0.2391 | 0.583 | 0.48 | +0.066 |
| H9 | +0.50 | 0.54 | 0.2913 | 0.583 | 0.59 | +0.047 |
| H10 | -2.25 | -1.80 | 0.9623 | 0.962 | 0.47 | -0.612 |

- **Closest to the bar: H1**, the 12-month winner, with the literature's sign (−). Recent losers beat
  recent winners into the print by ~3 pts, but at t 2.6 and q 0.06 this is **a candidate, not a finding**.
- **The wrong way round:** H10 (profitability, t −1.8) and H3 (lottery, t −1.4) point against the literature.
  This is weak, and it is recorded as negative knowledge.

## Steps 5–7 — the rules

| rule | segment | n | entry dates | BUY share | T0 hit | BUY hit | lift, pts | t | return lift, pts |
|---|---|---|---|---|---|---|---|---|---|
| R-LIT | train | 1684 | 247 | 0.47 | 0.541 | 0.539 | -0.16 | -0.13 | -0.27 |
| R-LIT | validation | 1034 | 133 | 0.51 | 0.542 | 0.534 | -0.72 | -0.45 | -0.73 |

BUY-share tripwire (30–70%): not triggered.

## Descriptive, not tests — T0 hit rate by cluster (TRAIN + VALIDATION)

| split | n | T0 hit | R-LIT BUY hit | ≥ 30 events and 10 dates |
|---|---|---|---|---|
| cluster=ai_infra | 43 | 0.558 | - | yes |
| cluster=consumer | 436 | 0.555 | 0.554 | yes |
| cluster=crypto_proxy | 8 | 0.250 | 0.000 | insufficient |
| cluster=drones_robotics_space_defense | 278 | 0.586 | 0.581 | yes |
| cluster=hardware_networking | 348 | 0.586 | 0.566 | yes |
| cluster=healthcare_growth | 252 | 0.520 | 0.455 | yes |
| cluster=semis | 434 | 0.479 | 0.389 | yes |
| cluster=software_internet | 919 | 0.541 | 0.563 | yes |
| session=AMC | 1820 | 0.538 | 0.527 | yes |
| session=BMO | 898 | 0.548 | 0.555 | yes |

- **Semis were the one cluster where buying everything lost: 47.9%.** This is descriptive, found by
  looking, and therefore a candidate only (rule 6).

## Counts

`{"built": 3536, "with_prices": 3536, "no_price": 0, "unscored_missing_gt5": 247, "train": 1684, "validation": 1034}`

## Disclosures (D006 §8)

- **Survivorship:** the sample is today's listed companies.
- **No option gate:** the sample is a superset of what the live ≥ 4% implied-move gate admits.
- **Timing agreement:** easier in history than live, because yfinance's past timestamps have had time to be corrected.
- **Universe:** a 2026-09-28 preview, not the Season A screen.
- **Factor timing:** history uses the snapshot-session close; live uses the S2 window.
- **Dividends:** not added back (one overnight).
