# Earnings Experiment

This repository is the complete working record of a pre-registered forecasting experiment on the
earnings announcements of US-listed companies: before each announcement, a fixed rule and an AI model
each record a prediction of whether the share price will rise across it, and every prediction is hashed
and timestamped before the result exists. It then measures whether either method does better than the
plain baseline of buying before every announcement, and it reports a well-measured "no effect" with the
same care as a positive result.

**Scope.** This is a research record. Every order in `paper/` was placed in a simulated (paper)
brokerage account, and the other results are computed from public prices. `BUY` and `NO_BUY` are the
experiment's prediction labels, not recommendations. The plan allows real money only after a
pre-registered gate, in 2027 at the earliest (`registry/D008_graduation_v1.md`,
`registry/D019_reframe_v1.md`).

## Status on 2026-11-19

- Started 2026-09-13. The pilot covered announcements from 2026-09-23 to 2026-10-07.
- **Season A** runs from 2026-10-12 to 2026-11-20 and is in its last week.
- **Reframed on 2026-11-04** (`registry/D019_reframe_v1.md`), after an independent review
  (`reviews/2026-11-03_stage1_committee/`): the AI-judgment track runs to the end of Season A and then
  stops with no verdict, new simulated options trades are halted, and the experiment continues as a
  code-only measurement of the average return from buying just before an announcement.
- **Next: Gate 1, early December 2026**, a continue-or-terminate decision on criteria fixed in advance
  (`registry/D019_reframe_v1.md` §5).
- No method has been confirmed to beat the baseline. The fixed rule failed validation on historical data
  before it went live and is scored as registered (`registry/README.md`, T1 rule v0).

## Start here

| file | what it is |
|---|---|
| `STATE.md` | where the work stands, and the next action |
| `CHARTER.md` | why it exists, what counts as improving, where the edge is, the improvement backlog |
| `RESEARCH_PLAN.md` | the roadmap: seasons, gates, and what must be true before each next step |
| `FRAMEWORK.md` | the full design: outputs first, then inputs, then the rules |
| `HYPOTHESES.md` | every test the experiment runs, in one place |
| `JOURNAL.md` | the lab notebook: dated observations, newest first |
| `CLAUDE.md` | the operating rules the AI follows every session |
| `check.py` | the health check: run first every session; PASS, or stop |

## Folders

| folder | holds |
|---|---|
| `registry/` | frozen rules D001–D019 and the T1 rule, hashed in `FROZEN.sha256`, never edited, only versioned; `registry/README.md` is the index |
| `universe/` | each season's screened universe, event statuses, mid-season additions |
| `events/` | one folder per event: date confirmation, gate, option chain, factor snapshot, decision, thesis, manifest, timestamp tokens; Season A events also hold the code-built dossier and the AI track's own frozen files |
| `outcomes/` | graded prices (fetch-once), outcomes and reports; never on disk for the AI step |
| `paper/` | ledgers of the simulated (paper) brokerage accounts, and the fill re-checks |
| `shadow/` | exploratory tracks: the daily earnings-calendar capture, the market-wide and off-season tracks |
| `pipeline/` | the code: screening (`s1_screen.py`, `s2_gate.py`), date finding, factors, freezing (`freeze.py`), grading (`grade.py`), reports, paper trading, shadow tracks, the health check; `due.py` is the unattended driver |
| `.github/workflows/` | the scheduled GitHub Actions jobs that run the pipeline |
| `logs/` | `actions/`: every tool call the AI step made, per GitHub Actions run; `t2/`: each AI decision attempt |
| `ops/` | runner setup, the AI step's instructions (`actions_prompt.md`), incident notes, the archived history of `STATE.md` |
| `analysis/` | exploratory analysis, kept apart from anything confirmatory |
| `reviews/` | literature review, errata, the external evaluator brief, the independent Stage 1 review, drafts of next rule versions |
| `tests/` | pytest tests of the pipeline code |
| `archive/PRE_v1_closed/` | the retired previous model: **a record, not a starting point** |

## Checking the record

```
pip install -r requirements.txt
python check.py
```

`check.py` reads only. It re-hashes every frozen rule against `registry/FROZEN.sha256`, confirms the
archive is unchanged, and checks the timestamp tokens (this needs `git` and `openssl` on the path).
Each event's `manifest.json` lists the hashes of that event's files, and the `manifest.tsr_*` files are
RFC 3161 timestamp tokens over that manifest from two independent timestamp authorities.

## For the operator: open THIS folder as the session

Start experiment sessions **in this folder**, not in the DRIVE repo, and open with **`pre earnings model`**.
A session opened here loads only this project's rules. A session opened in DRIVE loads the portfolio's
rules and memory every turn, the wrong context for an experiment that must stay blind to the portfolio.

Backup: every commit is pushed to `C:\repos\earnings-experiment.git`, off OneDrive.
