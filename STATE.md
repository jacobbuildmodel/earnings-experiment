# STATE — Earnings Experiment

**Phase 1 · Pilot (live)** · updated 2026-09-25 21:06 ET · pipeline hardened, D005 frozen, external
evaluation done — **3 of 10 confirmed events have been lost to missed S2 windows and nothing has been
gated yet**, but the cause is now settled and fixed: the runner waits for the window instead of
relying on a scheduled fire landing in it. First test Mon Sep 28. See the Cloud run log.

## Where things are

| what | where |
|---|---|
| this project | `C:\Users\jacob\OneDrive\Desktop\Jacob\Earnings Experiment` — its own git repo |
| backup | `C:\repos\earnings-experiment.git`, remote `local` — push after every commit |
| PRE v1 | `archive/PRE_v1_closed/`, byte-exact and fenced — never read it while designing (`archive/README.md`) |
| DRIVE | PRE was removed there in commit `ea4d32d`; a DRIVE chat that hears `pre earnings model` sends Jacob here |

## Done

- Repo created; PRE v1 archived — 98 files, SHA-256 verified (`d256787`).
- `FRAMEWORK.md` v0.1 — outputs-first design (`ea772cf`).
- **Handoff (2026-09-14):** trigger phrase wired in `CLAUDE.md`; `check.py` health check; off-OneDrive
  backup; session-only evidence rescued into `analysis/exploratory/` (the pilot screen and the raw source probes).
- **Every figure and quote in `FRAMEWORK.md` re-checked against the saved lookups (2026-09-14).** Corrected:
  - pilot screen: **34** names passed, not 30. The "22 big movers" figure was dropped — it was annualised
    at-the-money vol, and for 8 of the 34 the option expiry ended before the report
  - replaced three overstated or unsourced descriptions ("shrinking", "on rate risk alone", "AI hardware
    manufacturing") and a false sector claim (Manchester United is Communication Services)
  - §8 no longer claims every source was probed live — only Alpha Vantage and yfinance were
  - removed an unverified claim that 1.74 "matches the consensus quoted in coverage"
  - Frazzini & Lamont: the premium tracks volume at **past** announcements, not pre-print volume
  - a link labelled "Thomas & Zhang 2008" pointed to a different, 2019 paper — relabelled
  - the calendar preview is date-sorted, so Sep 14 – Oct 9 is complete, not partial
- **PRE v1's reported figures checked against filings and call transcripts (2026-09-14).** Nothing was
  fabricated; there were mislabels and one unsupported causal story. See `reviews/ERRATA_2026-09-14_PRE_v1_figures.md`.

## Frozen 2026-09-16 — `registry/` (hash-checked by `check.py`; never edit, only add versions)

- **D001 outcome v1:**
  - Exit A is the first official open after the print. The official open is the daily-bar Open, not the
    09:30 one-minute bar: for CPRT on 2026-09-11, yfinance and Alpha Vantage both give 32.01 (probe 13).
  - **WIN = raw_return > 0** (Jacob's choice). WIN_net (20 bp) and WIN_excess are secondary.
  - **The bar is T0's hit rate, not 50%.**
  - It also fixes: price sources and their tolerance, fetch-once storage, splits and dividends, VOID rules.
- **D002 allowlist v1:** the §10 draft, verbatim. **Five terms are still judgment** (taxonomy source,
  "AI-hosting", "robotics is the product", healthcare "largest", options liquidity, plus the screening date
  and the implied-move formula). D003 must turn them into numbers before any calendar name is screened.
- `FRAMEWORK.md` is now v0.2 (§2, §3, §5, §12 match the registry; **the registry wins on conflict**).
- The WIN_excess benchmark (ETF map, beta window, leave-one-out threshold) is frozen WITH the universe.

## Literature review — DONE 2026-09-17 → `reviews/literature_review.md`

- 48 papers, each tagged by verification tier:
  - **V1**: abstract read on a primary page. Only V1 figures are quoted.
  - **V2**: bibliography confirmed only.
- **27 candidate factors, LR01–LR27**, each with the sign that favours BUY, how well its window matches
  ours, what data it needs, and its FRAMEWORK family.
- Uncomfortable points:
  - the announcement premium means **T0 is a real opponent**
  - published edges decay: about 35% after publication in McLean & Pontiff's 2012 draft, and for large
    stocks the post-earnings drift has been gone since 2006 (Martineau)
  - most papers use 3-day windows, not our open-to-open
  - many attention effects change the size of the move, not its direction
- Caught: a wrong remembered title (Jin, Livnat & Zhang); an "11%" figure absent from the paper's own
  abstract; McLean & Pontiff figures available only from the 2012 draft.
- Actions it created: probe FINRA daily short-sale volume · **capture option chains before every entry
  from Season A (or the pilot), even unused** · pin the EPS basis · choose a live sentiment proxy and
  freeze it with the universe · read each paper's method section before its factor is registered.

Not blocking: ThetaData ~$40/month for historical options, or collect free going forward (default: free) ·
a retail-attention source (default: leave it out of v0) · real trades, paper, or signals only (default: signals).

## Frozen 2026-09-16 ET (evening) — D003, D004, pipeline

- **D003 universe screen v1.**
  - S1, the season screen: pilot screen date **2026-09-17**, capture slot 00:00–09:30 ET;
    Season A screen date **2026-10-09**.
  - S2, the per-event gate: runs 14:30–15:50 ET in the session before entry.
  - Also frozen: the Yahoo industry map, the filing keyword tests, the $10B healthcare floor, the
    benchmark ETF map.
- **D004 decision protocol v1.**
  - T1 is null in the pilot.
  - T2 has fixed allowed and forbidden inputs, and **may not read this season's outcomes**.
  - BUY ⇔ confidence > 0.5.
  - Business stage comes from SEC XBRL.
- **Pipeline** in `pipeline/`:

  | script | job |
  |---|---|
  | `s1_screen.py` | season screen (steps: nasdaq · market · screen) |
  | `s2_gate.py` | per-event gate, plus the full option-chain capture |
  | `factors.py` | factor snapshot |
  | `freeze.py` | hash, commit, push; proves commit < entry open |
  | `sessions.py` | NYSE holidays, from nyse.com |

- `check.py` now also fails if any file frozen by an event manifest changes.
- ⚠ **Rule gap:** 2026-11-27 closes at 13:00, so the S2 window 14:30–15:50 does not exist that day.
  **D003 v2 must fix this before the Season A screen (Oct 9).**

## Pilot — universe frozen 2026-09-17 (`universe/pilot/`, commit f29ad02)

- The 00:01 ET background job was killed with no output. The capture was run by hand at **08:03–08:06 ET**,
  inside the slot. Nasdaq: 145 rows · Alpha Vantage: 3,760 rows · union in the window: 153 names.
- **12 candidates:** AEHR AIR APLD BB CHRN DRI JBL LEVI MU NKE PAYX PENG.
  - ⚠ **PAYX** is in because Yahoo labels it "Software - Application", although FRAMEWORK meant payroll
    to be OUT. Kept for the pilot (rule 5). Fix it in D003 v2 (e.g. exclude by name, or use SIC 7374).
- Date and session confirmation is in `universe/pilot/event_status.json`, and each event's
  `events/pilot/<T>_<date>/confirm.json` holds the company quote:

  | S2 snapshot (ET, 14:30–15:50) | event | entry |
  |---|---|---|
  | Mon Sep 21 | PAYX BMO Sep 23 | Sep 22 open |
  | Tue Sep 22 | DRI BMO Sep 24 · BB BMO Sep 24 (from call time) | Sep 23 open |
  | Mon Sep 28 | JBL BMO Sep 30 · AIR AMC Sep 29 | Sep 29 open |
  | Tue Sep 29 | MU AMC Sep 30 (from call time) | Sep 30 open |
  | Wed Sep 30 | NKE AMC Oct 1 | Oct 1 open |
  | Mon Oct 5 | PENG AMC Oct 6 (from call time) | Oct 6 open |
  | Tue Oct 6 | LEVI AMC Oct 7 (from call time, confirmed 2026-09-23) | Oct 7 open |

  - **CHRN:** INELIGIBLE, unconfirmed. Its 10-K was already filed Aug 19; there is no company date and
    no yfinance date.
  - **PENDING:** AEHR (calendars say Oct 5, yfinance Nov 2), LEVI (calendars Oct 8, yfinance Sep 30),
    APLD (Oct 8). None of the three had announced a date as of Sep 17. Re-check before their S2 windows.
    **LEVI resolved 2026-09-23:** the company announced an Oct 7 call at 17:00 ET → AMC Oct 7, snapshot
    Oct 6. AEHR and APLD are still PENDING.
- **How company sources were found:** many IR sites are JavaScript-rendered, but their Q4 feed works:
  `https://<ir-host>/feed/PressRelease.svc/GetPressReleaseList?LanguageId=1&bodyType=0&pressReleaseDateFilter=3&pageSize=8&pageNumber=0&tagList=&includeTags=true&year=-1&excludeSelection=1`
  and `/feed/Event.svc/GetEventList?...`. BlackBerry puts its events in a script block on
  investors.blackberry.com/press-releases. AAR lists its releases on aarcorp.com/en/investors/.
  The web-search tool was down.
- **Each S2 run (superseded 2026-09-21 — see the hardening section; kept for the record):**
  1. `python pipeline/s2_gate.py pilot <T> <date>`
  2. `python pipeline/factors.py pilot <T> <date>`
  3. if PASS: T2 writes `decision.json` + `thesis.md` under D004
  4. `python pipeline/freeze.py pilot <T> <date>` — for INELIGIBLE events too
- The S2 window in Singapore time is **02:30–03:50 SGT the next calendar day** (ET = SGT − 12 until
  Nov 1).
- **Automated — GitHub Actions, live 2026-09-20.** `.github/workflows/s2-window.yml` runs the PART 2
  prompt at **18:35 and 19:35 UTC, Mon–Fri** (14:35 and 15:35 ET on daylight time; 13:35 and 14:35 ET
  after Nov 1, so one fire is always inside the window). It needs nothing switched on at Jacob's end.
  Authentication: repository secret `CLAUDE_CODE_OAUTH_TOKEN`; the job fails loudly if it is missing.
  - ⚠ The laptop task `earnings-pilot-s2-window` is **DISABLED (2026-09-20)** and must stay that way.
    Two schedulers would gate and freeze the same event twice. It also fired hours late whenever the
    laptop slept — on 2026-09-18 it was due 02:43 SGT and started at 08:08 SGT, which is why it went.
  - The claude.ai cloud routine was rejected: that environment blocks SEC, Nasdaq, NYSE and Yahoo at its
    proxy (403, twice). See `ops/cloud_routine.md` and `ops/cloud_probe.md`.

## Cloud run log (GitHub Actions `.github/workflows/s2-window.yml`, PART 2 prompt)

- **2026-09-20 02:56 ET (Sun):** first live run of the Actions job. `check.py` PASS. Nothing was due —
  Sunday is not a session and no event has a snapshot_session of 2026-09-20; no gate, no decision, no
  freeze. Re-checked the three PENDING names against their company sources; all three stay PENDING
  (detail in `universe/pilot/event_status.json` → `rechecks`):
  - **AEHR** — aehr.com/newsroom newest item 2026-09-03; no FY27 Q1 date. yfinance still 2026-11-02
    15:00 ET, intraday (→ `unconfirmed` under D003 §6) and outside the pilot window.
  - **LEVI** — IR feed newest item 2026-07-08; no Q3 date. Last year the equivalent release came 14 days
    ahead, so expect ~Sep 24. yfinance still 2026-09-30 16:00; **its earliest possible snapshot session
    is Tue 2026-09-29**, before the Oct 8 calendar date.
  - **APLD** — IR RSS newest item 2026-07-27; no FY27 Q1 date. The company sets its call ~12 days ahead,
    so expect ~Sep 26. yfinance still 2026-10-08 16:00.
  - Data-source facts learned: the runner needs `lxml` or yfinance `get_earnings_dates()` raises
    `ImportError`; APLD is **not** on Q4 — `/feed/PressRelease.svc/…` 404s on `ir.applieddigital.com`
    and the working company source is `…/news-events/press-releases/rss`.
  - The Actions environment reaches Yahoo, the IR hosts and PyPI — the egress block that stopped the
    claude.ai cloud environment does not apply here.

- **2026-09-21 (Mon) — PAYX lost.** PAYX's snapshot session. No `gate.json`, no `factors.json`, no
  freeze commit was produced. The only commit of the day is `7613757` at **16:34:01 ET**, where
  `due.py gate` found `now > hi` and marked PAYX **INELIGIBLE `missed_window`**. The 23:00 UTC
  housekeeping run started **2 h 25 min late** (runlog `2026-09-22T0125Z_35675414876.json`) and its AI
  step died on `API Error: 529 Overloaded` — 0 tool calls, so no PENDING re-check and no log line that
  day. Both failures are recorded here, not fixed: the AI step may not edit the workflow.
- **2026-09-22 (Tue) — DRI and BB lost.** Same pattern. No `gate.json` for either; the only commit is
  `e714bfb` at **15:52:46 ET**, marking both **INELIGIBLE `missed_window`**. 15:52 is three minutes
  after the 15:50 ET window closes.
- **2026-09-22 21:04 ET — housekeeping (this run).** `check.py` PASS. `due.py t2-list` empty; nothing
  awaiting T2, nothing gated, nothing frozen. All three PENDING names re-checked against their own
  company source and all three stay PENDING (detail in `event_status.json` → `rechecks`):
  - **AEHR** — aehr.com/newsroom newest item still 2026-09-03; no FY27 Q1 date. `investors.aehr.com`
    does not resolve (NXDOMAIN) — the newsroom page is the company source. Its own lead time is ~7 days
    (2026-07-07 release for the 2026-07-14 print), so expect an announcement ~2026-09-28.
    yfinance unchanged at 2026-11-02 15:00 ET, intraday.
  - **LEVI** — Q4 press-release feed newest item still 2026-07-08 16:10 ET; no Q3 webcast release. The
    ~2026-09-24 date expected from last year's 14-day lead has not arrived. yfinance unchanged at
    2026-09-30 16:00. Earliest possible snapshot session **2026-09-29**.
  - **APLD** — stockpr RSS newest item still 2026-07-27 16:05 ET; no FY27 Q1 date. The ~2026-09-26 date
    expected from its 12-day lead has not arrived. yfinance unchanged at 2026-10-08 16:00.

- **2026-09-23 09:45 ET — housekeeping (this run).** The fire arrived early and the pre-check found
  nothing due, so this is housekeeping only: `check.py` PASS, `due.py t2-list` empty, no event has a
  snapshot session of 2026-09-23, nothing gated, nothing frozen, no decision written. The two scheduler
  commits of this morning (`0eb3314` six fires per window, `f70ab06` `due.py wait`) are on main.
  - **LEVI is CONFIRMED — the first PENDING name to resolve.** Its IR feed published
    "Levi Strauss & Co. to Webcast Third Quarter 2026 Earnings Conference Call" at **2026-09-23 09:00 ET**:
    the call for the quarter ended Aug 30 is "Wednesday, October 7, 2026, at 2 p.m. Pacific Time /
    5 p.m. Eastern Time". A 17:00 ET call with no session wording → **AMC Oct 7** (`session_from_call_time`),
    inside the pilot window; snapshot session **Tue Oct 6**, entry Oct 7 open.
    `events/pilot/LEVI_2026-10-07/confirm.json` written.
    ⚠ **Neither second source agrees yet:** yfinance still returns the stale 2026-09-30 16:00, and the
    Nasdaq calendar lists LEVI on 2026-10-08 `time-not-supplied`. `s2_gate.py` re-reads both inside the
    window on Oct 6 and marks the event INELIGIBLE `unconfirmed` if neither shows Oct 7 AMC by then.
    That call belongs to code, not to this step — but expect it to be close.
  - **AEHR** — aehr.com/newsroom (HTTP 200) newest item still 2026-09-03 (Lake Street conference); no
    FY27 Q1 date. The ~2026-09-28 announcement expected from its own ~7-day lead has not arrived.
    yfinance unchanged at 2026-11-02 15:00 ET, intraday. Earliest possible snapshot session 2026-10-01.
  - **APLD** — stockpr RSS (HTTP 200) newest item still 2026-07-27 16:05 ET; no FY27 Q1 date. The
    ~2026-09-26 date expected from its 12-day lead has not arrived; Nasdaq still says Oct 8
    `time-not-supplied`. Earliest possible snapshot session 2026-10-06.

- **2026-09-23 21:00 ET — housekeeping (this run, Actions run 35940775870).** The second run of the same
  ET day: the 23:00 UTC fire arrived ~2 h late again (19:00 ET due, 21:00 ET started), the same delay
  measured on 09-21 and 09-22. Nothing was due — no event has a snapshot session of 2026-09-23 —
  `check.py` PASS, `due.py t2-list` empty, no gate, no freeze, no decision. `find events -name gate.json`
  still returns nothing: **no pilot event has ever been gated.** Both remaining PENDING names re-checked
  against their own company source; both stay PENDING (detail in `event_status.json` → `rechecks`):
  - **AEHR** — aehr.com/newsroom (HTTP 200) newest item still 2026-09-03 (Lake Street conference); no
    FY27 Q1 results date. yfinance unchanged at 2026-11-02 15:00 ET, intraday. The ~2026-09-28
    announcement expected from its ~7-day lead has not arrived. Earliest possible snapshot session
    2026-10-01, so ~4 housekeeping runs remain before it must resolve.
  - **APLD** — stockpr RSS (HTTP 200) newest item still 2026-07-27 16:05 ET; no FY27 Q1 date. yfinance
    unchanged at 2026-10-08 16:00. The ~2026-09-26 date expected from its 12-day lead has not arrived.
    Earliest possible snapshot session 2026-10-06.
  - LEVI is no longer PENDING (CONFIRMED 09-23 09:45 ET); nothing new on its second-source conflict,
    which code resolves inside the Oct 6 window.

- **2026-09-24 21:02 ET — housekeeping (this run).** Nothing was due: no pilot event has a snapshot
  session of 2026-09-24 (the next is Mon 2026-09-28, AIR + JBL). `check.py` PASS, `due.py t2-list`
  empty, no gate, no freeze, no decision written, and `find events -name gate.json` still returns
  nothing. No commit was made on this ET day before this one — the 23:00 UTC fire again arrived ~2 h
  late (19:00 ET due, 21:02 ET started), the fourth day running. Both PENDING names re-checked against
  their own company source; both stay PENDING (detail in `event_status.json` → `rechecks`):
  - **AEHR** — aehr.com/newsroom (HTTP 200) newest item still 2026-09-03 (Lake Street Best Ideas Growth
    Conference); no FY27 Q1 results date. yfinance unchanged at 2026-11-02 15:00 ET, intraday. The
    ~2026-09-28 announcement its ~7-day lead implies is still four days out, so it is not yet late.
    Earliest possible snapshot session 2026-10-01.
  - **APLD** — stockpr RSS (HTTP 200) newest item still 2026-07-27 16:05 ET; no FY27 Q1 date. yfinance
    unchanged at 2026-10-08 16:00. The ~2026-09-26 announcement its 12-day lead implies is still two
    days out, so it is not yet late either. Earliest possible snapshot session 2026-10-06.

- **2026-09-25 21:06 ET (Fri) — housekeeping (this run).** Nothing was due: no pilot event has a
  snapshot session of 2026-09-25 (the next is Mon 2026-09-28, AIR + JBL). `check.py` PASS, `due.py
  t2-list` empty, no gate, no freeze, no decision written, and `find events -name gate.json` still
  returns nothing. Code ran the **Friday mid-season screen** (D003 §7) and committed
  `universe/pilot/midseason/2026-09-25.json` (`7e9484e`, 21:03:28 ET): 125 calendar names, 18 tested,
  **0 added** — 12 `industry_out`, 6 `size`. The pilot's 12 candidates are unchanged.
  - ⚠ **The mid-season screen ran without Alpha Vantage.** The capture records
    `"alphavantage": "not pulled - no ALPHAVANTAGE_API_KEY"`. The secret exists (added 09-21) but
    `.github/workflows/s2-window.yml` never passes it into the job env — `grade.yml` and
    `s1-screen.yml` both do. So every mid-season screen so far is **Nasdaq-calendar only**, a D003 §7
    deviation. The AI step may not edit `.github/`; this needs a laptop session, ideally before the
    Season A screen on Oct 9.
  - Both PENDING names re-checked against their own company source **and** SEC EDGAR as a second
    company source; both stay PENDING (detail in `event_status.json` → `rechecks`):
    - **AEHR** — aehr.com/newsroom (HTTP 200) newest item still 2026-09-03 (Lake Street); no FY27 Q1
      results date. EDGAR newest filings are ARS 09-10 and DEF 14A 09-09 — annual-meeting material, no
      8-K or release with an earnings date. yfinance unchanged at 2026-11-02 15:00 ET, intraday. The
      ~2026-09-28 announcement its ~7-day lead implies is three days out, so it is not yet late.
      Earliest possible snapshot session 2026-10-01.
    - **APLD** — stockpr RSS (HTTP 200) newest item still 2026-07-27 16:05 ET; no FY27 Q1 call
      announcement. EDGAR shows four filings dated 2026-09-25 (POSASR, DEF 14A, DEFA14A, ARS) —
      annual-meeting and shelf material, none carrying an earnings date. yfinance unchanged at
      2026-10-08 16:00 ET. The ~2026-09-26 announcement its 12-day lead implies is one day out, so it
      is not yet late either. Earliest possible snapshot session 2026-10-06.

### 🔴 The scheduler is losing the pilot — 3 of 10 confirmed events gone in two days

No pilot event has ever been gated. `find events -name gate.json` returns nothing; PAYX, DRI and BB are
all `missed_window`. Seven confirmed events remain: **AIR and JBL (snapshot Mon Sep 28) · MU (Tue Sep 29) ·
NKE (Wed Sep 30) · PENG (Mon Oct 5) · LEVI (Tue Oct 6, confirmed 2026-09-23)**. On this trend the pilot
ends with zero snapshots and D005's power problem becomes moot — there is nothing to evaluate.

What the evidence shows, and what it does not:
- **Scheduled runs start late.** Measured: the 23:00 UTC fire of 09-21 began ~01:25 UTC (+2 h 25 m); the
  23:00 UTC fire of 09-22 began ~01:02 UTC (+2 h 02 m); the gate step of 09-22 ran at 19:52 UTC against
  a 19:40 cron (+~13 m, and that alone was enough to miss by 3 minutes).
- **The 18:40 and 19:10 UTC fires left no trace at all** on either day — no commit, no runlog. Two
  explanations fit equally and cannot be told apart from inside the runner: GitHub dropped the
  scheduled runs, **or** they ran and `due.py gate` failed under `continue-on-error: true`, which exits
  green and commits nothing. `gh run list` returns **HTTP 403 Resource not accessible by integration**,
  so the AI step cannot read run history to settle it.

- **SETTLED 2026-09-23, from the Actions API (read outside the runner, in the DRIVE-folder chat at
  Jacob's request): the in-window fires NEVER RAN.** Every run on those two days, UTC:
  Mon 20:33 · 21:00 · 22:10 · 22:33 · 23:14 · 01:20(+1); Tue 19:52 · 20:08 · 21:38 · 22:01 · 22:54 ·
  01:02(+1). Nothing between 18:30 and 19:50 UTC on either day, and no cancelled or skipped run in
  the list. So GitHub dropped the 18:40 and 19:10 fires outright; `due.py` did not silently fail.
  **ROOT FIX, same day (infrastructure only, no rule touched): the runner now WAITS for the window.**
  `due.py wait` holds a run that arrives up to 4 h early until the window opens, so any fire landing
  anywhere in that five-hour span produces a gate - a dropped fire and a 2.5-hour delay both survive.
  Fires now start at 11:07 ET to give that span room. More fires alone were only shorter odds on the
  same broken dependency; this removes the dependency on trigger precision. It sleeps only when an
  ungated event is due, and a stdlib-only precheck job ends a fire in seconds when nothing is due.
  Tested on all four arrival times and live on Actions run 35868728963 (green).
  **Next test: Mon 2026-09-28, AIR and JBL.**

- **Nightly grade job was failing every night since 09-21** and nobody saw it: `grade.py --commit` ran
  `git add outcomes` before any outcome existed, which is fatal, so the job exited 1 on a pure no-op.
  Fixed 09-23: no `outcomes/` means nothing to commit, exit 0. A no-op must never look like a failure,
  or a real failure stops standing out.
- The design assumed "three fires land inside the window" makes a miss unlikely. It does not, if the
  early fires are dropped and the late ones are delayed past 15:50 ET.

**Done 2026-09-23 (was: the one thing that needed a human).** Jacob read the Actions API outside the
runner; the in-window fires were absent, not failing. Two commits followed, both infrastructure only:
`0eb3314` six fires per window on odd minutes, then `f70ab06` — **`due.py wait` holds a runner that
arrives up to 4 h early until the window opens**, so any fire landing in that five-hour span produces a
gate, and a stdlib-only pre-check ends a fire in seconds on a day with nothing due. The AI step remains
forbidden from editing `.github/`. **First real test: Mon 2026-09-28, AIR and JBL.**

## Hardening before evaluation — 2026-09-21 (laptop session, ~07:50–09:15 ET)

Everything below is committed: `c781a26` · `c5f8c6a` · `e61e01c`. Two independent reviews by a second
model (Sonnet) were run. The first covered the design and pipeline, the second D005 and the grader.
Their defects were fixed before anything went live.

**Who does what now (GitHub Actions `.github/workflows/s2-window.yml`):**

| step | who | what |
|---|---|---|
| gate + factor snapshot | **code** `pipeline/due.py gate` | inside 14:30–15:50 ET. INELIGIBLE → frozen at once. PASS → capture committed and pushed at once. No gate by 15:50 → `missed_window` |
| T2 decision + thesis | **AI** `ops/actions_prompt.md` | only for events awaiting T2 (`due.py t2-list`). `archive/` and `outcomes/` are not on disk for it (sparse checkout). Every tool call is logged to `logs/actions/`, with fence breaches flagged |
| freeze | `freeze.py` (the AI, or code in `due.py finalize`) | refuses BUY/confidence mismatches, missing `decided_et`, and inputs dated after the snapshot. Two RFC 3161 timestamps (DigiCert, FreeTSA). A lost push fails loudly. A rejected push is merged, never rebased |
| last chance | **code** `due.py finalize --last-chance` at 23:00 UTC | a PASS event with no valid T2 is frozen with **T2 MISSING**, so T0 keeps it |
| status file | **code** | `event_status.json` is synced from the frozen record (status `FROZEN`) |
| mid-season screen | **code** `due.py midseason` | Fridays in the 23:00 UTC run (D003 §7) |
| grading | **code** `.github/workflows/grade.yml` | 21:30 UTC weekdays. `grade.py --commit` writes `outcomes/` |

- **Fires (UTC, Mon–Fri):** 18:40 · 19:10 · 19:40 · 20:10 · 20:40 · 23:00. That puts three in the
  window in both EDT and EST; v1 had only one after Nov 1.
- **The laptop task stays DISABLED.**

**Fixed:**
- **factors.py stage bug.** A derived Q4 broke the next year's Q4, so PAYX, DRI and AEHR read
  `unknown`. They now read mature, mature and unprofitable_growth. Restated periods use the latest
  filing before the snapshot.
- **s2_gate.** An empty strike list no longer crashes the run.
- **check.py** now verifies the timestamp tokens and fails if any commit touches a frozen file after
  its freeze.
- **The runner checks out `main` at step time.** A run that waited in the queue could otherwise gate
  an event twice.

**New code:**

| file | job |
|---|---|
| `pipeline/grade.py` (D001) | prices fetched once; print timing checked against the company's Item 2.02 8-K; `confound_8k`; corrections |
| `pipeline/report.py` (D005) | the full evaluation |
| `pipeline/runlog.py` | logs every AI tool call |
| `s1_screen.py` | now has `screen_one` and `midseason`; re-running the pilot screen reproduces `candidates.json` exactly |

**Frozen: `registry/D005_evaluation_v1.md`** — the evaluation protocol, in place before any outcome
can be known. Implementation hashes are in `D005_implementation_v1.sha256`.
- the cluster is the entry session
- lift is tested by the wild cluster bootstrap-t, one-sided
- "insufficient" below 30 events or 10 event-dates, with no effect size produced
- Holm only over registered confirmatory hypotheses (`D005_confirmatory_<season>.json`)
- exploration needs BH q < 0.10, |t| > 3 and the same sign in both halves
- **Power:** ~100 events detect only a ~12 pp lift. One season's "no evidence" is the expected result
  even if a modest edge exists.

**Recorded deviations:**
- The 2026-09-18 Friday mid-season re-pull (D003 §7) was never run; no code existed. The 09-25
  dry run found only BSET and GNS as new names, both industry_out.
- **Mid-season screens run without the Alpha Vantage calendar** (Nasdaq only): `s2-window.yml` does not
  pass `ALPHAVANTAGE_API_KEY` into the job env, so `due.py midseason` records
  `alphavantage: not pulled`. First seen in the live 2026-09-25 screen. Needs a workflow edit from a
  laptop session — the AI step is forbidden from touching `.github/`.
- The leave-one-out benchmark is not implemented, because issuer holdings files are not fetchable.
  Every WIN_excess is flagged `bench_weight_missing`.
- Until the `ALPHAVANTAGE_API_KEY` secret exists, every graded price is `single_source`.

**EPS basis lead (2026-09-21):** coverage says the Zacks consensus for ORCL's quarter was 1.74, which
matches yfinance and the non-GAAP basis. This is a web summary, not yet verified. The Nasdaq/AV
1.39/1.63 pair is still unexplained. D005 §5 bars any EPS-surprise factor from a rule until the basis
is pinned.

## External evaluation — DONE 2026-09-21 → `reviews/evaluations/2026-09-21_external.md`

Two independent evaluators, each starting cold: E1 Sonnet, E2 Opus with an empirical-finance lens.

- **E2 verdict:** no critical flaws; the blindness machinery is "unusually strong". The binding threat
  is **power**: ~100 events give 15–40% power against realistic edges, so a single-season "evidence"
  result is likely false, or overstated if true.
- **27 findings:** 22 accepted, 3 disclosed, 1 deferred, 1 not taken. All are logged with where they
  landed.

**Frozen 2026-09-21 as new versions** (v1s stay live and scored, rule 5):

| rule | what changed | applies to |
|---|---|---|
| D003 v2 | S2 window from the close · ADP and PAYX named out (Jacob approved a payroll rule; the SIC filter was dropped after an audit showed it would remove AKAM, FICO, ROP and fintechs) · Alpha Vantage calendar by code · mid-season cap as of the screen date · `printed_before_entry` gate · stale-quote and two-expiry event-move recording | from seasonA |
| D004 v2 | T2 deadline = snapshot-session close · timed inputs on the snapshot day | from seasonA |
| D005 v2 | success needs hit-rate lift **and** return lift ≥ 0 · verdict on the full sample only · T2 confidence test (registrable as confirmatory) · within-date and leave-one-date-out · exit A split into the pre-print and print legs · gate selectivity · grading changes · disclosures · requirements for rule v0 | all seasons, pilot included; v1 printed beside it |

**Code changes with them:**
- the workflow guard: an AI edit to code, rules or workflow is restored and the run fails
- git history reads are flagged in the log
- `check.py` refuses deletions under events/universe/registry and any non-append change to the hash
  lists
- grader implementation v2 registered in `D005_implementation_v1.sha256`

## CHARTER.md — origin note (2026-09-21)

Jacob's "purpose / edge / what improving means" questions were meant for the earnings model in his
CLAUDE folder, not for this experiment. The answers written here became `CHARTER.md`. It stays, because
it holds for the experiment too. Jacob received a generic handoff file (research and sources only, no
experiment specifics) to carry into a CLAUDE-folder chat himself. Nothing was written to that folder
(rule 9).

## Waiting on Jacob

Nothing blocking. The Alpha Vantage secret was added 2026-09-21 (confirm on the first grading run: prices
should no longer be `single_source`).

## Next actions

1. 🔴 **Watch Mon Sep 28 (AIR + JBL) — the first test of the wait-for-the-window fix.** The scheduler
   change is in (`0eb3314`, `f70ab06`); nothing has ever been gated, so it is unproven. Seven events
   are left: AIR + JBL (Sep 28) · MU (Sep 29) · NKE (Sep 30) · PENG (Oct 5) · LEVI (Oct 6).
   LEVI also needs a second source to catch up to Oct 7 AMC, or code marks it `unconfirmed`.
2. ~~Pass `ALPHAVANTAGE_API_KEY` into `s2-window.yml`~~ — **done `420cb29` (2026-09-28).** Confirm on
   Fri Oct 2: the mid-season capture should no longer say `alphavantage: not pulled`.
   - 2026-09-28 laptop session: Jacob asked for the ORCL / CPRT / ADBE correction read-throughs in the
     CLAUDE folder. **Declined under rule 9** — nothing in `..\CLAUDE\` was opened. If a data-source
     fact is in there, it comes in by Jacob pasting only that fact, and it is re-verified against a
     primary source before it is used.
3. First grading run after an exit, and the first `report.py pilot`. Descriptive only; "insufficient".
   Note there is nothing to grade yet — no event has reached entry with a frozen snapshot.
4. **Season A S1 capture:** 2026-10-08 16:00 → 10-09 09:30 ET, under D003 v2. Automate it with a
   one-off workflow that runs `nasdaq`, `av`, `market`, `screen`, or run it in a laptop session.
5. History study → rule v0, frozen before Oct 12, meeting D005 v2 §7. Pin the EPS basis before any
   surprise factor.
6. Before Season B's screening date: register `D005_confirmatory_seasonB.json`, including
   `T2_confidence`.

## Watch-outs

- **Alpha Vantage free key: 25 calls a day, 1 a second.** Three probes were rate-limited for firing too
  fast. The ETF-holdings endpoint the leave-one-out benchmark needs is still untested.
- The pilot screen's implied-vol column is a proxy — never reuse it as the §10 rule.
- `FRAMEWORK.md` was drafted in a chat that held PRE v1's full history. Review it with fresh eyes; the
  external evaluator is the check on that.
