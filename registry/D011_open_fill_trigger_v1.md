# D011 opening fills: the decision trigger, v1 (frozen 2026-10-15 ~21:15 ET, before any Season A open)

**Why.** D011 v3 changed how closes are priced. Opening orders still follow v1:
- the order goes in at the indicative natural;
- it is cancelled after 15 minutes and sent at most twice (`-open`, `-open-r1`);
- if both attempts go unfilled, the trade is `open_failed: platform` and booked simulated (Jacob, 2026-10-02).

Until 2026-10-14, cron gaps meant the 15-minute cancel rarely happened: DPZ's only open filled after 32 minutes.
The window runner now enforces it. Alpaca's free quotes are randomized (CLAUDE.md), so opens may fail the way
closes did. The 10-14 chat chose to watch the first week before changing anything. This note fixes, before any
data, what "watch" decides.

**Population.** On each paper account separately (options account, structure F; long account, structure L): the
first 6 trades with `snapshot_session` ≥ 2026-10-16 that sent at least one opening order.

**Measure.** Each trade is recorded as one of:
- filled on attempt 0;
- filled on attempt 1;
- `open_failed: platform`.

These are read from the ledger's order records only. **No P&L, no result and no grade is read for this decision.**

**Trigger.** If 2 or more of an account's 6 are `open_failed: platform`, D011 v4 is drafted for that account's
opens: the v3 close ladder (natural, then +5% … +25% of |natural|, 2-minute cancel), with an independent review.
- It is frozen before the 14:30 ET of a snapshot session, and applies only to snapshots after its freeze.
- Trades already open stay under the rule they were opened under.

If fewer than 2 fail, v1 opens stay, and this note is closed with its counts.

**Reported either way:** the three counts per account in STATE.md and JOURNAL.md, and later in the paper report.

**Not covered.** `open_failed` for any other reason (a reject code, `held_by_cap`, `halt`, `never_sent`) is
counted but does not trigger. Those are rule or capacity outcomes, not fills.
