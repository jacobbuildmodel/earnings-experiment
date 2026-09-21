# Earnings Experiment

A buy-side experiment: **before each earnings print, decide BUY or NO_BUY — and learn which factors
actually separate the winners, separately for each kind of business.**

Started 2026-09-13 · collection opens 2026-09-21.

## Start here

| file | what it is |
|---|---|
| `STATE.md` | where we left off, and the next action |
| `FRAMEWORK.md` | the full design — outputs first, then inputs, then the rules |
| `CLAUDE.md` | the operating rules the AI follows every session |
| `check.py` | the health check — run first every session; PASS, or stop |

## Folders

| folder | holds |
|---|---|
| `registry/` | frozen rules D001–D005 — hashed in `FROZEN.sha256`, never edited, only versioned |
| `universe/` | each season's screened universe, event statuses, mid-season additions |
| `events/` | one folder per event: confirmation, gate, option chain, factor snapshot, decision, thesis, manifest, timestamp tokens |
| `outcomes/` | graded prices (fetch-once), outcomes and reports — never on disk for the AI step |
| `pipeline/` | the code: `due.py` (unattended driver) · `s1_screen.py` · `s2_gate.py` · `factors.py` · `freeze.py` · `grade.py` · `report.py` · `runlog.py` |
| `logs/actions/` | every tool call the AI step made, per GitHub Actions run |
| `ops/` | runner setup and the AI step's instructions (`actions_prompt.md`) |
| `analysis/` | exploratory analysis, kept apart from anything confirmatory |
| `reviews/` | literature review, errata, the external evaluator brief, drafts of next rule versions |
| `archive/PRE_v1_closed/` | the retired previous model — **a record, not a starting point** |

## Open THIS folder as the session

Start experiment sessions **in this folder**, not in the DRIVE repo, and open with **`pre earnings model`**.
A session opened here loads only this project's rules. A session opened in DRIVE loads the portfolio's
rules and memory every turn — the wrong context for an experiment that must stay blind to the portfolio.

Backup: every commit is pushed to `C:\repos\earnings-experiment.git`, off OneDrive.
