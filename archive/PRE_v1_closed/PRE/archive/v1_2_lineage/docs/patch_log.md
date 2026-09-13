# pre_engine.py — autopatch ledger

Per the Self-Correcting Engine Protocol §4A.

**Boundary (refined 2026-06-30, OUTCOME-EQUIVALENCE):** a change is PLUMBING
(autonomous) ONLY if re-running the full historical log reproduces byte-identical
component values AND verdicts. If it moves ANY logged value or verdict — even a
"bug fix" — it is LOGIC and needs n-evidence + 2 holdouts + Jacob sign-off.
Plumbing autopatches are logged here and never alter/re-hash existing frozen
records (new schema is forward-only).

## Reclassification note — 2026-06-30
Under the new outcome-equivalence test, the v1.2.1 fixes #B1 and #B2 below are
**LOGIC, not plumbing** — they change verdicts (e.g. DS=+3 with an UNAVAILABLE
input now → INCOMPLETE; <4-quarter ESTIMATED now → NO TRADE). They are retained
because Jacob explicitly approved "fix the red findings" on 2026-06-26 and the
log was EMPTY at the time (no frozen record broken). Any future change of this
kind must go through the full holdout + sign-off process. #C3 (a monitor/report
computation) and the T+1 loop + anomaly records (forward-only schema) remain
within the autonomous boundary.

## v1.2.1 — 2026-06-26
Source: repo-wide loophole & grey-area audit (initialization task).

Red findings fixed (operational, spec-fidelity — no model logic changed):
- **#B1 fail-closed hole.** `decide()` now runs a worst-case flip test over
  UNAVAILABLE judgment inputs (GG/VEL/REACT/FLAG ranges). A verdict an
  unavailable input could erase (e.g. DS=+3 with FLAG UNAVAILABLE → worst case
  +1) returns INCOMPLETE instead of trading. Replaces the crude |DS|<3 check.
- **#B2 G2 ESTIMATED enforcement.** `run()` now fails closed to NO TRADE when
  <4 confirmed quarters makes the reaction inputs ESTIMATED — they are the
  deciding margin for G2, and the spec forbids an ESTIMATED deciding margin.
  Previously only a warning string.
- **#C3 ablation kill switch restored.** `monitor_accuracy()` again computes
  the n≥20 per-component standalone-hit ablation switch (joins postmortems to
  preregs), alongside the PAUSE and Type-B switches.

New capability (T+1 learning loop + anomaly gate):
- `write_postmortem(classification=...)` — NORMAL | ANOMALY.
- `attribute_failure()` — deterministic wrong-component attribution.
- `evaluate_outcome()` — joins frozen prereg (integrity-verified), labels
  CORRECT/WRONG, attributes failures, appends a `deduction` record.
- ANOMALY outcomes are ISOLATED everywhere (monitor + --review): logged but
  frozen out of accuracy / Type-B / ablation so exogenous shocks (CEO exit,
  litigation/raid, geopolitical) cannot distort the sustainable core.

Still open (NOT auto-applied — flagged for review):
- Look-ahead guard: validate component source timestamps ≤ T−1 close.
- Caps are warnings only; `run()` does not block over-cap trades (needs
  external portfolio state).
- SAT(a) REV-gate rests on n=2 (ACN, MU) — carry a forward holdout watch.

## v1.2.2 — 2026-06-30  (PLUMBING — outcome-equivalent)
Added the `inflection_override` flag to `score_sat` / `run` (default **OFF**).
This is candidate WATCH rule [W1] (see docs/watch_register.md), code-complete
but dormant.
- **Equivalence:** with the flag OFF (the default, and the only value any
  existing caller passes), `score_sat` returns byte-identical (a, b, score)
  for every input — re-running the full log reproduces identical values and
  verdicts. Verified on AVAV/NKE canonical (SAT 0/0) and the REV-gate
  regression (REV+2→0, REV−1→−1). No frozen record altered or re-hashed.
- Flipping the default to ON is a LOGIC change → requires W1's 2nd holdout +
  Jacob sign-off. Until then this is dormant plumbing.
