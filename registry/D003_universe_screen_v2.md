# D003 · Universe screening rule · v2 — FROZEN 2026-09-21 (ET) · applies from Season A

> **v1 stays LIVE for the pilot** and keeps being scored unchanged (rule 5). v2 governs `seasonA`
> onwards. Code picks the governing version per season (`pipeline/common.py` `rule_for`).
>
> Machine-readable twin: `D003_universe_screen_v2.json`. This file wins on any disagreement.
>
> v2 is frozen before the Season A calendar is pulled: its capture slot opens 2026-10-08 16:00 ET.
>
> **Sources of the changes:**
> - defects found internally (the early-close window; PAYX)
> - two external evaluations on 2026-09-21, a Sonnet and an Opus reviewer, each starting cold
>   (`reviews/evaluations/2026-09-21_external.md`)
>
> **Everything not listed below is v1 unchanged, word for word.**

## Change 1 — the S2 window is defined from the close

- v1: 14:30–15:50 ET.
- v2: **close − 90 min → close − 10 min** of the snapshot session.
  - A normal day is unchanged: 14:30–15:50.
  - An NYSE early close (13:00) gives 11:30–12:50.
  - Close times come from `pipeline/sessions.py`, which is sourced from nyse.com.
- *Scope note:* Season A's last snapshot session is 2026-11-19, so the early close on 2026-11-27 does
  not fall in Season A. The rule exists for later seasons.
- The switch from daylight to standard time on 2026-11-01 *is* inside Season A. The workflow has three
  in-window fires in both regimes, plus two at 16:40 and 17:10 UTC for early-close days.

## Change 2 — payroll processors excluded by name

D002 puts "mature tech services (payroll, …)" OUT. Yahoo files PAYX under "Software - Application".

**v2 excludes ADP and PAYX by name** (reason `named_exclude`), citing D002's word "payroll", the same
way D002 names MSTR.

*Why not the SEC-SIC filter first drafted:* run on 2026-09-21 over large software filers, it would also
have removed:
- AKAM — security, which D002 explicitly includes
- FICO and ROP
- AFRM, HOOD and COIN
- FIS, GPN, BR and ACN

SIC codes are also known to be stale and to misassign firms (Kahle & Walkling 1996). IT outsourcing is
already gated: Information Technology Services needs the AI-HOSTING filing test (v1 §4).

## Change 3 — calendar sources

- **S1:** Nasdaq and Alpha Vantage, as in v1. The Alpha Vantage calendar is pulled by code with the
  repository secret (`s1_screen.py <season> av`). If it cannot be pulled inside the capture slot, the
  screen runs on Nasdaq alone and the season is flagged `single_calendar`.
- **Friday mid-season screen (v1 §7):** Nasdaq is required; Alpha Vantage is added when the key is
  present. The run records which sources it used. A name that only Alpha Vantage lists can be missed
  when that source is absent. That is disclosed, not hidden.

## Change 4 — mid-season market cap as of the screening date

v1 §7 used the market cap at the Friday re-pull, so a name could qualify because it had just risen.
That is the "added because it moved" route rule 8 forbids.

**v2:** the size test for a mid-season addition uses
**shares outstanding (yfinance, at the re-pull) × the close of the session before the season's
screening date**, with the same $2B floor and band. The capture records both numbers.

## Change 5 — a print already public before entry is ineligible

**S2 adds a check before the option gate.** If SEC EDGAR shows an **Item 2.02 8-K** accepted in the
**30 days** before the snapshot, the event is **INELIGIBLE `printed_before_entry`**. The results are
already public, so the event cannot be traded blind. Every 2.02 filing found is stored in `gate.json`.

The grader separately voids an event whose 2.02 filing lands before the frozen release window
(D005 v2 §6).

## Change 6 — recorded at every S2 gate (not gates)

- Each option leg's **last trade time** (`lastTradeDate`), so stale quotes can be identified later.
- The **event-specific implied move** from two expiries, `B_event_move_term_structure` in
  `factors.json` (Dubinsky, Johannes, Kaeck & Seeger 2019). The straddle move used by the ≥ 4% gate
  also prices non-event days; this measure does not. D005 v2 states the truncation in terms of both.
- The **report-date shift** against the same quarter last year, `L_report_date_shift_days`: later
  reporting tends to carry bad news (Johnson & So 2018).

## Unchanged, deliberately

- The ≥ 4% straddle threshold stays the gate. Changing an eligibility threshold after a pilot is
  exactly the dial rule 8 forbids. Its selectivity is reported per cluster and stage (D005 v2).
- `diluted_implied_move` stays a flag, not a gate. Cutting on it is a pre-registered robustness cut
  (D005 v2), never chosen after results.
- The leave-one-out benchmark stays at its fallback (`bench_weight_missing`).
