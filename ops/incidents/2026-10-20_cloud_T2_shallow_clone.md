# Incident 2026-10-20: the cloud T2 decided nothing (shallow clone), and stale trigger-branch YAML spent 2 of 3 attempts

Written 2026-10-20 ~20:55 ET, before the outcome: LRCX, META and TXN (all PASS on the Tue 10-20 gates, T2 deadline
Wed 10-21 09:15 ET) have no T2 yet.

## What happened (counts and process only)
1. **Two of the three T2 attempts were spent on the refused token.** Each push of `earnings-s2-trigger` (14:47 and
   15:49 ET) ran `t2-queue.yml` **from the `claude/s2-trigger` branch**, and that branch still holds the old file
   ("claude from 11:00 UTC"). Fix `3c36975` is on main but never reached the branch:
   - on 10-20 15:46 UTC the routine's retry path (`git merge origin/claude/s2-trigger`, no `-X theirs`) merged the
     branch's old tree back over main's;
   - since then each `-X theirs` merge of main keeps the branch-side files. The branch differs from main in 37 files,
     including `s2_gate.py`, `find_dates.py` and lines of `FROZEN.sha256`.
   - Each run logged `probe_failed` ("organization has disabled Claude subscription access"). `attempts()` counts it.
     So **LRCX, META and TXN each have 1 attempt left.**
2. **The cloud T2 routine stopped at check.py.** The 17:20 ET run reported "FAIL - 1 problem(s)" and decided
   nothing. Cause, reproduced on a 1-commit clone:
   - the cloud routines start from a shallow (1-commit) clone, so every file looks first committed at HEAD;
   - check.py's freeze-time check then reads ABT's and SPCX's `manifest_t2g.json` as "committed at/after the entry
     open". Their entry opens (10-20 09:30 ET) fell between the 06:20 ET run, which passed, and the 17:20 ET run.
   - From then on it fails on **every** cloud run: T2, the D013 shadows and housekeeping.
3. **The laptop fallback is down as well:** the laptop's Claude CLI says "OAuth session expired and could not be
   refreshed".
4. **The housekeeping routine's first run (08:38 ET) was refused:** "You've hit your session limit" (the shared
   5-hour allowance).

## Fixes
- **check.py** (no hash list holds it): on a shallow clone it runs `git fetch --unshallow` before the history checks,
  and FAILs if it cannot. Tested on a fresh 1-commit clone: 803 commits fetched, PASS with 0 warnings. No check
  removed or weakened.
- **The trigger branch:** reset its tree to main's with a `[skip ci]` commit, so the next routine merge is clean.
- **Owed (needs Jacob):**
  - The `earnings-s2-trigger` prompt should build each trigger from main (`checkout -B claude/s2-trigger
    origin/main`, empty commit, force push), so stale files can never come back.
  - Re-login of the laptop CLI, so the laptop fallback works again.

## Expectations (committed before the 21:20 ET run)
- **The 21:20 ET cloud run passes check.py and freezes T2 for LRCX, META and TXN** with their last attempt, well
  before 09:15 ET.
- If it fails again, the 01:20 and 06:20 ET runs have no attempt left for any event whose last attempt failed. Those
  events go T2 MISSING, and this incident is updated with the reason.
- **Counterfactual:** without the stale branch, each event would have had 3 cloud attempts. Without the shallow-clone
  failure, the 17:20 ET run would have decided all three.
