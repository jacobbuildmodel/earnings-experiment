# D006 · History study procedure — how T1 rule v0 is built · DRAFT 2026-09-28

> The procedure, the factor list and the search log are fixed **before any history outcome is
> computed** (D005 v2 §7.1). When frozen this file moves to `registry/D006_history_study_v1.md`. The
> rule it produces is frozen separately as `registry/T1_rule_v0.json`, before 2026-10-12.
>
> Written 2026-09-28. At writing, no history return, hit rate or factor/return relation has been
> computed in this project. The retired model's archive was not read (rule 10). Reviewed the same day
> by an independent model (Sonnet, adversarial brief): 13 findings, all addressed in this text; the
> review is kept at `reviews/evaluations/2026-09-28_D006_review.md`.

## 1. What it produces

One mechanical rule, **T1 rule v0**: for each Season A event it outputs BUY or NO_BUY from factors that
code computes at the S2 snapshot. Code writes it into `decision.json → t1`. No AI touches it (D005 v2 §7.2).

Season A is exploratory for T1 (D005 v2 §7). Rule v0's job is to give T1 a real, pre-registered
record from the first full season, not to be right.

## 2. The history sample

**Companies.** Every ticker that passes D003 v2 S1 (industry map, named rules, exchange, domestic
filer) on a preview run with market data of 2026-09-28, plus the 12 pilot candidates.
- ⚠ **Survivorship, disclosed:** these are today's listed companies. Firms that delisted, were
  acquired or shrank below the size floor before today are missing. This is the universe the live
  experiment will trade; it is not the universe of each past date. D005 v2 §7.4 asks for the universe
  as of each date "where possible". The part that IS possible is done: size is tested as of each
  past event (below). Industry cannot be: Yahoo's classification is current-only.

**Events.** Every earnings print of those companies with a print date from **2022-09-01 to
2026-09-18** (ends before the pilot; D005 v2 §7.5). The first year serves only as ranking reference
(§5 step 2). An event needs, like a live event, two agreeing
sources for date and session:
1. **SEC:** an 8-K with Item 2.02, and its EDGAR `acceptanceDateTime` (ET):
   - accepted between 16:00 ET on session D−1 and 09:30 ET on session D → **BMO on D**
   - accepted between 16:00 ET on D and 09:30 ET on the next session → **AMC on D**
   - accepted during a session (09:30–16:00) → **INTRADAY → excluded**
2. **yfinance `get_earnings_dates`** timestamp, same session rule.
- **Agreement is on the trade, not the label.** AMC on D and BMO on the next session are the same
  trade: same snapshot, entry and exit A. An 8-K is often filed the morning after an evening
  release. So the two sources agree when they imply the same entry and exit sessions. The event
  takes yfinance's date and session, because the 8-K is a filing about the release.
- An 8-K accepted during the session → excluded (`intraday_8k`). No yfinance print with the same
  trade → excluded (`no_yfinance_same_trade`). This also drops Item 2.02 8-Ks that are not the
  quarterly print, such as preliminary results. Counted by reason.
- Requiring yfinance to agree is also the guard against a late 8-K. Disclosed.

**Size, as of the event.** Shares outstanding × the actual traded close of the snapshot session
(yfinance's split back-adjustment undone) ≥ $2B (the D003 v2 floor). The $10B healthcare floor and
other cluster floors apply the same way.
- **Shares:** the first **fresh** value — period end within 200 days of the snapshot, filed on or
  before it — of:
  1. `dei:EntityCommonStockSharesOutstanding`, summed over share classes
  2. `us-gaap:CommonStockSharesOutstanding`
  3. the latest quarter's `us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding`
- A stale value is never used. Some filers stopped tagging the cover page: ACMR's last `dei` value
  is from 2019, which would have put a $5B company at $0.1B.
- No fresh value → excluded (`no_pit_size`).

**Not reconstructible, disclosed:** the S2 option gate (implied move ≥ 4%, spread, open interest)
needs historical option chains we do not have. The history sample is therefore a **superset** of
what the live gate lets through. Robustness check (§6): the subsample whose average absolute exit-A
reaction over the previous four prints is ≥ 4% — a realised-move proxy for the implied-move gate.

## 3. Timing and outcome — D001 exit A, as in the live experiment

| session | snapshot session | entry | exit A |
|---|---|---|---|
| BMO on D | D−2 | open of D−1 | open of D |
| AMC on D | D−1 | open of D | open of D+1 |

- Prices: yfinance daily bars, `auto_adjust=False` (split-adjusted Open, dividends not added back —
  one overnight, disclosed).
- **WIN_raw = exit-A open > entry open.** raw_return = exit / entry − 1.
- A missing entry or exit bar → excluded (`no_price`).
- **Factors are computed from data available at the snapshot-session close.** Live, the snapshot is
  taken 14:30–15:50 ET, so history is up to ~2 hours later. Disclosed; no factor uses intraday data.

## 4. The candidate factors — fixed now, with the literature's sign

Every factor must be computable live at the snapshot from the same sources, by the same code
(source match, D005 v1 §5). Signs come from `reviews/literature_review.md` and are **not** estimated
from history.

**Point in time for filed data.** EDGAR `companyfacts` lists every value with the filing that
reported it (`filed`, `accn`), including the prior-year comparatives that later filings restate.
- Only values with `filed` ≤ the snapshot session are used.
- Where a period was reported more than once by then, the **most recently filed** of those values is
  used. That is what the market could read that day; a restatement filed after the snapshot cannot
  enter.
- Instant values (shares, assets) are those of the latest filing on or before the snapshot.

| id | factor | definition (as of the snapshot-session close) | sign | source of the sign |
|---|---|---|---|---|
| H1 | 12-month winner | close(snapshot) / close(snapshot − 252 sessions) − 1 | − | LR01 |
| H2 | 5-day pre-print pressure | close(snapshot) / close(snapshot − 5 sessions) − 1 | − | LR10 |
| H3 | lottery (MAX) | largest daily close-to-close return in the last 21 sessions | − | LR11 |
| H4 | volatility | annualised std of daily returns, last 60 sessions | − | low-volatility anomaly; LR08 lists volatility as one of its disagreement proxies. ⚠ H4 is **not** a test of LR08's disagreement channel, which needs dispersion and borrow cost |
| H5 | past announcement volume | mean, over the previous 4 prints in this sample's event list, of volume on the reaction day ÷ mean daily volume of the 250 sessions to the snapshot | + | LR02 |
| H6 | last quarter's surprise (SUE, seasonal random walk) | (EPS_q − EPS_q−4) ÷ std of that difference over the 8 quarters before, for the latest quarter filed before the snapshot. EPS = `us-gaap:EarningsPerShareDiluted`, 3-month facts (Q4 = annual − 3 quarters); needs ≥ 6 differences | + | LR17 |
| H7 | high-seasonality quarter | the quarter about to be reported (the one after the latest filed) had the highest mean diluted EPS of the four quarter positions over the last 3 fiscal years → 1, else 0 | + | LR18 |
| H8 | value (sales-to-price) | TTM revenue ÷ PIT market cap. Revenue = the D004 §4 tags plus `RevenueFromContractWithCustomerIncludingAssessedTax`, first with a value per quarter | + | LR20 (⚠ LR20's evidence is about asymmetric reactions; H8 tests only the direction) |
| H9 | scheduled later than last year | (this print date − the same fiscal quarter's print date a year earlier) − 364, in days | − | LR23 |
| H10 | operating profitability | TTM `OperatingIncomeLoss` ÷ latest `Assets` | + | profitability premium (Novy-Marx 2013; Fama–French RMW); LR27: anomalies pay more on announcement days |

**Not in the list, and why:**
- **Options factors (LR12–LR16):** no historical chains. They are captured live from the pilot on, for rule v1.
- **Analyst revisions and dispersion (LR08, LR19):** free sources are current-only (D005 v2 §7.3).
- **Short interest, retail flow, sentiment, news tone (LR04, LR05, LR09, LR25, LR26):** paid, flaky or unprobed.
- **Same-day reporters, Friday, busy day (LR06, LR07, LR24):** these move the size of the reaction, not its sign.
- **Peer-driven pre-print move (LR21):** needs a peer set and the peers' print dates. The only mechanical
  peer set we have is the benchmark ETF, which mixes print-driven moves with everything else.
  Deferred to rule v1; the live factor snapshot records the stock's move since its peers' prints for that.
- **Yesterday's prints were good (LR22):** needs a market-wide surprise series on one EPS basis, which is
  not pinned (STATE). Deferred.
- **The LR27 composite:** H1, H8 and H10 are its parts. The R-LIT composite below already averages them,
  so a separate composite would count the same information twice.
- **Own past win rate:** no literature sign. Recorded, not used.

## 5. The procedure — code only

1. **Build** the event table and all H factors. Log the counts excluded at each step.
   - **Before D006 is frozen**, the build is run once and only its **counts** are published: events and
     print dates in TRAIN and VALIDATION, exclusions by reason, and missingness per factor by cluster
     and stage.
   - The build computes **no price after the snapshot**. `pipeline/history.py` refuses to compute any
     outcome until D006 is in `FROZEN.sha256`.
2. **Score — strictly backward-looking, exactly as live.**
   - For each event and factor: the percentile rank of its value within the **reference
     distribution**, flipped for a − sign, so that 1 = most favourable to BUY.
   - The reference distribution is that factor's values over all sample events whose snapshot session
     falls in the **four calendar quarters before** the event's own quarter.
   - Nothing from the event's own quarter or later enters its score. This is also exactly what the
     live rule does (§7).
   - To give the first TRAIN quarter a reference, events from **2022-09-01** onward are built. The
     2022-09-01 → 2023-08-31 events serve only as reference; they are never scored or tested.
   - A missing value scores 0.5 (neutral).
   - **An event with more than 5 of the 10 factors missing is not scored.** It is excluded from every
     test and counted by cluster and stage, because missingness is not random (young companies lack
     8 quarters of EPS).
3. **Split by print date:**
   - **TRAIN:** 2023-09-01 → 2025-08-31
   - **VALIDATION:** 2025-09-01 → 2026-09-18

   Nothing from VALIDATION is used before step 6.
4. **Univariate screen, TRAIN only — 10 tests, logged whatever the result.** For each factor:
   - lift = hit rate of events scoring > 0.5, minus hit rate of all scored events
   - its t and one-sided p: the D005 implementation (`pipeline/report.py`): OLS of WIN_raw on BUY,
     clustered by entry session, restricted wild cluster bootstrap-t, 9,999 draws, seeded
   - BH q-value across the 10
5. **Two candidate rules, weights never fitted:**
   - **R-LIT:** composite = mean of all 10 scores.
   - **R-SEL:** composite = mean of the scores of the factors that pass the **rule 7 exploration bar on
     TRAIN**: lift > 0, **t > 3 and BH q < 0.10**. If none passes, R-SEL does not exist, which is the
     likely outcome and is reported as such.
   - **BUY threshold:** an event is BUY if its composite exceeds the **median composite of its reference
     distribution** (the same four prior quarters). The rule buys about half the events by
     construction. That keeps T1 comparable with T0, whereas a fixed 0.5 cut on a mean of ranks would let
     the BUY share drift with factor correlations.
   - **BUY share tripwire:** the BUY share of each rule on TRAIN and VALIDATION is reported. Outside
     30–70% is flagged in the report. It is not a reason to change the rule.
6. **Validation — 2 tests, the only look at VALIDATION.** For each rule, over all scored VALIDATION
   events (the T0 bar):
   - hit-rate lift over T0
   - return lift
   - bootstrap t (D005 method)
7. **Choose rule v0:**
   - It is R-SEL if R-SEL exists and its VALIDATION hit-rate lift beats R-LIT's.
   - Otherwise it is **R-LIT**, including when both lifts are ≤ 0.
   - A rule with VALIDATION lift ≤ 0 is still frozen and scored live, labelled **"failed validation"**.
     An honest, zero-snooping T1 track is worth more than a gap. The label travels with every report.
   - **Winner's curse:** when both rules exist, rule v0's VALIDATION number is the better of two. It is
     reported as a selected-winner estimate, expected to overstate the true edge, and never as a
     forecast for Season A.
8. **Report** in `analysis/history/report.md`:
   - every number from steps 4–7, with n and the number of print dates
   - the BUY shares
   - descriptive splits, not tests: by cluster, by stage, BMO/AMC, and the ≥ 4% realised-move
     subsample
   - exclusion counts and missingness by cluster and stage
   - the rule 7 verdict wording: "insufficient" wherever a cell has under 30 events or 10 dates
   - the disclosures of §2 and §3

## 6. Search log and test count (rule 7)

- `analysis/history/search_log.json` records every computation in steps 4–7, including any re-run
  after a bug fix (with the diff and reason).
- **Total tests: 10 univariate + 2 validation = 12.**
- **A bug fix is not a new search.** A fix that changes any number is logged, and the whole pipeline
  re-runs from step 1. Changing a definition in §4 or §5 after results are seen is **not allowed**. It
  would need a D006 v2 and a new rule version with its own clock.

## 7. Live use

- `T1_rule_v0.json` holds:
  - the 10 definitions
  - the chosen rule
  - the frozen reference: each factor's values over the **last four calendar quarters of the history
    sample**, and the median composite. This is the §5 step 2 method; the reference just stops moving
    at the freeze.
- Live factors are computed at the snapshot by the same code (`pipeline/history_factors.py`), from the
  same sources. T1 is written by code, never by the AI.
- An event with more than 5 of 10 factors missing live gets T1 = null with the reason, never guessed.
- **The reference belongs to this universe.** If D002 or D003 changes the universe materially (for
  example CHARTER I1, widening the allowlist), rule v0's reference is stale. Scoring a new universe
  needs a new rule version with its own reference and clock. Rule v0 keeps being scored only on events
  its universe would have admitted.

## 8. Disclosures carried into every report

- **Survivorship:** today's listed companies (§2).
- **No option gate** in history: the sample is a superset of what the live gate admits (§2).
- **Two-source agreement is easier in history than live.** yfinance's past timestamps have had time to
  be corrected, so the history exclusion rate understates what the live gate will see.
- **Universe preview vs the frozen screen:** the history universe comes from a D003 v2 run on
  2026-09-28 market data, not the Season A screen of 2026-10-09, which does not exist yet. The two are
  compared once the screen exists, and the differences are listed. The rule is not re-run.
- **Close vs the S2 window:** history factors use the snapshot-session close; live uses 14:30–15:50 ET.
