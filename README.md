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

## Folders — created as the work reaches them

| folder | holds |
|---|---|
| `registry/` | pre-registered hypotheses and frozen rule versions — hashed, never edited |
| `universe/` | each season's screened universe, frozen on its screening date |
| `events/` | one folder per earnings event: snapshot, thesis card, decisions, outcome |
| `ledger/` | append-only decisions and outcomes |
| `analysis/` | exploratory and confirmatory analysis, kept strictly apart |
| `src/` | pipeline code |
| `reviews/` | external evaluator briefs and responses |
| `archive/PRE_v1_closed/` | the retired previous model — **a record, not a starting point** |

## Open THIS folder as the session

Start experiment sessions **in this folder**, not in the DRIVE repo. A session opened here loads only
this project's rules. A session opened in DRIVE loads the portfolio's rules every turn — the wrong
context for an experiment that must stay blind to the portfolio.
