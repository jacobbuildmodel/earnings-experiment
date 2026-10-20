# Incident 2026-10-19 — ABT 2026-10-21 and SPCX 2026-10-20: T2 MISSING on Season A's first two PASS events

Written 2026-10-20 ~07:40 ET. That is after the T2 deadline became unreachable, but **before ABT's outcome exists**
(BMO Oct 21; exit A = the Oct 21 open). Nothing here reads or predicts a graded result.

## What happened
- **14:31 ET Mon:** ABT passed the S2 gate, the first Season A PASS. Stage 1 froze with T0 BUY and T1 BUY (`97dd737`,
  `manifest.json` 14:31:19 ET, entry 2026-10-20 09:30).
- **14:37, 14:38, 16:31 ET:** `t2-queue.yml` ran the claude backend in Actions. All three attempts were refused:
  "Your organization has disabled Claude subscription access for Claude Code". The token was refused on every
  Actions run since 2026-10-15. The new token Jacob saved on 10-19 is refused the same way (housekeeping runlog
  2026-10-20 02:10 UTC).
- `t2_stage2.py` counts a `probe_failed` refusal as a failed attempt. At `MAX_ATTEMPTS = 3` it leaves T2 MISSING
  (D004 v4, hashed). So the cloud routine `earnings-t2-cloud`, whose claude calls work, found "0 event(s) waiting"
  at 17:20, 21:20, 01:20 and 06:20 ET.
  - The proof the cloud path works: the D013 shadows that run there decided ABT at 17:52 and 17:53 ET.

**SPCX 2026-10-20 (AMC Oct 20, entry Oct 20 open) is the same case.** Its claude attempts were refused at 14:37, 14:38 and
16:31 ET; the T2R, T2O and T2G shadows froze. It was confirmed on 10-19 by the fixed `find_dates`, and gated PASS at
14:30 ET that day. Health raised both as T2 AT RISK at 04:50 ET on 10-20; neither can be decided within the protocol.

## What is NOT done, and why
- **T2 stays MISSING.** Retrying would need either an edit to `t2_stage2.py` or a relabelled attempt log.
  - An edit ends the A + B pooling of H-T2C (D005 v3: the protocol is the file's hash).
  - A relabelled log falsifies the record.
- T0 and T1 stand. The shadows stand as recorded: T2R (the same model and prompt, a re-run) NO_BUY 0.50, T2O NO_BUY
  0.47, T2G BUY 0.53. **None of them is T2.**

## Expectation, committed before the outcome (descriptive only)
- Had T2 run, the nearest evidence is T2R: the same model, system prompt and dossier, a re-run.
- So T2 would most likely have been NO_BUY near 0.50. That is a coin-flip decision, and its absence costs
  calibration data (one event), not a clear signal.

## Fixes
1. **Done, `t2-queue.yml` (D004 v4 dated line 2026-10-20).** Actions runs the claude backend only if the repository
   variable `T2_ACTIONS_CLAUDE` is `on`. It is unset, so the cloud routine now holds all 3 attempts.
   - The old "last resort from 11:00 UTC" was `hour >= 11`, which also fired minutes after every afternoon gate. It
     is now 11:00–13:59 UTC, the entry morning only.
2. **Jacob:** the refusal is an account setting ("ask your admin to enable access"). Either enable Claude Code
   subscription access in the organization's admin settings, or keep Actions' claude off for good. The cloud routine
   does not need the token.
3. **Next:**
   - a health alarm for an AI-step or T2 refusal (in the plan);
   - for a future D004 version, not now: an auth refusal should be classed like a usage limit, which is retried and
     not counted. That changes `t2_stage2.py`, so it waits for a version that starts its own clock.
