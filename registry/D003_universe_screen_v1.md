# D003 · Universe screening rule · v1 — FROZEN 2026-09-16 (ET)

> Turns D002's allowlist into a rule that code can run. Written **before any calendar for the pilot or
> Season A was pulled**. Disclosed contamination: the 2026-09-13 pilot preview (in `FRAMEWORK.md` and
> `STATE.md`) had already named MU, JBL, AEHR, PENG, APLD and BB. No threshold below was chosen by
> checking whether it keeps or drops a named stock. Machine-readable twin: `D003_universe_screen_v1.json`.
> This file wins on any disagreement.

## 1. Two stages

| stage | when | decides | output |
|---|---|---|---|
| **S1 · season screen** | once, on the season's screening date | which **companies** are candidates this season | `universe/<season>/candidates.json`, frozen and committed |
| **S2 · event gate** | per event, in the session before entry | whether **this print** is eligible (options priced and liquid; date and session confirmed) | a gate record inside the event's frozen snapshot |

Only events that pass S2 are decided (T0/T1/T2) and graded. An event that fails S2 keeps a row with the
reason, and it is never graded. S2 is measured before entry, so it uses no information from the print.

## 2. Seasons and screening dates

| season | prints in window (report date D, ET) | screening date (ET) | capture |
|---|---|---|---|
| `pilot` | 2026-09-21 → 2026-10-09 | **2026-09-17** | calendars and market caps captured between 00:00 and 09:30 ET on 2026-09-17, which is the Sep 16 close |
| `seasonA` | 2026-10-12 → 2026-11-20 | **2026-10-09** | between the close of 2026-10-08 and 09:30 ET on 2026-10-09 |

Later seasons get their own dates in a new registry entry, before their calendar is pulled. A capture
outside its slot → the season screen is re-run in the next valid slot, and the miss is logged.

## 3. S1 — the season screen

**Candidate calendar** = the union of two sources, both pulled in the capture slot:
- **Nasdaq** `api.nasdaq.com/api/calendar/earnings?date=` for every weekday from window start − 3 to
  window end + 3 calendar days
- **Alpha Vantage** `EARNINGS_CALENDAR` (horizon 3month), rows whose report date falls in the same range

A company is a **candidate** when every test holds:

1. **Listing.**
   - yfinance `quoteType` is `EQUITY`, on NYSE, Nasdaq or NYSE American.
   - Excluded: ETFs, funds, SPACs (industry `Shell Companies`), preferreds, units, warrants.
   - Excluded tickers: any containing `^`, and any ending in a preferred, unit, warrant or right suffix
     (a `-P…` preferred suffix, `.U`, `.W`, `-WT`, `.R`, `-RT`). Class shares such as `BRK-B` stay in
     when yfinance `quoteType` is `EQUITY`.
2. **US domestic filer.** SEC EDGAR lists the company, and its most recent periodic report is a 10-Q or
   10-K. **A company filing 20-F, 40-F or 6-K is excluded:**
   - its prints do not arrive in the 8-K / 10-Q form that D001's VOID checks read
   - "US-listed common stock" (D002) excludes ADRs
3. **Size.** yfinance `marketCap` ≥ **$2,000,000,000** at capture.
   - Between $1.9B and $2.1B, it must also be ≥ $2B on a second source (the Nasdaq calendar row's
     `marketCap`, or Alpha Vantage `COMPANY_OVERVIEW`).
   - Missing on both sources → excluded, reason `no_cap`.
4. **Listed history.** At least one earnings report as a listed company before the screening date.
   **Test:** EDGAR shows at least one 10-Q or 10-K filed before the screening date. Otherwise excluded,
   reason `no_prior_print`: the factors need history.
5. **Industry**, from yfinance `industry`, matched exactly against the table in §4. An industry not in
   the table is OUT.

## 4. The industry map — Yahoo Finance taxonomy, fetched 2026-09-16 (145 industries)

**Unconditional IN**

| cluster | Yahoo industry | extra test |
|---|---|---|
| Semiconductors & equipment | Semiconductors · Semiconductor Equipment & Materials | — |
| Software & internet | Software - Application · Software - Infrastructure · Internet Content & Information | — |
| Tech hardware & networking | Computer Hardware · Communication Equipment · Electronic Components | — |
| Drones, robotics, space & defense-tech | Aerospace & Defense | — |
| Consumer | Internet Retail · Specialty Retail · Apparel Retail · Apparel Manufacturing · Footwear & Accessories · Restaurants | — (S2's implied move is the only further gate) |
| Healthcare growth | Biotechnology · Medical Devices | **market cap ≥ $10,000,000,000** ("largest names only") |

**Conditional IN** — each passes only its filing test (§5)

| cluster | Yahoo industry | test |
|---|---|---|
| AI infrastructure & compute | Information Technology Services | **AI-HOSTING** |
| AI infrastructure & compute | Capital Markets | **BITCOIN-MINER** and **AI-HOSTING** |
| Drones, robotics, space & defense-tech | Specialty Industrial Machinery | **ROBOTICS** |
| Crypto-proxy | any industry | ticker is **MSTR** (named individually in D002) |

**How D002's wording maps onto the taxonomy.** Recorded so nobody re-reads it later:
- "security" software is classified by Yahoo under Software - Infrastructure or Application.
  `Security & Protection Services` is physical security, so it is **OUT**.
- "electronics manufacturing": Yahoo has no separate industry. EMS firms sit in Electronic Components.
- **OUT because D002 does not list them:**
  - technology: Consumer Electronics · Scientific & Technical Instruments · Electronics & Computer
    Distribution · Solar
  - consumer: Home Improvement Retail · Luxury Goods · Department Stores
  - healthcare: Medical Instruments & Supplies · Diagnostics & Research · Health Information Services
  - communication services: Electronic Gaming & Multimedia
- **All REIT industries are OUT**, including data-center REITs, as D002's "Out" line says.
- A consequence to be aware of: large consumer-electronics names are outside the universe. Changing
  that is a D002 v2 decision for a later season.

## 5. Filing tests — computed by code, counts stored

**Filings used:** the company's most recent 10-K and most recent 10-Q, each filed on or before the
screening date and within 400 days of it (primary document only, from SEC EDGAR, with a User-Agent).

**How the count works:**
- The HTML is converted to text, lower-cased, with whitespace collapsed.
- A count is the number of non-overlapping, case-insensitive matches of the listed phrases, summed
  across both filings.
- Every match is stored with 80 characters of context either side, so a reviewer can see what was
  counted. **The reviewer cannot overrule the count in v1.**

| test | phrases | passes when |
|---|---|---|
| **AI-HOSTING** | `high-performance computing` · `high performance computing` · `hpc` (whole word) · `gpu` (whole word, incl. `gpus`) · `ai cloud` · `ai data center` · `colocation` | **≥ 10** total matches |
| **BITCOIN-MINER** | `bitcoin mining` · `mining pool` · `hashrate` · `hash rate` | **≥ 5** total matches |
| **ROBOTICS** | `robot` (prefix: robot, robots, robotic, robotics) · `autonomous` · `unmanned` · `drone` (prefix) | **≥ 10** total matches |

No filing found → the test fails, reason `no_filing`.

## 6. S2 — the event gate (per print)

**When:** during the regular session **before the entry session**, between **14:30 and 15:50 ET**.
- BMO on D: the snapshot session is D−2.
- AMC on D: it is D−1.

It must be committed before the entry open (D001 VOID rule).

**Date and session confirmation — two sources, one of them the company:**

| source | what counts |
|---|---|
| **company** (required) | a company press release, IR events page, or SEC filing stating the report date **and** either the session ("before the market opens" / "after the market closes") or a release time. With only a conference-call time: a call before 09:30 ET → BMO, a call at or after 16:00 ET → AMC, flag `session_from_call_time`. A call during the session → `unconfirmed`. |
| **second** | yfinance `get_earnings_dates()` timestamp (time < 09:30 ET → BMO · ≥ 16:00 ET → AMC), or a Nasdaq calendar row with `pre-market` / `after-hours` |

- If they disagree, or the company source is missing, the event is **INELIGIBLE**, reason `unconfirmed`.
- The date must fall inside the season window.

**Implied move and liquidity — from the yfinance option chain at snapshot time:**

```
spot         = yfinance fast_info last_price at snapshot
expiry       = the first listed expiry on or after the reaction day (D001)
strike       = the listed strike nearest spot (a tie takes the lower strike);
               the same strike is used for the call and the put
mid(leg)     = (bid + ask) / 2
implied_move = (mid(call) + mid(put)) / spot
```

| check | passes when | otherwise |
|---|---|---|
| implied move | `implied_move ≥ 0.04` | INELIGIBLE `low_implied_move` |
| quotes | both legs have bid > 0 and ask > bid | one re-fetch after 5 minutes; still failing → INELIGIBLE `no_quote` |
| spread | `(ask − bid) / mid ≤ 0.10` for **each** leg | INELIGIBLE `wide_spread` |
| open interest | `OI(call) + OI(put) ≥ 500` at that strike | INELIGIBLE `thin_oi` |
| expiry distance | expiry is > 5 sessions after the reaction day | eligible, but flagged `diluted_implied_move`, because the straddle then prices non-event days too |

The full chain for that expiry is stored in the snapshot whether the event passes or not. This is the
literature review's standing action: capture options before every entry.

## 7. Mid-season additions

Each Friday of a season, both calendars are re-pulled. A company that was **not** in the S1 candidate
calendar, and now shows a print inside the window, is run through S1 with its market cap at that
moment. If it passes, it joins with the flag `added_midseason`. Nothing else may add a company.
A company that fails S1 is never re-tested within the same season.

## 8. WIN_excess benchmark — secondary outcome (D001 §4)

| Yahoo industry | ETF |
|---|---|
| Semiconductors · Semiconductor Equipment & Materials | SOXX |
| Software - Application · Software - Infrastructure | IGV |
| Internet Content & Information | XLC |
| Computer Hardware · Communication Equipment · Electronic Components · Information Technology Services · Capital Markets (AI-infra) | XLK |
| Aerospace & Defense | ITA |
| Specialty Industrial Machinery | XLI |
| Internet Retail · Apparel Manufacturing · Footwear & Accessories · Restaurants | XLY |
| Specialty Retail · Apparel Retail | XRT |
| Biotechnology | XBI |
| Medical Devices | IHI |
| MSTR | IBIT |

- **beta:** OLS slope of the stock's daily adjusted close-to-close returns on the ETF's, over the
  **252 sessions** ending with the snapshot session.
  - Fewer than 126 sessions → beta = 1, flag `beta_default`.
  - beta is clipped to [0, 3], flag `beta_clipped`.
- **bench_return:** the ETF's return over the **same open/close points** as the stock's exit (D001 §1),
  from the same price sources.
- **leave-one-out:** if the stock's weight `w` in the ETF, from the issuer's holdings file saved at
  snapshot, is **≥ 2%**, then `bench = (ETF_return − w × stock_return) / (1 − w)`.
  No holdings file → unadjusted, flag `bench_weight_missing`.

## 9. What v1 does not do

- No liquidity floor on the stock itself beyond the ≥ $2B cap. The option-liquidity gate in S2 covers
  tradability for this universe.
- No sentiment or attention filter. Those are factors, not eligibility, and belong to T1/T2 (rule 8).
