# D009 · Shadow tracks · v1 — FROZEN 2026-10-02 (ET), before the Season A screen (2026-10-09)

> **Why.** Power is the binding constraint (CHARTER §6.1). Checks on 2026-10-02 on the D006 history
> (2,771 prints, 385 entry sessions; exploratory; re-derived by an independent reviewer the same day):
> - **No statistical shortcut.** The net premium's clustered t is 2.76. Sizing each event by 1/volatility
>   lowers it to 2.11, because the premium sits in the more volatile names. Hedging SPY (2.25) or the
>   sector ETF (2.57) also lowers it, because each stock's own move dominates.
> - **Where power comes from.** Returns split into a part shared by every print on the same entry
>   session (sd ≈ 1.8–1.9%) and a stock-specific part (sd ≈ 9.2–9.6%). Below about 25 events per
>   session, more events help. Above that, **entry sessions bind**: a season has only ~29 of them.
> - **Expected t after one season, at the history premium (net +0.65%):**
>   - the gated track (~150 events, ~5 per session): about 0.8, so D008's Gate 2 test has little power
>   - the market-wide track below (~1,300 events): about 1.5, capped near 1.8 however many names are added
> - **The market-wide premium is likely smaller.** It covers every industry, and in history the
>   low-volatility half earned only about +0.07%.
> - **What follows:** the most information per season comes from many names on every session, measured
>   at no cost. These tracks do that, and capture what history cannot: the exact weekly straddle.
>
> **Status of everything here: SHADOW.**
> - Registered, frozen and graded by code, and reported like the scored tracks.
> - Labelled exploratory/secondary.
> - **Never** allowed to change a scored track, a gate, a T2 decision or D008 (CHARTER §3.8, rule 5).
> - Gate 1 (early Dec) may register one of them as confirmatory for Season B, as a new version with its
>   own clock.
>
> Code: `pipeline/shadow.py`, hash in `D009_implementation_v1.sha256`. Workflow:
> `.github/workflows/shadow.yml` (code only, no AI).

## 1. Common mechanics (all three tracks)

- **Trade.** D001 v1, unchanged: entry at the official open of the entry session; exit A at the
  official open after the print (BMO: D−1 → D; AMC: D → D+1).
  - **Price.** yfinance daily `Open`, `auto_adjust=False`, fetched once after 06:00 ET the next day
    (D001 §2), stored in `outcomes/shadow/<season>/prices.jsonl`.
  - **Dividends.** Cash dividends with entry < ex-date ≤ exit are added; the dividend field must have
    been read, never assumed 0.
  - **Splits.** A split in (entry, exit] → VOID `split_in_window`.
  - **Single source.** There is no second price, so every shadow return is `single_source`. Disclosed;
    not a void.
- **Net return** = raw − 0.20% (the D008 round trip). The return minus SPY over the same opens (beta 1)
  is recorded as a descriptive check that a result is not just the market.
- **Existence before entry (rule 1 for shadows).** An event counts only if every file that defines it was
  **committed before the entry open**; otherwise VOID `not_committed_before_entry`:
  - SH-W: its `confirm.json`
  - SH-M: the calendar capture **and** the season's S1 `yfinance_market.json`
  - SH-X: its `gate.json`
- **Print timing**, from the company's Item 2.02 8-K (SEC EDGAR acceptance time), for every track:
  - accepted in the frozen release window → `verified`
  - accepted in the opposite session's window → VOID `print_contradicted`
  - accepted before the window opens → VOID `print_early`
  - every 2.02 8-K at or after 16:00 ET of the reaction day (BMO: D; AMC: D+1) → flag `late_8k`. An 8-K
    may lag its release by up to four business days, so for SH-W and SH-M the event is **graded, flagged,
    and every test is also reported without these events**. **For SH-X it is VOID `print_late`**: a print
    after expiry would hand the short straddle a free premium.
  - otherwise (no 2.02 8-K, or one lagging its release inside the reaction day) → flag
    `timing_unverified`; graded; also reported without
  - a SEC fetch error is never final: the event stays ungraded and is retried
  - **SH-M only:** no CIK, or the latest periodic form filed on or before D is a 20-F/40-F → VOID
    `not_domestic_*`
  - share classes of one CIK on one date are one event (alphabetically first ticker)
- Outcomes live in `outcomes/shadow/`, which is never on disk for the T2 step (D004).
  - **Disclosed:** the T2 job checks out full git history, so these files, like the scored outcomes,
    are reachable through `git show`. Fenced by instruction and by the tool-call log, not by
    construction.

## 2. SH-W — T0-wide (the allowlist, gate or no gate) — DESCRIPTIVE

**Event.** Every `events/<season>/<T>_<D>/confirm.json`: a company-confirmed date and session (D003 §6),
whatever happened next.
- Included: gate PASS; gated out (implied move < 4%, thin open interest, wide spread, no options);
  **missed window**; T2 MISSING.
- Not events: dates that are PENDING, `unconfirmed` or `outside_window`, which have no `confirm.json`.
- SH-W ⊇ T0's PASS events.

Its net mean is reported with its t and p every run, but **it is not in the test family (§5)**. At ~250
events on ~29 sessions its expected t is about 1, so a test would spend Holm's alpha on almost no power.
It measures the premium over the whole allowlist, and it stops an infrastructure failure (a missed
window) from costing an observation.

## 3. SH-M — market-wide

**3.1 Universe** (fixed by the season's frozen S1 capture, rule 8). Every ticker in
`universe/<season>/raw/yfinance_market.json` (the D003 calendar union captured in the S1 slot) with:
- `quoteType` EQUITY
- exchange NYSE, Nasdaq or NYSE American
- currency USD
- `marketCap` ≥ $2B **at capture**
- not a D003 excluded ticker
- not "Shell Companies"

**Any industry**, and no implied-move or options condition.

**3.2 Dating, live.**
- `shadow.py capture` runs each session day and writes `shadow/calendar/<session>.json` once: the
  Nasdaq calendar for the next six weekdays.
- **Session** comes from Nasdaq's pre-market / after-hours flag. Where Nasdaq gives no time, one
  yfinance timestamped earnings date is used (CLAUDE.md: never `.calendar`), for rows Nasdaq sizes at
  ≥ $1.5B.
- **A failed fetch:** a capture in which any day failed is **not written**, and a later fire retries.
  The evening fire writes what it has, with `failed_days` flagged.
- **An SH-M event** is (name, D, session) **as listed in the capture taken on its snapshot session**: BMO
  D−2 sessions, AMC D−1 (the D003 S2 snapshot). With no capture that day or no session, there is no
  event. D must lie in the season window.

## 4. SH-X — the short straddle (CHARTER §4, RQ4)

**Event:** every `gate.json`, of any gate status, that recorded both ATM legs with bids.

**Trade:**
- Sell the gate's call and put at their **bids** at the snapshot.
- Hold to the gate expiry.
- Pay the intrinsic value |S − K| at the expiry session's official close.

**P&L** per $1 of spot = `(call_bid + put_bid − |S_close(expiry) − K|) / spot`. The mid-price version is
recorded as a secondary. The P&L is exact for European exercise held to expiry.

**Disclosed:**
- early assignment and margin are ignored
- clustering by entry session understates dependence between straddles whose lives overlap

## 5. Hypotheses, tests and verdicts — one family of exactly three, Holm-corrected

| id | hypothesis (one-sided) | sample |
|---|---|---|
| **H-M** | mean SH-M net return > 0 | graded SH-M |
| **H-X** | mean SH-X P&L on spot (bid) > 0 | graded SH-X |
| **H-VOL** | mean SH-M net return of events whose 60-session realised volatility to the snapshot session is above the sample's median, **minus** that of the rest, > 0 | graded SH-M with volatility |

- **H-VOL is a candidate found by looking.** On 2026-10-02 the D006 history showed the premium larger in
  the more volatile names. Volatility-quintile means: TRAIN +0.4 / −0.2 / +0.8 / +1.4 / +1.0%;
  VALIDATION −0.3 / +1.1 / 0.0 / +3.0 / +1.8%. The median split gave +1.2 pts at t 2.9, inflated by
  the winner's curse. History ends 2026-09-18, so Season A is out of sample (rule 6).
- **Volatility definition:** `history_factors.py` H4 — stdev of 60 daily percent changes of adjusted
  closes × √252, and the snapshot session's bar must exist.
- **Test:** cluster-robust t by entry session and the D005 restricted wild cluster bootstrap: 9,999 draws,
  Rademacher weights at ≥ 12 clusters, Webb below, seed per test name (`report.R`). H-VOL is an OLS of
  net return on a high-volatility dummy, with the same bootstrap on the slope.
- **Holm over exactly H-M, H-X and H-VOL (m = 3).** A test that cannot run counts as p = 1. The rule 7
  minimum applies: under 30 events or 10 entry sessions → "insufficient".
- **Every result reports its minimum detectable effect:** (1.645 + 0.842) × clustered se.
- **Every result is also reported without** `timing_unverified` and `late_8k` events.
- **When verdicts are given:**
  - Runs before season end are "interim (monitoring only)", with no verdict.
  - **Season end** = the season's last report date + 10 days, when every timing check is final.
  - The registered verdict is on **Seasons A and B pooled**, at the end of Season B. Season A's
    season-end result is an interim reported to Gate 1.
- **Verdict wording:**
  - "p < 0.05 after Holm (shadow, secondary)"
  - or "no evidence (shadow) — an effect smaller than <MDE> would usually be missed"
  - never "works" and never "no effect"
- **What a result can do:** at Gate 1, a hypothesis may be registered as a confirmatory hypothesis for a
  later season (new version, own clock). Nothing else.

## 6. Pilot

- The pilot is graded by the same code as a **functional test only**. Pilot numbers are never pooled
  into any season result.
- Captures began 2026-10-02, so pilot SH-M events exist only for prints whose snapshot session is on or
  after that date (from AMC Oct 5 / BMO Oct 6), and only once each capture is committed before its
  entry open.

## 7. Operational notes and what is not in v1

- **T2 capacity (2026-10-02, not a rule change).** The `t2` job's `max-parallel` rose from 5 to 10, and
  an API-key fallback runs on a usage-limit refusal (HTTP 429). D004 v3 Change 3's text says "up to 5 in
  parallel". That is a description of capacity, not a rule; the hash order and MISSING(capacity) rule
  are unchanged. A fallback decision is marked `_apikey` in its run-log name.
- **Not in v1:**
  - a second price source for shadows (Alpha Vantage's 25 calls a day cannot cover ~1,300 events)
  - options P&L at exit A (it needs an option quote at the reaction-day open, which is not captured)
  - a **year-round** SH-M (off-season sessions: ~60% of weekdays carry at least one print ≥ $2B; worth
    about +25% information a year) — a candidate for v2
  - a T2 ensemble shadow (CHARTER I2) — deferred: the subscription's weekly limit was exhausted on
    2026-10-02, so extra AI runs would take capacity from T2 itself
