# registry/ — frozen decisions

Everything here is **frozen**. A frozen file is never edited. A change is a new file with a higher
version (`D001_outcome_v2`) and its own clock, and the old version keeps being scored untouched (rule 5).

`FROZEN.sha256` holds the hash of every frozen file. `check.py` re-hashes them at the start of every
session and **FAILS** if any has changed. To freeze a new file, add its line to `FROZEN.sha256` in the
same commit that adds the file. Lines are only ever appended.

| id | what | frozen | status |
|---|---|---|---|
| D001 | trade mechanics and outcome v1: exit A, official open, WIN = raw direction, T0 is the bar | 2026-09-16 | LIVE |
| D002 | universe industry allowlist v1 (the FRAMEWORK §10 draft, verbatim) | 2026-09-16 | LIVE; five terms still need numbers → D003 |
