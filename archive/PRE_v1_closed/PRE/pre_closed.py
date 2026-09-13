"""
PRE IS A CLOSED EXPERIMENT. This module is the mechanical guard that keeps it closed.
================================================================================
Closed 2026-09-13 on the owner's decision, after four independent external reviews all
reached the same verdict: retire the directional forecast.

WHY IT WAS CLOSED, in the order the arguments actually survived scrutiny.

  1. NO DEMONSTRATED EDGE. 14/27 = 51.9% against a pre-specified 50% null is p = 1.00.
     Separation between UP and DOWN calls was -1.86pp at t = -0.50. Not an inverted
     signal - nothing, in either direction.

  2. THE ARGUMENT THAT ACTUALLY DECIDED IT: the scoring stack was edited FOUR TIMES
     inside its own measurement window (2026-08-09, 08-12, 09-05 x2), each time in
     response to observed misses. `value`/`vrich`/`SAT` were cut mid-sample; on
     2026-09-02 the DEFAULT_ETF change altered the BENCHMARK used to compute idio for
     6 of 7 names in that batch. So 51.9% is the blended in-sample score of a sequence
     of different models, and out-of-sample n for the final stack is FIVE.

  3. AND WAITING COULD NOT FIX IT. The error ledger's job was to detect mechanisms and
     demand changes; every change it extracted reset the out-of-sample clock and
     destroyed the frozen specification a record requires. Simulated against pure
     noise, the 3-confirmation firing rule reached a "RIPE" class ~68% of the time over
     13 misses with author-chosen labels. The governance layer was not merely
     disproportionate to the evidence - it was what prevented evidence from existing.

WHAT WAS *NOT* THE REASON, recorded so it is not repeated as folklore:
  * NOT "always-DOWN beat it by 3.7pp". That benchmark was chosen after seeing the data;
    the two rules make identical predictions on 16 of 27 events and differ on 11, 5 right
    vs 6. McNemar exact p = 1.00. The entire "edge" was one event.
  * NOT "the effective sample is 6 event-dates". That assumed same-night names are
    perfectly redundant. Tested: Tarone/Pearson chi2 = 4.92 on 5 df, dispersion 0.98 - no
    block structure in CORRECTNESS, because the model's own calls vary within a night.
    Cluster bootstrap 33-70% vs naive 33-70%, identical.
  * NOT the Singapore time zone. 21:30 SGT is 9:30pm, and a real 2pp edge on 10pp sigma at
    ~5 prints a week is a per-trade Sharpe near 0.2 - worth staying up for.
  * NOT the "inverted conviction gradient", which was noise on cells of n=2 and n=6 and was
    wrongly reported as a finding for three sessions.

WHAT THE EXPERIMENT PRODUCED, which is why the record is kept rather than deleted:
  a clean, honestly-obtained negative result on 27 pre-registered, integrity-hashed,
  blind directional forecasts. That is worth more than a flattering one.

WHAT SURVIVED AND WHERE IT WENT:
  two forensic rules, into `.claude/skills/earnings/SKILL.md` - the guidance-qualifier
  diff (a raise on a changed basis is not a raise) and the OCF/NI earnings-quality ratio.
  Nothing else was salvaged, deliberately: the blindness protocol and clock guard are
  entangled across ~2,000 lines of scoring code, and refactoring to rescue them is how a
  retirement quietly becomes a rebuild.

THE BINDING RULE
  The ledgers are the record of a finished experiment and are now READ-ONLY. Appending to
  them would silently mix new rows into a closed sample and make the negative result
  uninterpretable - the same defect, one layer up, that closed the model in the first place.

  Reopening is a deliberate act, not a drift: delete the `CLOSED` sentinel file and say so
  in PRE/STATE.md. It is not done by importing a module or by running an old command.

Test paths are unaffected: every guard fires only on the PRODUCTION default path, and the
test suites all write to tempfile directories.
"""
from __future__ import annotations

from pathlib import Path

__version__ = "1.0.0"

SENTINEL = Path(__file__).with_name("CLOSED")


def is_closed() -> bool:
    """True while the CLOSED sentinel is present."""
    return SENTINEL.exists()


def assert_open(path, default) -> None:
    """Refuse a write to the PRODUCTION ledger while PRE is closed.

    `path` is whatever the caller passed; `default` is that module's production default.
    A write anywhere else (a tempfile, an explicit scratch path) is always allowed, so the
    guard cannot break the test suites or an offline re-analysis of the frozen record.
    """
    if not is_closed():
        return
    try:
        same = Path(path).resolve() == Path(default).resolve()
    except OSError:
        same = str(path) == str(default)
    if same:
        raise RuntimeError(
            f"PRE IS CLOSED — refusing to append to {Path(default).name}.\n"
            "This ledger is the record of a finished experiment (closed 2026-09-13); "
            "adding rows would mix new observations into a closed sample.\n"
            "Reasoning: PRE/pre_closed.py. Status: PRE/STATE.md.\n"
            "Post-print work now belongs to /earnings. To genuinely reopen, delete "
            f"{SENTINEL.name} and record that decision in PRE/STATE.md."
        )
