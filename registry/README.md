# registry/ — frozen decisions

Everything here is **frozen**. A frozen file is never edited. A change is a new file with a higher
version (`D001_outcome_v2`) and its own clock, and the old version keeps being scored untouched (rule 5).

`FROZEN.sha256` holds the hash of every frozen file. `check.py` re-hashes them at the start of every
session and **FAILS** if any has changed. To freeze a new file, add its line to `FROZEN.sha256` in the
same commit that adds the file. Lines are only ever appended.

| id | what | frozen | status |
|---|---|---|---|
| D001 | trade mechanics and outcome v1: exit A, official open, WIN = raw direction, T0 is the bar | 2026-09-16 | LIVE |
| D002 | universe industry allowlist v1 (the FRAMEWORK §10 draft, verbatim) | 2026-09-16 | LIVE; its open terms are set by D003 |
| D003 | universe screening rule v1: season screen (S1), per-event gate (S2), Yahoo industry map, filing tests, benchmark map | 2026-09-16 ET | LIVE |
| D004 | decision protocol v1: T0 buy-all, T1 null in the pilot, T2's allowed/forbidden inputs and outputs, business-stage formula | 2026-09-16 ET | LIVE |
| D005 | evaluation protocol v1: clustering by entry session, wild cluster bootstrap test of lift, fixed verdict wording, Holm/BH, partial pooling, grading details, power table; implementation hashes in `D005_implementation_v1.sha256` | 2026-09-21 ET | LIVE |
| D003 v2 | S2 window from the close (early closes), ADP and PAYX named out, Alpha Vantage calendar by code, mid-season cap as of screen date, `printed_before_entry` gate, stale-quote and event-move recording | 2026-09-21 ET | LIVE from seasonA (v1 stays live for pilot) |
| D004 v2 | T2 deadline = snapshot-session close; timed inputs on the snapshot day | 2026-09-21 ET | LIVE from seasonA (v1 stays live for pilot) |
| D005 v2 | success needs hit-rate lift and return lift >= 0; only the full sample gets a verdict; confidence test, within-date, leave-one-date-out, exit-A legs, gate selectivity; grading changes; disclosures; rule v0 requirements | 2026-09-21 ET | LIVE for all seasons; v1 still computed beside it |
| D006 | history study procedure v1: sample, 10 PIT factors with literature signs, backward-looking ranks, TRAIN/VALIDATION, R-LIT vs R-SEL (t > 3, BH q < 0.10), 12 tests; implementation hashes in `D006_implementation_v1.sha256` | 2026-09-29 ET | LIVE - produces T1 rule v0 |
