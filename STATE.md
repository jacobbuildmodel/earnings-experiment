# STATE — Earnings Experiment

**Phase 1 · Pilot (live)** · updated 2026-09-29 14:36 ET · pipeline hardened, D005 frozen, external
evaluation done — **the pipeline gated an event for the first time today: MU, inside the window, frozen
INELIGIBLE `thin_oi`.** The scheduler problem is over (the wait held); a **rule** problem replaced it.
MU's Oct 2 expiry carries **309,771 contracts of open interest**, and the gate rejected it on **260 at
one strike** — D003's floor is measured at the single nearest strike, which scales wrongly with share
price. That floor is unchanged in D003 v2, so Season A inherits it. Five of ten confirmed events were
lost to missed windows (PAYX · DRI · BB · AIR · JBL) and MU is out by rule, leaving **four live events**:
NKE Sep 30 · PENG Oct 5 · LEVI and APLD Oct 6.

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
  | Tue Oct 6 | LEVI AMC Oct 7 (from call time, confirmed 2026-09-23) · APLD AMC Oct 7 (session stated, confirmed 2026-09-28) | Oct 7 open |

  - **CHRN:** INELIGIBLE, unconfirmed. Its 10-K was already filed Aug 19; there is no company date and
    no yfinance date.
  - **PENDING:** AEHR (calendars say Oct 5, yfinance Nov 2), LEVI (calendars Oct 8, yfinance Sep 30),
    APLD (Oct 8). None of the three had announced a date as of Sep 17. Re-check before their S2 windows.
    **LEVI resolved 2026-09-23:** the company announced an Oct 7 call at 17:00 ET → AMC Oct 7, snapshot
    Oct 6. **APLD resolved 2026-09-28:** an Oct 7 17:00 ET call with the results release stated for after
    that day's close → AMC Oct 7, snapshot Oct 6. **AEHR is the last one PENDING**, and must resolve by
    its earliest possible snapshot session, 2026-10-01, or code marks it INELIGIBLE `unconfirmed`.
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

- **2026-09-28 (Mon) — 🔴 AIR AND JBL LOST. The wait-for-the-window fix failed its first live test.**
  This was the day the fix of 09-23 (`f70ab06`, `due.py wait`) was supposed to prove itself. It did not.
  - **What is on the record.** The only runner commit of the ET day is `b2e0e21` at **17:11:54 ET**
    (21:11:54 UTC) — the `finalize` status sync — recording both **AIR** (AMC Sep 29) and **JBL** (BMO
    Sep 30) as **INELIGIBLE `missed_window`**, checked 17:11:53 ET. That is 81 minutes after the
    14:30–15:50 ET window closed. No `Capture …` commit, no `Freeze …` commit, no `gate.json` anywhere:
    `find events -name gate.json` returns **0**, so **no pilot event has ever been gated**. No runlog for
    09-28 in `logs/actions/` (newest is `2026-09-26T0107Z`), which is expected — `due.py plan` does not
    call the AI on a non-housekeeping fire with no PASS event.
  - **Two causes still fit, and this step cannot tell them apart:**
    1. **Every fire from 10:30 ET (window − 4 h, the earliest `wait` will hold a runner) through
       15:50 ET was dropped or delayed past the close**, so no run ever reached `gate()` inside the
       window and the 17:11 run was the first to arrive. Mildly favoured: 17:11 ET is ~28 min after the
       20:43 UTC fire, the same 20–145 min lateness measured on 09-21 and 09-22.
    2. **A run did arrive in time and `s2_gate.py` crashed**, under `continue-on-error: true`, leaving
       no `gate.json`, no commit and no visible failure. The specific exposure: `opt, full =
       chain_gate(...)` at `pipeline/s2_gate.py:200` is **not** wrapped in try/except, unlike the
       fallback chain capture at :206, so any yfinance error in the option gate kills the script before
       either file is written — and the 09-28 laptop note says the option gate had never run live
       against real quotes.
    Nothing in the event directories separates them: `gate.json` is written before `option_chain.json`,
    so a crash anywhere earlier leaves exactly the empty directory we see.
  - **What would settle it, and why the AI cannot:** the Actions run list for 2026-09-28 plus the
    "Gate and snapshot every event due now" step log. `gh run list` returns **HTTP 403 Resource not
    accessible by integration** — the `s2` job grants only `contents: write` and `id-token: write`, with
    no `actions: read`. That is a one-line workflow change, and **the AI step is forbidden from editing
    `.github/`**. Until it is made, every future loss will be as undiagnosable as this one. Jacob read
    the API from outside on 09-23; that is the route again.
  - **MU's snapshot session is tomorrow, Tue 2026-09-29**, then NKE Sep 30. Whatever is wrong is still
    wrong.

- **2026-09-28 22:29 ET — housekeeping (this run).** `check.py` PASS. `due.py t2-list` empty — nothing
  awaiting T2, so no decision was written; nothing was gated or frozen by this run. Not a Friday, so no
  mid-season screen. Both PENDING names re-checked against their own company source, and **one resolved**:
  - **APLD is CONFIRMED — the last PENDING name to resolve, announced today.** Its press-release RSS
    published, at **2026-09-28 16:05 ET**, "Applied Digital Sets Fiscal First Quarter 2027 Conference
    Call for Wednesday, October 7, 2026, at 5:00 p.m. Eastern Time". The detail page states the session
    outright — the quarter ended Aug 31, 2026, a 17:00 ET call, and "A press release detailing these
    results will be issued after the market closes on the same day" — so **AMC Oct 7 is stated, not
    inferred** (`session_from_call_time` false), inside the pilot window; snapshot session **Tue Oct 6**,
    entry Oct 7 open. `events/pilot/APLD_2026-10-07/confirm.json` written.
    Second sources: **yfinance now agrees** (2026-10-07 16:00 ET, was the stale 2026-10-08 16:00); the
    Nasdaq calendar still lists APLD on 2026-10-08 `time-not-supplied` and has no Oct 7 row, so it
    neither agrees nor disagrees. `s2_gate.py` needs one agreeing second source, and has one.
  - **AEHR stays PENDING, and is now late against its own pattern.** aehr.com/newsroom (HTTP 200) does
    have a new item — 2026-09-28, "Aehr Test Systems to Participate in 18th Annual CEO Investor Summit
    2026 in San Francisco" — but it is an investor-conference release, **not** an earnings date; no FY27
    Q1 results date. yfinance unchanged at 2026-11-02 15:00 ET, intraday (unconfirmed under D003 §6) and
    outside the pilot window; Nasdaq unchanged at 2026-10-05 `time-not-supplied`. The ~2026-09-28
    announcement its own ~7-day lead implies was due **today** and did not come. Earliest possible
    snapshot session **2026-10-01**, after which code marks it INELIGIBLE `unconfirmed`. Expect that.
  - **LEVI's second-source conflict has cleared** (recorded under its `rechecks`, informational — code
    re-reads both inside the Oct 6 window). yfinance now gives 2026-10-07 16:00 ET and Nasdaq now lists
    LEVI on 2026-10-07 `time-after-hours`; both agree with the company's AMC Oct 7, so the 09-23 warning
    that LEVI would be marked `unconfirmed` no longer applies.

- **2026-09-29 14:31 ET (Tue) — 🟢 THE FIRST GATE EVER, and 🔴 MU is out by rule, not by scheduler.**
  `check.py` PASS. Code gated MU **inside the window** and froze it in the same minute:
  `gate.json` `captured_et` **14:31:00 ET**, `in_s2_window` true, freeze commit **`6da4a56`** at
  **14:31:08 ET**, entry open 2026-09-30 09:30 ET → **BLIND**, with both RFC 3161 tokens. `find events
  -name gate.json` now returns **1**. The four-hour `wait` did what the six extra fires could not.
  - **Status INELIGIBLE, reason `thin_oi`.** Everything else passed: date and session confirmed by the
    company (a 14:30 MT = 16:30 ET call, `session_from_call_time`) with yfinance 2026-09-30 16:00 and
    the Nasdaq calendar `time-after-hours` both agreeing; spot 1072.66; expiry 2026-10-02, one session
    after the reaction day; implied move **7.69%** (floor 4%); relative spreads **0.85%** call and
    0.85% put (ceiling 10%). It failed only `OI(call) + OI(put) ≥ 500` at the nearest strike: **211 +
    49 = 260**.
  - 🔴 **That is a defect in the liquidity test, not an illiquid stock.** The captured 2026-10-02 chain
    holds **309,771 contracts** of open interest across 240 call and 252 put strikes — 10,884 at the
    1100 call alone. At a $1,072 share price the strike grid is $2.50–$5 wide, so one contract is
    ~$107k of notional and per-strike OI is naturally small; a fixed 500-contract floor at **one**
    strike therefore rejects the most liquid names hardest. Everything the experiment needs — a tight
    two-sided quote and a real implied move — was there. **D003 v2 keeps `min_oi_call_plus_put: 500`
    at the same single nearest strike**, so Season A inherits it. Rule 5: MU stays INELIGIBLE and v1
    and v2 stay untouched; this goes to D003 v3 as a pre-registered change (candidates: OI summed over
    the strikes within ±1 implied move, or a notional floor, or dollar volume instead of OI).
  - The option gate had never run live against real quotes before today (the 09-28 dry run had blank
    pre-market quotes). It ran clean, retried nothing, and stored the full chain.
  - `due.py t2-list` empty — MU is INELIGIBLE, so **no T2 decision was due and none was written**. This
    step gated nothing and froze nothing; code did both.
  - **AEHR stays PENDING and is now late against its own pattern.** aehr.com/newsroom (HTTP 200) newest
    item is still 2026-09-28, the CEO Investor Summit release — an investor conference, not an earnings
    date; the newest financial-news item is still the 2026-07-14 FY26 Q4 results release. SEC EDGAR as
    the second company source: newest filings ARS 2026-09-10 and DEF 14A 2026-09-09, annual-meeting
    material, **no 8-K carrying a date**. yfinance unchanged at 2026-11-02 15:00 ET, intraday and
    outside the window; Nasdaq unchanged at 2026-10-05 `time-not-supplied` (fiscal quarter ending
    Aug/2026), and AEHR is on no Oct 6 or Oct 7 calendar row. Its ~7-day lead implied an announcement
    **yesterday**. Earliest possible snapshot session **2026-10-01** — two housekeeping runs left before
    code marks it INELIGIBLE `unconfirmed`. Expect that.
  - **NKE is tomorrow (snapshot Wed Sep 30, AMC Oct 1)** and is the first event that can actually reach
    a T2 decision.

### 🔴 The scheduler is losing the pilot — 5 of 10 confirmed events gone, and the fix did not hold

**Updated 2026-09-28: AIR and JBL make it five (PAYX · DRI · BB · AIR · JBL).** The section below is the
09-23 diagnosis and fix, kept as written; the 09-28 log entry above records that the fix did not work and
what still cannot be seen from inside the runner.

#### The original diagnosis — 3 of 10 confirmed events gone in two days

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

## 🔴 Laptop session 2026-09-28 (~07:50–08:35 ET): Season A capacity — handoff

**On main (`330b82f`):** the season screen now fires 8× across the Oct 8–9 slot, is allowed 300 min
and checkpoints its capture. The Season A calendar holds ~4,300 names, about 70 min of Yahoo calls, so
under the old 60-minute limit the screen could never have finished.

**Season A preview (not the screen): 317 candidates, 165 prints on Nov 3–5.** At that volume the
current pipeline loses events three ways:
- sequential gating overruns the 80-minute window
- one AI step cannot decide ~80 T2s before the 16:00 deadline
- the AI cannot confirm ~300 company dates by hand

**Branch `season-a-readiness` (`7f943e1`) — NOT merged; test before merging:**
- `find_dates.py`: code confirms dates from company IR feeds (5/5 pilot names correct)
- parallel gate in `due.py`, which now also commits missed-window statuses itself
- `s2-window.yml`: T2 as a per-event matrix + finalize job, whole workflow under one concurrency group
- D006 history study: draft + independent review (13 findings, all addressed) + code. `history.py
  build` computes events and PIT factors only; `study` refuses until D006 is frozen.

**Next, in order:**
1. After today's 15:50 ET window: confirm AIR/JBL `gate.json`. A dry run at 08:00 ET worked end to
   end, but pre-market quotes were blank, so the option gate itself is untested live.
2. Finish the history build (`python pipeline/history.py build`, ~2 h; no outcomes). Publish the counts
   into the D006 draft §5.1, then freeze D006 → `registry/`.
3. `history.py study` → freeze `T1_rule_v0.json` before Oct 12. Then wire T1-by-code into
   `factors.py`/`freeze.py`, and draft D004 v3: T1 by code; T2 in a hash-random order when capacity
   runs short (missing at random); stage revenue tag `...IncludingAssessedTax` (AIR and NKE read
   `unknown` today); a base-rate card before T2's research; a leak probe.
4. Test the branch on a pilot event (e.g. dispatch after an evening gate), then merge before Oct 8.
   Do NOT merge during 14:30–15:50 ET.
5. Rerun the `find_dates` hit-rate test (a 60-name sample was cut off).

Jacob asked for the ORCL/CPRT/ADBE read-throughs from the CLAUDE folder: declined (rule 9). Nothing is
needed from the evaluation model.

## Next actions

1. 🔴 **The single-strike open-interest floor is throwing away good events — fix it in D003 v3 before
   the Season A screen (Oct 9).** MU was gated cleanly on 2026-09-29 and rejected `thin_oi` on 260
   contracts at the nearest strike while its captured expiry held **309,771**. The floor is
   `min_oi_call_plus_put: 500` at the **one** nearest strike in **both** D003 v1 and v2, so it is a
   live Season A defect, not a pilot curiosity, and it bites hardest on the highest-priced, most liquid
   names. Rule 5: **do not edit v1 or v2, and do not re-gate MU** — write v3, pre-registered, with a
   measure that does not scale with share price (OI summed over strikes within ±1 implied move · a
   notional floor · dollar option volume · or drop the OI test and keep the spread test, which MU
   passed at 0.85%). Check the same arithmetic against the other high-priced Season A names before
   choosing the number.
2. 🟢 **The scheduler problem looks solved — confirm it holds.** `due.py wait` (`f70ab06`) produced the
   first gate in the pilot's history on 2026-09-29 at 14:31 ET, after failing on 09-28. Two clean
   in-window gates in a row (NKE Sep 30, then PENG Oct 5) would settle it. Still worth doing from a
   laptop session, because neither is fixed and both would have hidden today's success or tomorrow's
   failure: **give the `s2` job `actions: read`** (the AI step gets HTTP 403 on its own run history),
   and **wrap the `chain_gate` call at `pipeline/s2_gate.py:200`** the way the fallback at :206 already
   is, so a yfinance error writes an INELIGIBLE gate instead of silently losing the event. The AI step
   may not touch `.github/` or `pipeline/`.
   - LEVI's second sources caught up on 09-28 (yfinance Oct 7 16:00, Nasdaq Oct 7 `time-after-hours`), so
     the `unconfirmed` risk flagged on 09-23 has cleared. AEHR must announce by Oct 1 or it is INELIGIBLE.
3. ~~Pass `ALPHAVANTAGE_API_KEY` into `s2-window.yml`~~ — **done `420cb29` (2026-09-28).** Confirm on
   Fri Oct 2: the mid-season capture should no longer say `alphavantage: not pulled`.
   - 2026-09-28 laptop session: Jacob asked for the ORCL / CPRT / ADBE correction read-throughs in the
     CLAUDE folder. **Declined under rule 9** — nothing in `..\CLAUDE\` was opened. If a data-source
     fact is in there, it comes in by Jacob pasting only that fact, and it is re-verified against a
     primary source before it is used.
4. First grading run after an exit, and the first `report.py pilot`. Descriptive only; "insufficient".
   Note there is still nothing to grade — MU is frozen INELIGIBLE, so no event has yet reached entry
   with a PASS snapshot.
5. **Season A S1 capture:** 2026-10-08 16:00 → 10-09 09:30 ET, under D003 v2. Automate it with a
   one-off workflow that runs `nasdaq`, `av`, `market`, `screen`, or run it in a laptop session.
6. History study → rule v0, frozen before Oct 12, meeting D005 v2 §7. Pin the EPS basis before any
   surprise factor.
7. Before Season B's screening date: register `D005_confirmatory_seasonB.json`, including
   `T2_confidence`.

## Watch-outs

- **Alpha Vantage free key: 25 calls a day, 1 a second.** Three probes were rate-limited for firing too
  fast. The ETF-holdings endpoint the leave-one-out benchmark needs is still untested.
- The pilot screen's implied-vol column is a proxy — never reuse it as the §10 rule.
- `FRAMEWORK.md` was drafted in a chat that held PRE v1's full history. Review it with fresh eyes; the
  external evaluator is the check on that.
