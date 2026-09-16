# Source probes, 2026-09-13

What each data source **actually returned** when called. `FRAMEWORK.md` §8 rests on these results, and a
summary of Alpha Vantage's own documentation was wrong about several of them. Each file is the raw
response, recovered from the session record, with any API key masked and transient download links removed.

| # | call | returned | supports |
|---|---|---|---|
| 01 | `EARNINGS_CALENDAR` CPRT | a garbled reply, no rows | — |
| 02 | `EARNINGS_CALENDAR` AEO | one row, timing `post-market` | the calendar works on the free key |
| 03 | `EARNINGS_CALENDAR` all | 3,548 lines — too large to return inline; its preview is in `../2026-09-13_pilot_screen/` | the calendar; **962 of the 1,064 preview rows carry no BMO/AMC flag** |
| 04 | `HISTORICAL_OPTIONS` ORCL | error: *"This is a premium endpoint"* | ❌ historical options are blocked on the free key |
| 05 | `ETF_PROFILE` IGV | rate-limited, no data | untested |
| 06 | `EARNINGS` ORCL | 123 quarters back to 1996, each with `reportTime` (pre- or post-market) | earnings history with timing |
| 07 | `EARNINGS_ESTIMATES` ORCL | rate-limited | retried as #12 |
| 08 | `NEWS_SENTIMENT` ORCL | 34 articles with per-ticker sentiment and relevance scores | news sentiment works |
| 09 | `INSIDER_TRANSACTIONS` ORCL | transactions returned | insider trades work |
| 10 | `HISTORICAL_PUT_CALL_RATIO` ORCL | rate-limited | retried as #11 |
| 11 | `HISTORICAL_PUT_CALL_RATIO` ORCL, 2026-09-10 | full chain 0.60, plus a ratio per expiry | historical put/call works |
| 12 | `EARNINGS_ESTIMATES` ORCL | quarterly estimates back to 2017, with 7/30/60/90-day averages and revision counts | estimate history works |
| 13 | `TIME_SERIES_DAILY` CPRT + yfinance daily and 1-minute (added 2026-09-16) | both vendors give the 2026-09-11 open as **32.01**; the 09:30 bar opens at 31.76 | the daily Open is the official open — pinned in `registry/D001` |

## ⚠ The trap these files prove

For ORCL's quarter ending 2026-08-31, **#06 gives a consensus of 1.39 (reported 1.63, a +17.3% beat) while
#12 gives 1.74** — same vendor, same quarter, two numbers, most likely two EPS bases. No beat-rate or
surprise factor may be built until the basis is pinned; this is a next action in `STATE.md`.

## Free-key limits observed

25 calls a day and 1 call a second. Three of the calls above (#05, #07, #10) were rate-limited for firing
too fast — space every call and never run them in parallel.
