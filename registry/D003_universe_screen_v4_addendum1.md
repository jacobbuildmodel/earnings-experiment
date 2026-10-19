# D003 v4 — addendum 1 (2026-10-19 ET): how the gate reads Yahoo's after-close placeholder

A **clarification** of how the code reads one second-source value, fixed before any gate it can affect.

**The rule, unchanged** (D003 v1 §6, carried word for word into v2–v4). The second source is a yfinance
`get_earnings_dates()` timestamp, "time < 09:30 ET → BMO · ≥ 16:00 ET → AMC", or a Nasdaq calendar row with
`pre-market` / `after-hours`. "If they disagree, or the company source is missing, the event is INELIGIBLE,
reason `unconfirmed`."

The rule is silent on a stamp inside market hours. The code (`pipeline/s2_gate.py`) labels one `INTRADAY` and treats
it as a disagreement. That stays, except for the one signature below.

**The data-source fact (found 2026-10-19, checked live).**
- yfinance writes an **upcoming** earnings date with the UTC offset in force when the record was made. An
  after-close placeholder made in daylight time is 20:00 UTC, which reads **15:00 EST** for a date after the
  2026-11-01 clock change.
  - AMD, NET and EW: the upcoming Nov 3–5 stamps are 20:00 UTC.
  - Every past November and February print is 21:00 UTC (16:00 EST), e.g. AMD 2025-11-04.
- Upcoming BMO stamps are 08:00 defaults (ABT, BSX), unlike their 06:00–07:00 history. So **upcoming yfinance rows
  are placeholders**, and for an AMC date after Nov 1 the independent second source is in effect Nasdaq alone.
- All 235 INTRADAY stamps on record in `universe/seasonA/event_status.json` rechecks are exactly 15:00:00-05:00 on
  dates from Nov 2.
- **Effect before this change:**
  - 48 Season A names with a company AMC statement and an agreeing Nasdaq `time-after-hours` row could not be
    confirmed.
  - From Fri 2026-10-30 (the snapshot for AMC Mon Nov 2), the gate would have marked every such AMC event
    INELIGIBLE "second source disagrees". That is most of the Season A peak.

**The change** (`s2_gate.py`, `find_dates.py`; review 2026-10-19 SHIP WITH FIXES, all applied):
- `amc_placeholder(ts)`: a stamp at 15:00–15:59 on a standard-time (UTC−05:00) date. Only that signature changes.
  - Its session is `None`, with `artifact: "amc_placeholder"` and a note in the record.
  - **It never agrees.** It still **disagrees with a company BMO**, as before.
- Any other mid-session stamp is still `INTRADAY` and still disagrees.
- One shared `votes(seconds, session)` now decides agree/disagree for both the gate and
  `find_dates.second_source_agrees`. Before, the two held duplicate copies.
- The requirement of one agreeing second source and none disagreeing is unchanged.

**What it cannot let through.**
- A truly intraday report cannot be confirmed: the company source must state BMO or AMC, or give a release or call
  time outside the session (§6).
- A real midday yfinance stamp still vetoes.
- A company BMO against the placeholder still fails.

**No recorded outcome changes.**
- The 9 gates run so far hold only 16:00-04:00 AMC and 08:00-04:00 BMO stamps. The 125 `confirm.json` files hold no
  INTRADAY or null yfinance session.
- **Disclosed status effect (intended):** ~50 PENDING names carrying this placeholder become confirmable. The next
  `find_dates` run may confirm them. That changes their PENDING status, not any outcome.
- The first gate this can affect is 2026-10-30. It is committed and pushed before then.

**Enforced:** `s2_gate.py` is now listed in `registry/D003_implementation_v4.sha256` (append-only). `check.py` FAILS
on any unregistered edit. Tests: `tests/test_second_source_dst.py` (4 cases, incl. the BMO veto and the gate's use of
the shared votes).

`c66fcc926459c828a02393ac078d72b514f8b072900111bac70b80150053aaf7  pipeline/s2_gate.py`
