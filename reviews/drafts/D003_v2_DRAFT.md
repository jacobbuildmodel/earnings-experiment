# D003 v2 — DRAFT, not frozen · for the external review, then freeze before 2026-10-08 16:00 ET

> v1 stays live and scored for the pilot (rule 5). v2 applies from the **Season A** screen. It must be
> frozen, committed and hash-listed before the Season A capture slot opens: **2026-10-08 16:00 ET**
> (2026-10-09 04:00 SGT). Everything not listed here is v1 unchanged.

## Change 1 — the S2 window on early-close days (defect found 2026-09-16)

v1 fixes 14:30–15:50 ET. On **2026-11-27** the market closes at 13:00, so the window does not exist.

**v2:** the S2 window is **close − 90 min → close − 10 min** of the snapshot session. On a normal day
that is 14:30–15:50 (unchanged). On an early close it is 11:30–12:50. The close times come from
`pipeline/sessions.py` (from nyse.com).

Needs with it: workflow crons at 16:40 and 17:10 UTC (11:40 / 12:10 EST), so at least two fires land
inside the early-close window.

## Change 2 — payroll and business-services processors in the software industries (PAYX defect)

D002 puts "mature tech services (payroll, IT outsourcing)" OUT. Yahoo labels PAYX "Software -
Application", so v1 let it in.

SEC SIC codes checked on 2026-09-21:

| code | examples |
|---|---|
| 7372 | ORCL, CRM, ADBE, NOW, PLTR, SNOW, CRWD, PAYC, PCTY, BB |
| 7374 | ADP, WDAY, TOST, APLD |
| 7389 | FIS, GPN, BR, ACN |
| 8700 | PAYX |

No code separates payroll from software on its own: ADP shares 7374 with Workday.

**Recommended v2 rule (default):** for companies in `Software - Application` or
`Software - Infrastructure`:
- OUT if the SEC SIC code is outside **3570–3579, 3660–3679 and 7370–7379** (this catches PAYX 8700,
  and FIS, GPN and BR at 7389)
- plus **ADP by name**, citing D002's word "payroll", the same way D002 names MSTR

Alternatives:
- (a) the SIC rule only — ADP stays in
- (b) names only: ADP and PAYX
- (c) no change — PAYX-type names stay in

## Change 3 — calendar sources where Alpha Vantage is unavailable

The S1 capture needs the Alpha Vantage calendar, pulled by hand through a laptop session, and the
Friday mid-season screen (§7) runs in GitHub Actions, where there is no Alpha Vantage key.

**v2:**
- **S1:** Alpha Vantage is required. If it cannot be pulled in the slot, the screen runs on Nasdaq
  alone, flagged `single_calendar`.
- **Mid-season screen:** Nasdaq alone is sufficient, and Alpha Vantage is added when a key is set.
  The run records which sources it used.

## Not changed, noted for the review

- Stocks with only monthly option expiries (PAYX's first expiry was 17 sessions after its print) get
  `diluted_implied_move` and stay eligible. An alternative is to make "expiry > 5 sessions after the
  reaction day" INELIGIBLE. Recommended: keep v1, because it is a flag, and D005 can cut on it.
- The leave-one-out benchmark cannot run: the issuer holdings files are not machine-fetchable.
  Options: capture holdings by hand at each snapshot, drop leave-one-out, or accept the
  `bench_weight_missing` flag. Recommended: accept the flag. WIN_excess is secondary.
