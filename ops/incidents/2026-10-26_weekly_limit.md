# Incident 2026-10-26 — cloud T2 fires refused by the account's weekly limit (nothing lost)

Written Mon 2026-10-26 11:25 ET by the week-plan chat. No outcome, P&L or C1 figure was read.

## What happened
- `earnings-t2-cloud` (`trig_01H4HJJ2uPLZXUwfi7q5fXr3`) fired on schedule all weekend. The Mon 01:20 UTC run's log
  (`cse_015PdGcM7onxDK48qbweTRSn`, read with `get_run_log`) ends after 1 s: `rate_limit: rejected (seven_day)`,
  "You've hit your weekly limit · resets 6am (UTC)". The Sun 21:21 UTC and Mon 05:21 UTC runs lasted 9 s like it,
  against ~60 s for a normal run: inferred refused, logs not read. The Sun 10:21 UTC run took ~60 s (not refused).
- So the weekly limit ran out between Sun 10:22 and 21:21 UTC and came back at the Mon 06:00 UTC reset. The
  10:20 UTC fire ran normally.
- **Nothing was lost:** no T2 was due between Fri 17:54 ET (GLXY's T2O) and today's 14:30 ET gates.
- **Health could not see it.** A refused routine run writes nothing to the repo. The "AI step refused" alarm reads
  Actions logs only; "T2 AT RISK" fires only when a PASS name is waiting.
- The usage card (`get_usage`, 09:05 ET) says the plan is **Pro**, not Max as STATE recorded. Weekly all-models was
  10% at 09:00 ET and 12% at 09:20 ET; the 5-hour window was 75% at 08:57 ET and 90% at 09:20 ET. This laptop chat plus
  one Sonnet subagent (164k tokens, the recall audit) used most of that.
- What used last week's allowance is unknown: Jacob's own chats, other routines and the experiment's chats all draw
  on it.

## Why it matters
Each PASS name needs three AI calls (T2, T2R, T2O). This week has 85 gates; at Season A's 26% pass rate that is ~22
PASS names. The peak week (Nov 2–6) is heavier still. If the limit runs out before a fire, that name's T2 is
MISSING. That is the scored decision, and it can't be redone (Rule 1).

## Expectations (written before reading the next fires)
- Tonight's 21:20 UTC (17:20 ET) `earnings-t2-cloud` fire is not refused and freezes T2 for every PASS name from
  today's 19 gates. The 21:50 UTC `earnings-t2-models` fire does the same for T2R/T2O.
- Weekly all-models stays below 60% until Fri 30 Oct 17:20 ET. That fire covers the first entries of the peak
  (Nov 2 AMC / Nov 3 BMO).
- If Friday's fire were refused, the Mon 2 Nov 10:20 UTC fire (06:20 EST, after the 06:00 UTC reset) still lands
  before the 09:15 ET deadline. It is the only fallback, and it shares the window with the reset.

## Fixes
- **Now (rule, this chat):** laptop chats in season stay lean. No subagents unless a task needs one. Read
  `get_usage` at the start of each session; at weekly ≥ 60% before a Friday, laptop work stops until the reset.
- **Owed (Tue, peak capacity):** the weekly AI allowance becomes a line in the capacity computation (calls per PASS ×
  projected PASS, against the remaining %).
- **Owed:** a check that can see a refused routine run, e.g. the laptop start-up (`ops/startup.py`) listing the last
  T2 fires via `RemoteTrigger list_runs` durations. Health in Actions cannot call that API.
