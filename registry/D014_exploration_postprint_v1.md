# D014 · Exploration batch 3 · v1 — the first hour after the print, on history, 2022-09 → 2026-09

> **Frozen before any reaction-day price is pulled.** Reviewed before freezing by an Opus 5.5 agent (FREEZE
> WITH FIXES: the signal moved from the auction price to pre-market trades before 09:27, plus 10 smaller
> fixes, all applied). The only data probe ran on NON-event days
> (`pipeline/intraday_probe.py`, run 38413251458: SPY and AAPL on 2022-09-06, 2024-06-04 and 2025-03-04):
> it showed the Alpaca free plan serves SIP 1-minute bars back to 2022-09 with pre-market from 08:00 ET or
> earlier, NBBO quotes, and the official opening and closing auction prints.
> **This is EXPLORATION (rule 6).** It confirms nothing. A survivor is a CANDIDATE. Its confirmation is a
> separate, later registration (a live paper track on Season A's remaining events and Season B), frozen
> before that track's first reaction day.

## 0. Where the idea came from (disclosed)

- **Jacob**, passed on 2026-10-13 through a note from the DRIVE portfolio chat. The note held ideas and
  public papers only, with no holdings, accounts or ratings, so rule 9 is not touched. No DRIVE file was
  read.
  - Jacob's question: when a stock spikes or flushes after results, is the move justified? If not, can the
    first half hour (09:30–10:00 ET) capture it, by fading or following?
- **Literature (V2, not verified here):**
  - Intraday reversal about 30 minutes after BAD news (Euronext Paris, 2001–03, small sample).
  - Post-earnings drift is gone for large US stocks since 2006 (Martineau 2022, already in
    `reviews/literature_review.md`).
- **Rule 10:** a repo-wide text search on 2026-10-13 surfaced two lines of the fenced archive about
  "intraday" alpha. They are excluded. They did not shape any choice below. Every choice was fixed from
  the question and the data's shape.
- **The experiment's own primary exit is A**, the first open after the print. This batch starts exactly
  where exit A ends. It changes nothing in D001–D013.

## 1. Question

From the reaction session's official open, does an earnings stock **continue** its gap or **reverse** it
over the next 5, 10, 30 and 60 minutes and to the close? Does that depend on:
- the gap's size against the options-implied move
- whether the EPS surprise agrees with the gap
- the market's direction that morning
- good news vs bad news
- company size
- pre-market attention?

And after real spreads, can either side be captured?

## 2. Events

- **Events:** the 3,536 events of `analysis/history/graded_events.json` (D006): ticker, session, cluster,
  `exit_A` and `factors.market_cap_pit`.
  - R = `exit_A`, the reaction session.
  - R−1 = the session before R: the latest date before R with a SPY daily bar (Alpaca).
    `pipeline/sessions.py` lists only 2026–27 holidays, so it cannot be used for history.
  - The 20-session window for `PMV` is defined the same way.
  - **Survivorship disclosed:** these are names listed today.
- **Segments**, by R:

  | segment | R from | R to |
  |---|---|---|
  | TRAIN | 2022-09-01 | 2025-08-31 |
  | VALIDATION | 2025-09-01 | 2026-09-18 |

  VALIDATION is D006's. TRAIN also takes D006's 2022-09 → 2023-08 reference year, for power.
  **Nothing from VALIDATION is used before step 6.**
- Season A and later stay out of sample.

## 3. Data (Alpaca market data, free plan, feed `sip`, adjustment `raw`; every value keeps its source)

| field | definition |
|---|---|
| `C0` | R−1 close: the official closing auction price, the largest-size print in the auctions endpoint's closing list on R−1; else the R−1 daily bar close (labelled `c0_from_bar`) |
| `PM` | **the signal price:** the last trade before **09:27 ET** on R, when a market-on-open order can still be sent. It is the close of the latest 1-minute bar starting before 09:27, from R's pre-market (04:00 on) and, for AMC reporters, R−1's after-hours (16:00–20:00). It counts only at or after the minute of the release's SEC acceptance (`accepted_et`, when known), so a pre-release trade is never the signal. None → VOID `no_premarket` |
| `O` | R open, **the entry:** the official opening auction price, the largest-size print in R's opening list stamped 09:30 ET or later (an Arca early-open print is not the cross); else the open of R's first regular-session 1-minute bar (labelled `open_from_bar`). Its time `o_t` is kept |
| `P_h`, h = 5, 10, 30, 60 | the last trade at or before 09:30 + h ET: the close of the latest regular-session 1-minute bar starting before 09:30 + h. **Missing when the official open came at or after 09:30 + h** (a delayed opening), or when no bar exists since 09:30 |
| `P_c` | R close: the closing auction price as for `C0`; else R's last regular bar close (labelled) |
| quotes `hs_t`, `mid_t` | the last NBBO quote at or before t, within the 5 minutes before it, for t = 09:35, 09:40, 10:00 and 10:30. `hs` = (ask − bid) / (2 · mid). Missing, crossed or zero-bid → missing |
| attention `PMV` | the volume from R's 04:00 to 09:27, plus R−1's 16:00–20:00 for AMC reporters, divided by the mean daily volume of the 20 sessions before R (raw daily bars) |
| SPY | `C0`, `PM` (no release floor), `O`, `P_h` and `P_c` for SPY on R |
| surprise | yfinance `get_earnings_dates` `Surprise(%)` for the row whose ET date is the report date, taking the closest within ±1 day. **The EPS basis is vendor-defined** (STATE #2). A ticker that fails is retried on the next run. Missing stays missing |
| implied move `IM` | `implied` (the straddle mid at the pre-print close / spot) from `analysis/d010/events_valid.csv`, matched on (ticker, R), keeping only rows with strike/spot in [0.8, 1.25] (the D010 v2 scale fix). The straddle runs to the first expiry after R, so `IM` **overstates** the one-day priced move. Disclosed, not corrected |

**Voids**, counted by reason and by year:
- `no_c0` and `no_open`: no auction price and no bar.
- `no_premarket`: no signal price.
- `split`: the split-adjustment factor (raw close / split-adjusted close) differs between R−1 and R by more
  than 1%. A split check that cannot be made is counted as `split_unchecked` and does not void the event.
- `not_a_session`: R has no SPY daily bar.
- **Ticker changes:** a name that traded under another symbol earlier (XYZ was SQ) may return no bars
  before the change and is voided and counted. Accepted, disclosed.

**Fetch failures:**
- Each request is retried 3 times.
- A month with any failed bar, daily-bar or auction request is **not written**, so a rerun retries it.
- A failed quote stays missing.
- No value is ever filled.

## 4. Returns

- **The signal, known before the open:** g = PM / C0 − 1, and s = sign(g).
  - **Gap floor:** only events with **|g| ≥ 1%** are studied. A smaller gap is not a spike or a flush.
    Those below the floor are counted.
- **Continuation:**
  - y_h = s · (P_h / O − 1) for h = 5, 10, 30, 60
  - y_c = s · (P_c / O − 1)
  - **Positive = the stock kept going the pre-market gap's way after the open.** Negative = it reversed.
  - Entry is at the auction. Neither O nor anything after 09:27 is used to define s or a group.
- **Delayed variant:** y_d = s · (P_30 / P_5 − 1). Enter at 09:35, exit at 10:00.
- **Market-adjusted (secondary):** each y minus s · (SPY's return over the same window).
- **Costs (net returns), whichever side would be traded:**

  | | follow | fade |
  |---|---|---|
  | exit at minute h | s · (mid_h / O − 1) − hs_h − fee | −s · (mid_h / O − 1) − hs_h − fee |

  - Each exit is at the quote's mid less the half spread, since a last trade carries bid-ask bounce.
  - **Entry at the opening auction:** no spread.
  - **The close** is an auction: s · (P_c / O − 1) − fee, with no spread.
  - **Delayed variant:** s · (mid_10:00 / mid_09:35 − 1) − hs_09:35 − hs_10:00 − fee. Fade is the
    mirror.
  - **Fee:** a flat 2 bp per round trip, which is $1.98 on a $10,000 position at moomoo SG's $0.99 per
    order.
  - Missing quote → net missing for that event, counted.
  - **Not modelled, disclosed:**
    - short borrow (intraday only)
    - auction fill risk
    - market impact
    - the SEC and FINRA sell fees (well under 1 bp)
    - the noise of using one quote snapshot

## 5. Statistics (frozen)

- Every mean has a standard error **clustered by R** (CR1): many reporters share a morning.
- t = mean / SE. Two-sided p from the normal.
- **Rule 7:** under 30 events or 10 dates in a cell → "insufficient", and not tested.

## 6. Procedure

1. **Build.** Log counts per segment, voids by reason and year, events below the gap floor, split checks
   not made, and the coverage of IM, surprise, PMV and quotes.
2. **Descriptive, all segments.**
   - The distribution of |g|, of |g| / IM, and how often the open gap has the pre-market gap's sign.
   - The share of the reaction day's move reached by minute h: median |P_h / C0 − 1| / |P_c / C0 − 1| over
     events with |P_c / C0 − 1| ≥ 1%.
   - y by year and by cluster.
   - None of these is a test.
3. **The family: 42 tests on TRAIN, every one logged whatever the result.** Null: mean y = 0.

   | block | tests |
   |---|---|
   | unconditional | y_5, y_10, y_30, y_60, y_c (5) |
   | C1 big gap: \|g\| > IM | the same 5 horizons |
   | C2 surprise disagrees with the gap: sign(surprise) ≠ s, surprise ≠ 0 | 5 |
   | C3 market against: sign(SPY's PM / C0 − 1) ≠ s | 5 |
   | C4 bad news: s = −1 | 5 |
   | C5 mid-cap: market_cap_pit < $10B | 5 |
   | C6 high attention: PMV above its TRAIN median, taken separately for BMO and AMC reporters | 5 |
   | delayed variant y_d | unconditional and each of C1–C6 (7) |

   - C1–C6 are each a mean **inside the flagged group**: that group is what would be traded.
   - Every flag is known before 09:27. C1 uses PM's gap; C3 uses SPY's PM.
   - The complement group's mean is reported next to each, but not tested.
4. **A survivor on TRAIN** needs |t| > 3 **and** Benjamini–Hochberg q < 0.10 over the 42.
5. **Cost check on TRAIN**, survivors only. The traded side is follow if t > 0, fade if t < 0. Report its
   net mean, its CR1 t and its coverage.
6. **VALIDATION, the only look, survivors only.**
   - **CANDIDATE**: the same sign, a one-sided p (CR1) that stays < 0.05 after **Holm's correction across
     the survivors** (the horizons are nested, so they tend to survive together), **and** a net mean of the
     traded side > 0 on VALIDATION.
   - **Failed validation**: anything else. It is reported as negative knowledge.
   - **No survivor on TRAIN**: the verdict is "no first-hour pattern clears the bar". VALIDATION is still
     described, but not tested.
7. **The secondary**, market-adjusted y, is reported next to every primary number and decides nothing.

## 7. What a result means

- **A CANDIDATE** goes to Jacob with a proposal: a live paper track in shares on the Alpaca paper
  account. It would be automatic at the open, with its own registration frozen before its first reaction
  day.
  - **Options** (Jacob's short-dated puts) are a later probe only. Option spreads are widest at the open,
    and D010 found buying vol around prints loses after costs.
- **No candidate** is negative knowledge for the charter: "the first hour after a print is not
  capturable on our universe, on these conditioners, at this power".

## 8. Files

- `analysis/d014/fetch.py`: builds `analysis/d014/raw/events_intraday.csv.gz` plus a manifest. It holds
  derived per-event prices only, no raw bars.
- `analysis/d014/run_d014.py`: steps 1–7, writes `results.json`, `REPORT.md`. Deterministic.
- Both are hashed in `registry/D014_implementation_v1.sha256` before the fetch runs.
- Run by `.github/workflows/d014.yml` (workflow_dispatch), using the paper account's data keys.
