"""
Convenience runner for the three PRE self-test suites.
================================================================
The suites now live in tests/ and import the engine (pre_engine, pre_calcrisk,
pre_ledger) from the PRE root by bare module name. This wrapper puts the PRE root
on PYTHONPATH so the suites resolve those imports no matter where they sit or what
the current directory is.

    python run_tests.py

Exit 0 = all assertions pass across the four suites. Non-zero = a suite failed.
This file only orchestrates existing tests; it contains no decision logic.
"""
from __future__ import annotations
import os
import sys
import re
import subprocess
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
SUITES = [
    "tests/pre_selftest.py",       # 47 — engine (§11 AEHR walkthrough, C4, skew, C13 feed integrity)
    "tests/calcrisk_selftest.py",  # 59 — calc-risk (each pinned to a named post-mortem failure)
    "tests/ledger_selftest.py",    # 12 — ledger round-trip (temp file; real ledger untouched)
    "tests/edgescore_selftest.py", # 60 — edge-score, the PRODUCTION scorer (v1.5.0)
    "tests/guidance_selftest.py",  # 76 — GG construction, provenance/contamination, polarity, EDGAR
    "tests/vel_selftest.py",       # 36 — VEL: acceleration bucketing, retro + staleness guards
    "tests/forecast_selftest.py",  # 42 — FORECAST: never abstains; separation from the trade layer
    "tests/batch_selftest.py",     # 26 — batch runner: the CLOCK GUARD + the GG handoff
    "tests/errors_selftest.py",    # 49 — ERROR LEDGER: independence rule, surprise gate, ship guard
    "tests/dossier_selftest.py",   # 22 — DOSSIER: the 5-event cap and what survives a purge
    # THE STANDING RULE, EXECUTABLE. Every control ships with a test that it FIRES on
    # real data, not a test that it exists. Three defects on 2026-08-09 were one process
    # defect three times — build the control, forget to wire it. This suite is the price
    # of adding a control, and it is one assertion.
    "tests/controls_fire_selftest.py",  # 34 — DO THE CONTROLS ACTUALLY FIRE?
]


def main() -> int:
    """QUIET BY DEFAULT (2026-08-12). `--verbose` restores the per-assertion dump.

    THE REASON IS TOKENS, AND IT WAS MEASURED. The suites print one line per
    assertion - 485 of them - and this runner is the FIRST command of every /pre
    session, so all of it landed in the context window. token_audit.py measured
    that at **14,060 tokens per run**: the single largest avoidable line item in
    the workflow, and larger than the operational content of METHOD.md.

    Nothing is lost. A PASS is a boolean - "47 passed, 0 failed" carries exactly
    what 47 PASS lines carry, at 0.3% of the cost. A FAILING suite still prints
    IN FULL, because that is the moment detail changes a decision. That is the
    whole principle: pay for output that changes a decision, never for output
    that confirms one.
    """
    verbose = ("--verbose" in sys.argv) or ("-v" in sys.argv)
    env = dict(os.environ, PYTHONPATH=str(ROOT))
    rc, total, failed = 0, 0, []
    for suite in SUITES:
        if verbose:
            print(chr(10) + "===== " + suite + " =====")
            result = subprocess.run([sys.executable, str(ROOT / suite)], env=env)
            out = ""
        else:
            result = subprocess.run([sys.executable, str(ROOT / suite)], env=env,
                                    capture_output=True, text=True, errors="replace")
            out = (result.stdout or "") + (result.stderr or "")
        rc |= result.returncode
        m = re.search(r"=== (\d+) passed, (\d+) failed ===", out)
        if m:
            total += int(m.group(1))
        if result.returncode != 0:
            failed.append(suite)
            if not verbose:                 # a failure buys its own verbosity
                print(chr(10) + "===== " + suite + " - FAILED, full output =====")
                print(out)
    if rc == 0:
        print("ALL SUITES PASSED  (%s%d suites)"
              % (("%d assertions, " % total) if total else "", len(SUITES)))
    else:
        print("A SUITE FAILED: " + ", ".join(failed))
    return rc


if __name__ == "__main__":
    sys.exit(main())
