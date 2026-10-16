# D011 implementation v4 — addendum 1 (2026-10-15 ET): the routine push starts the paper window runner

- **The registered `.github/workflows/paper-window.yml`** (hashed in `D011_implementation_v4.sha256`) starts only
  from GitHub's cron. Its fires never landed in time:
  - 2026-10-14: the four afternoon fires (17:55, 18:15, 18:45, 19:15 UTC) began at 21:00, 21:43, 21:57 and
    22:18 UTC, all after the window's 15:56 ET end.
  - 2026-10-15: neither morning fire (13:35, 14:05 UTC) had started by 10:23 ET. The morning window was then
    dispatched by hand (run 38750990764) to retry DPZ's open v1 close.
- **Nothing was lost to a rule.** The frozen `paper-options.yml` crons kept sending closes (14:52 and 15:46 ET on
  2026-10-14). The runner exists so the D011 v3 2-minute cancel and resend happen on time.
- **The fix:**
  - `paper-window.yml` is left byte-identical as the registered record. Its crons stay as a second layer.
  - `.github/workflows/paper-window-push.yml`, hashed below, starts on the routine `earnings-s2-trigger`'s pushes to
    `claude/s2-trigger` (14:45, 15:45, 18:45, 19:45 UTC), the trigger that already starts the S2 gate and the C1
    capture, and on `workflow_dispatch`.
  - It runs the same `pipeline/paper_window.py` with the same two windows and the same concurrency groups. The ET
    clock at job start picks the window:
    - before 12:00, the morning window, `--only-if-active`;
    - at or after 10:30, the afternoon window, waiting for it inside the same job.
  - So in EDT the 10:45 push covers both windows in one job, ending by 15:58 inside a 345-minute timeout.
  - In EST (from 2026-11-02) the 09:45 push covers the morning only, and the 13:45 push covers the afternoon.
  - A start before 07:00 ET runs neither window, so a stray early dispatch cannot overrun the timeout.
  - **Queueing.** GitHub keeps one pending run per concurrency group and cancels the older pending run when
    another queues. Each push also starts `s2-window.yml`, whose completion queues the frozen `paper-options.yml`
    and `paper-long.yml` about 17 s later (measured 2026-10-14: push run done 15:46:57Z, frozen run queued
    15:47:01Z). Those runs take 20–35 s. The window job therefore waits behind a 150 s `settle` job, so it queues
    after that short run instead of being cancelled by it.
  - **Residual risk, disclosed:** if a long window job already holds the group (a hand dispatch, or a late
    `paper-window.yml` cron), this start waits and can be cancelled. The running job covers its own window, and a
    later push covers the rest. An afternoon start at the 14:45 EDT push misses 14:27–14:45, where only the frozen
    10-minute crons run. Before dispatching any paper workflow by hand while this job runs, cancel it.
- **Independent review** (Sonnet, read-only, 2026-10-15): SHIP WITH FIXES. Applied:
  - the settle job (finding 1: pending starts evicted by the push's own frozen run);
  - the afternoon step runs only if the morning step was reached (finding 4);
  - the 07:00 floor (finding 5).
  - The reviewer verified the clock logic, both DST mappings and the timeout. It found no same-account double send:
    one group means one running job.
- `pipeline/paper_window.py`, `paper_options.py`, `paper_long.py` and every other file in
  `D011_implementation_v4.sha256` are unchanged, and their registered hashes still hold.
- This is an operational change to the scheduler. It changes no D011 rule, no order logic and no outcome
  definition.

`c0f4e9c6f00fea43a249cd5212f08872ee394b74fcf6793971dd665285a733d1  .github/workflows/paper-window-push.yml`
