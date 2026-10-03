# Cloud session brief: research work paid by the cloud-session credit

Jacob starts a claude.ai cloud session on this repo and types: **`follow ops/cloud_session_prompt.md`**.
Written 2026-10-02 by the laptop session. The credit is $100, it expires 2026-11-05, and it pays for
cloud sessions only.

---

You are working on Jacob's buy-side Earnings Experiment in a claude.ai cloud session.
- Read `CLAUDE.md` and `CHARTER.md` first, and obey every rule in them.
- Then read `STATE.md` (top section), the newest `JOURNAL.md` entry, and `registry/D009_shadow_tracks_v1.md`.
- Jacob has no coding background. Never ask him to run a command.

## Hard limits for this session

- **Work on a branch named `cloud/<topic>` and open a pull request. Never push to `main`.** The live
  pipeline (GitHub Actions) commits to `main` on its own schedule, and the laptop session reviews and
  merges your PR.
- **Never touch:** `events/`, `universe/`, `outcomes/`, `shadow/`, `paper/`, or `.github/workflows/`. No
  edit to any file listed in `registry/FROZEN.sha256`, and no new line in it. A rule you draft goes in
  `reviews/proposals/` as a DRAFT; the laptop session freezes it after review.
- Rules 9–10: never read Jacob's holdings or anything outside this repo, and never read
  `archive/PRE_v1_closed/`.
- Never fabricate data. A failed fetch is recorded as missing.
- **Before anything else, run `python check.py`.** If it says FAIL, stop and report.

## Step 0 — network probe (5 minutes)

On 2026-09-17 this environment's proxy blocked SEC, Nasdaq, NYSE and Yahoo with a 403 (`ops/cloud_probe.md`).
Re-test each with Python `requests`, 20 s timeout, sending the headers in `pipeline/common.py`:
- `https://data.sec.gov/submissions/CIK0000320193.json`
- `https://api.nasdaq.com/api/calendar/earnings?date=2026-10-06`
- `https://www.nyse.com/markets/hours-calendars`
- `yfinance.Ticker("SPY").history(period="5d")`
- `https://www.dolthub.com/api/v1alpha1/post-no-preference/options/master?q=select+1`

Write the results to `ops/cloud_probe_2026-10.md`. If any are blocked, tell Jacob in plain words to open
claude.ai/code, go to the environment settings, and set **network access to Full**, or allow those
domains. Then carry on with the tasks that need no network.

## Tasks, in order: do as many as the session allows, each committed separately

**T1 — the pooled report for D009 (needed before Season B ends; no network).**
D009 §5 registers its verdict on Seasons A and B **pooled**. `pipeline/shadow.py report` handles only
one season.
- Add a `report-pooled <seasonA> <seasonB>` command: the same tests, the same Holm m = 3, the MDE, and
  the with/without-unverified sensitivity, over both seasons' graded events.
- Use the same seeds by test name.
- Add `tests/test_shadow_stats.py`. Build synthetic data with a known mean and check that the
  intercept-only wild bootstrap (`report.wild_p_k` with X = ones) rejects at about 5% under the null
  and has power under an alternative. Check the Holm family: a test that cannot run counts as p = 1,
  and m is always 3.
- Don't change any existing behaviour of `shadow.py`. Its hash is registered, and the laptop session
  will register the new version.

**T2 — draft D009 v2: the year-round market-wide shadow (CHARTER I11).**
- Write `reviews/proposals/D009_v2_yearround_DRAFT.md`. It extends SH-M to off-season sessions.
  - The universe rule outside a season window needs a fixed, rule-based screen (rule 8). Propose one;
    for example, the last season's S1 capture plus a quarterly screen date.
  - Quantify the information gain, using `analysis/history/graded_events.json`: the variance split
    between the part a session shares and the stock-specific part is in JOURNAL 2026-10-02.
- If the network is open, count last year's off-season prints ≥ $2B per weekday from the Nasdaq
  calendar.
- Implement it on the branch, behind a new command, without changing v1's behaviour.

**T3 — the Gate 1 report builder (early December; no network).**
`pipeline/gate1.py` builds `outcomes/reports/gate1_<date>.md` from the season's report JSONs:
- D005: T1, T2, the T2 confidence test and calibration
- D008: H-S0 (`report.h_s0`)
- D009: the shadow report
- the health numbers in CHARTER §6
- the list of decisions Gate 1 must make: CHARTER I12, and promoting a D009 hypothesis

Test it on the pilot's outputs. It reads `outcomes/` and writes only the report path when it runs.
Don't run it for real in this session: just make it work on the pilot.

**T4 — only if the network is open: pre-register D010, exploration batch 2.**
- Write `reviews/proposals/D010_exploration_batch2_DRAFT.md` **before pulling any data** (rule 7).
  - 5–10 new point-in-time signals, from the literature (`reviews/literature_review.md`) and
    outside-the-box ideas, each with its sign and the paper behind it.
  - Use the D007 method: BH q < 0.10, |t| > 3, the same sign in both halves.
  - Avoid what D006 and D007 already tested.
- Commit the draft before writing any data code. Stop there: the laptop session freezes it, and only
  then may it run.

## End of the session

- Push the branch and open a PR titled `cloud: <what>`. The body says what was done, what was tested,
  what failed, and what the laptop session must review or freeze.
- Add a short dated note to `JOURNAL.md` **on the branch**: what happened, what it taught, what changed.
- Report to Jacob in plain English, in 5–8 lines.
