# Incident 2026-10-21: every cloud routine stopped at its first git step (stale local `main`); WDC and MXL T2 saved

Written Wed 2026-10-21 ~21:25 ET, after the manual T2 run and before reading the next scheduled fires.
Follows `2026-10-20_cloud_T2_shallow_clone.md` (same family: the cloud clone is not the repo we think it is).

## What happened (process only; no outcome or P&L read)
1. **17:21 ET `earnings-t2-cloud` and 17:50 ET `earnings-t2-models` decided nothing.** Step 1
   (`git checkout -q main && git pull -q --ff-only origin main`) failed: "Diverging branches can't be fast-forwarded".
   The run logs (RemoteTrigger `get_run_log`) show the sandbox's local `main` at `73e75f6` (10-20 14:41 ET), a day old,
   in a shallow clone: the pull cannot find a merge base, so it refuses. The 06:20 ET runs, with 56 commits since
   `73e75f6`, passed; by 17:21 ET today's window had added ~50 more. **Reproduced** in a depth-60 clone with `main`
   reset to `73e75f6`: the same error, exit 128.
2. **WDC and MXL (PASS, entry 10-22 open, T2 deadline 09:15 ET) had only T2G.** Health went "T2 AT RISK" from
   18:24 ET, inside a report already RED since 04:49 ET (ABT / SPCX T2 MISSING, DPZ shares), so nothing stood out.
3. The 21:20 / 01:20 / 06:20 ET fires would have failed the same way, and housekeeping (08:30 ET) too.

## Fix (Jacob approved in chat, 20:48 ET: "Yes, fix and run")
- Step 1 of `earnings-t2-cloud`, `earnings-t2-models` and `earnings-housekeeping-cloud` is now
  `git fetch -q origin main && git checkout -q -B main FETCH_HEAD`: it needs no shared history with a stale `main`.
  Nothing else in the prompts changed. Tested on the same simulation: `main` lands on the fetched tip.
- Fired once by hand: **T2 for WDC (NO_BUY 0.47, `f4591d3`) and MXL (BUY 0.52, `5f4224f`) frozen 20:50–20:51 ET**,
  check.py PASS, RFC 3161 tokens; then T2R / T2O for both (`cf32aca`, `d4e16d5`, `982f259`, `49836b7`).
- **Counterfactual:** without it, WDC and MXL go T2 MISSING (the 3rd and 4th this week) and their T2R / T2O too.

## Expectations (written before reading the next fires)
- 21:20 ET `earnings-t2-cloud`: step 1 passes, "claude: 0 event(s) waiting". 21:50 ET `earnings-t2-models`: the same.
- Thu 08:30 ET housekeeping passes step 1 and commits its re-checks.
- Thu 10-22 has no snapshot. Fri 10-23's 8 gates (AGYS, AMKR, CDNS, CLS, CVLT, EEFT, GLXY, RMBS) get T2 for their
  PASS names from the Fri 17:20 ET cloud run, with no hand-firing.

## Lessons
- A routine that never reaches the code leaves no log: only the outcome checks (T2 AT RISK, dates stale) see it.
- **A standing RED hides a new one.** Owed: health should mark RED lines that are new since the previous run.
- `git pull --ff-only` in a sandbox is only as good as the local branch it starts from. Build from the fetched tip.
