# Pilot screen, 2026-09-13 — NOT the universe

**This is exploratory evidence, not the frozen universe.** The universe is set once per season, by the
industry allowlist in `FRAMEWORK.md` §10, on a fixed screening date. This screen is kept because it
**proved the first draft of that rule was broken**, and the evidence behind §10 should stay re-checkable.

## What was run

- **Calendar:** `av_earnings_calendar_preview.json` — an Alpha Vantage earnings-calendar *preview*:
  1,064 of 3,548 lines, report dates 2026-09-14 → 2026-10-28, pulled 2026-09-13. Its transient download
  link was removed before saving.
- **Screen:** `classify_calendar.py` — for the 188 reporters dated Sep 14 – Oct 9: yfinance sector,
  industry, market cap and revenue growth; then, for names in five broad sectors with market cap ≥ $2B,
  the at-the-money implied vol of the first option expiry at least 7 days out.
- **Output:** `calendar_classified.json`.

## What it found — re-verified 2026-09-14 from these files

| figure | value |
|---|---|
| reporters Sep 14 – Oct 9 | 188 (4 returned no sector) |
| passed a broad-sector + ≥ $2B screen | **34** — Consumer Cyclical 12 · Technology 10 · Industrials 7 · Healthcare 4 · Communication Services 1 |
| of those, at-the-money implied vol ≥ 50% | **22** (see the warning below) |

**The pass list is the finding.** It admitted two homebuilders (LEN, KBH), an RV maker (THO), a
ski-resort operator (MTN), an auto-parts chain (AZO), a used-car dealer (KMX), a payroll processor
(PAYX — labelled "Software"), a lighting company (AYI), a plasma-drug maker with flat revenue (GRFS,
−0.9%) and Manchester United (MANU). A broad sector label cannot express "AI infrastructure" or
"slow-growth".

It also surfaced the names the experiment is for: **MU** (Sep 30, after close — confirmed by a
timestamped yfinance date), **JBL**, **AEHR**, **PENG**, **APLD** and **BB**.

## ⚠ The implied-vol column is a crude proxy — never reuse it as the §10 rule

- It is **annualised at-the-money implied vol**, not the event's implied move — and §10 uses the move (≥ 4%).
- It used the first expiry at least 7 days out. **For 8 of the 34 names — JBL, MU, ACN, NKE, AEHR, CCL,
  APLD and DAL — that expiry (2026-09-25) ends BEFORE the report**, so their number does not price the
  print at all.
- For the other 25 names that returned a value, the expiry does span the report, so their implied vol
  **includes** the print — both homebuilders among them, at 52–54%.

A real implied move has to come from the option expiry that spans the print (`FRAMEWORK.md` §10).
