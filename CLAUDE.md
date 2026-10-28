# CLAUDE.md — Earnings Experiment

You are running a **buy-side earnings experiment** for Jacob, a Singapore-based investor with no coding
background. He talks in plain English; you do all the technical work. Never ask him to run a command.

**The question:** before an earnings print, can we pick which stocks to BUY so the position profits from
the result — and does the answer differ by type of business?

**`CHARTER.md` is the compass:** purpose, what counts as improving (power first, then truthfulness,
signal, calibration, speed), where the edge is, the one-way valve to the portfolio model, and the
improvement backlog. Read it before choosing between options or proposing an improvement. Never settle
for "safe and working": every season ends with something tested that could make the next one better.

## SESSION HANDOFF — the trigger phrase is `pre earnings model`
When Jacob starts a new chat **in this folder** and types **`pre earnings model`** (or "PRE", "earnings
experiment", "where we left off"), read up and continue exactly where the last chat stopped. Silently:

0. **One call: `python ops/startup.py`.** It runs `git pull --ff-only github main`, `git push local main` and
   `check.py`, then prints STATE.md's start-up read: the NOW block, standing rules, Waiting on Jacob, Where
   things are, and the titles of the newest Log entries. The per-event runs happen in GitHub Actions
   (`.github/workflows/s2-window.yml`: code gates and freezes via `pipeline/due.py`, the AI step follows
   `ops/actions_prompt.md`) and commit to GitHub, so the laptop copy is behind until pulled.
   Don't commit here during 14:30–15:50 ET on a snapshot day.
1. check.py — **PASS, or stop** and say what failed. A FAIL means the record may be damaged.
2. Read the rest of `STATE.md` (the PLAN, a Log entry) only when the brief or the task names it: the full
   file costs ~20k tokens, the start-up read ~3k. With a hand-off brief, read only its READ ONLY list.
3. Read only the `FRAMEWORK.md` sections the next action needs — it is long, and this file is re-sent
   every turn.
4. Reply with a 4–6 line **WHERE WE ARE**: phase · what's done · what's waiting on Jacob · the single
   next action. Don't re-ask what he wants.

🔴 **A cloud session started by the routine `earnings-s2-trigger` does only what its prompt says** (push
one empty trigger commit to `claude/s2-trigger`). It never runs, reads or changes the experiment.
🔴 **A cloud session started by the routine `earnings-t2-cloud` does only what its prompt says** (runs
`pipeline/t2_stage2.py run --backend claude`, the D004 v4 stage-2 code, and nothing else).
🔴 **A cloud session started by the routine `earnings-t2-models` does only what its prompt says** (runs
`pipeline/t2_models.py run --backend all`, the D013 shadow code, and nothing else).
🔴 **A cloud session started by the routine `earnings-housekeeping-cloud` does only what its prompt says**
(`ops/cloud_housekeeping_prompt.md`: PENDING date re-checks written through `pipeline/hk.py`, one log line, nothing else).

🔴 **A chat that did not START in this folder must not run the experiment.** If this chat began in the
DRIVE repo and moved here, it has already loaded the portfolio's rules and memory. Say so, and ask Jacob
to start a fresh chat in `Earnings Experiment`.

🔴 **Fresh-chat rule (Jacob, 2026-10-20; threshold measured 2026-10-21; enforced by the hook since 2026-10-27). Hand off to a new chat at whichever comes first:**
- the context reaches **300k tokens** (heads-up at 250k). The threshold is measured, not guessed
  (`ops/token_efficiency_2026-10.md`; re-run `python ops/token_study.py`). The hook `ops/hooks/context_guard.py`
  (`.claude/settings.json`, on every prompt and tool call) reads the real count from the transcript;
- a work phase ends;
- **before a time-critical window** when the chat is already long: 200k in the two hours before the T2 window
  (07:15–09:15 ET, freezes before the open) and the gates window (14:30–15:56 ET, gates and paper exits).

**Enforced:** past the line, the hook refuses every tool call except the hand-off steps (read/edit STATE.md and
JOURNAL.md, git add/commit/push, `check.py`, `start_session`, the app's turn tools). It never refuses inside a live
window: finish the window's work, then hand off when it closes (no commits 14:30–15:56 ET). Only Jacob lifts it, for
one turn, by typing "override the guard".

Why: long chats lose detail and spend the 5-hour allowance the cloud routines share. Every call re-reads the whole
context: a call at 650k costs ~4× one at 125k. On 2026-10-19 a long chat got the 10:45 ET routine push refused.

How: finish the current step. **Rewrite STATE.md's NOW block** (≤ 25 lines), add the Log and JOURNAL entries, commit
and push. Then `start_session` (fresh context) with this brief, and stop working in the old chat. A chat started by
another session can't start one: it ends its turn with the same brief as its report.

    pre earnings model — hand-off from <chat>, <date, time ET>.
    TASK: <one line>.  DONE = <what exists at the end: files, tests green, pushed, what Jacob sees>.
    DECIDED: <decision · who · why, one line each; what was tried and failed>.
    READ ONLY: <path:lines — why>, at most ~6. Nothing else needs re-reading (not STATE's PLAN or Log,
      CHARTER, JOURNAL).
    FACTS: <the numbers, IDs, commits and paths the task needs, so they are not re-derived>.
    RULES THAT BITE: <hash-listed files, freezes, windows this task touches>.
    NEXT STEP: <the exact first command or edit>.  CLOCK: <deadlines in ET>.

Measured 2026-10-21: a fresh chat without such a brief took ~22 calls and +100k context before its first edit; a full
STATE.md read alone was ~20k (`ops/token_efficiency_2026-10.md`, "What a fresh chat reads").

**End of every session:** rewrite STATE.md's NOW block and add a Log entry so the next chat resumes cleanly, add the
day's observations to `JOURNAL.md` (the lab notebook: what happened, what it taught, what changed), then commit both.

## 🔴 THE RULES THAT STOP THIS EXPERIMENT LYING — never relax them
1. **Freeze before entry.** Factor snapshot, theses and all three decisions (T0 buy-all · T1 rule · T2 AI)
   are written, hashed and **git-committed before the entry open**. Anything created after the open is
   VOID, not late.
2. **One primary exit and one WIN definition, fixed before the first trade — never changed after.**
   Secondary exits are recorded and always labelled secondary.
3. **Grade every eligible name, BUY and NO_BUY.** The names we pass on are the control group.
4. **Code grades. AI never does.** The AI decides in T2; it never computes or judges an outcome.
5. **Never edit a live rule.** A change creates a NEW rule version with its own clock; the old version
   keeps being scored untouched. Editing the rule mid-measurement is what killed the previous model.
6. **Discovery is not proof.** A pattern is a CANDIDATE until it holds on data it was NOT found in.
   Never "confirm" on the data that suggested it.
7. **Count the tests.** Many factors × many clusters guarantees chance patterns. Exploration: false-
   discovery control and t > 3. Confirmation: only pre-registered hypotheses, corrected for their number.
   Under 30 events AND 10 event-dates a result is "insufficient" — never "works", never "no effect".
8. **The universe is a rule, not a feeling.** Screened once per season on a fixed date. Never add a name
   because it recently moved.
9. **Portfolio-blind.** Never read Jacob's holdings, accounts, ratings, cards or ANY file in the DRIVE
   repo (`..\CLAUDE\`). Decisions must not know what he owns.
10. **The archive is fenced.** `archive/PRE_v1_closed/` is the record of a retired model. Do NOT read it
    while forming hypotheses or making decisions — its conclusions about factors are not evidence,
    because its record was contaminated. Only the data-source facts below carry over.

## DATA-SOURCE FACTS — carried over as facts, never as hypotheses
- **yfinance `.calendar` is a day late for after-close (AMC) reporters.** Use the timestamped
  `get_earnings_dates()`, and confirm date + session from TWO sources, one of them the company.
- **SEC EDGAR returns 403 without a User-Agent header.** Always send one.
- **The clock is US Eastern** (`zoneinfo("America/New_York")`). Check ET before any freeze — a session
  can straddle a print.
- **Alpha Vantage free key: 25 calls/day, 1 per second.** Space calls and never fire them in parallel.
  Historical options are premium. Don't trust its docs on what is premium — probe.
- **Verify every figure against a primary source** before it enters a snapshot. Web summaries have
  fabricated numbers (a "$20.5B" revenue target that was really $26.5B). Flag fabrications explicitly.
- **Never fabricate market data.** If a fetch fails, record the field as missing.
- **Store the source tier with every value.** A figure said on the earnings call is company-stated,
  not filed. Many headline metrics (e.g. GPU utilisation, unit volumes) appear only on the call.
- **Read every filing in the event window** before attributing a reaction to the print. A same-evening
  8-K (an acquisition, a CEO change) confounds it.
- **yfinance's daily Open can differ from the 09:30 one-minute bar** (CPRT 2026-09-11: 32.01 vs 31.76).
- **GitHub's `schedule` is best-effort.** Fires are dropped or arrive hours late (lost PAYX, DRI and BB in Sep;
  stranded the DPZ exit on 2026-10-13). Anything that must act inside a time window starts early and waits or
  loops inside ONE job (S2: `due.py wait`; paper exits: `paper_window.py`). Never rely on a cron landing.
  Start it from the routine's `claude/s2-trigger` pushes (they land in seconds), with cron only as a backup.
- **GitHub keeps ONE waiting run per concurrency group; a newer one cancels it.** A run that must happen never
  waits in a busy group: `paper-window-push.yml`'s settle job (D011 impl v4 addendum 1).
- **The laptop's `gh` drops while it sleeps**: background jobs died with exit 4 on 10-14 and 10-15. Nothing
  that must happen runs as a laptop background job.
- **Alpaca's free options quotes are the "indicative" feed, randomized**; paper fills are judged against real
  quotes. A limit at the indicative natural may never fill (D011 v3, ops/incidents/2026-10-13_DPZ_exit.md).
- **Alpha Vantage transcripts use fiscal quarters** (ORCL's Sep 2026 call is `2027Q1`) and can lag by
  days. Returning nothing is not proof the call didn't happen.

## GIT
This is its own repo. Stage explicit paths only. New files are LF; `archive/**` is committed byte-exact
(`-text`) and never renormalised. **Commit every freeze before the entry open — the commit timestamp is
the proof the decision was blind.** After every commit, push to both remotes: `git push github main` (the GitHub copy, public since 2026-10-12 by Jacob's choice for free Actions minutes,
the cloud routine works from) and `git push local main` (the backup at `C:\repos\earnings-experiment.git`,
off OneDrive).

## HOW JACOB WANTS ANSWERS
No disclaimers, no hedging, no "consult an advisor". Say what the data says. Name-specific,
evidence-backed risk and disclosed data gaps are the product and always stay. Tables for anything
ranked. Surface the uncomfortable finding. Keep replies tight.
