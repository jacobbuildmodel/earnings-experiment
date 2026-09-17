# STATE — Earnings Experiment

**Phase 0 → 1 · Build → Pilot** · updated 2026-09-17 · collection opens **Mon 2026-09-21**

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

  - **CHRN:** INELIGIBLE, unconfirmed. Its 10-K was already filed Aug 19; there is no company date and
    no yfinance date.
  - **PENDING:** AEHR (calendars say Oct 5, yfinance Nov 2), LEVI (calendars Oct 8, yfinance Sep 30),
    APLD (Oct 8). None of the three had announced a date as of Sep 17. Re-check before their S2 windows.
- **How company sources were found:** many IR sites are JavaScript-rendered, but their Q4 feed works:
  `https://<ir-host>/feed/PressRelease.svc/GetPressReleaseList?LanguageId=1&bodyType=0&pressReleaseDateFilter=3&pageSize=8&pageNumber=0&tagList=&includeTags=true&year=-1&excludeSelection=1`
  and `/feed/Event.svc/GetEventList?...`. BlackBerry puts its events in a script block on
  investors.blackberry.com/press-releases. AAR lists its releases on aarcorp.com/en/investors/.
  The web-search tool was down.
- **Each S2 run:**
  1. `python pipeline/s2_gate.py pilot <T> <date>`
  2. `python pipeline/factors.py pilot <T> <date>`
  3. if PASS: T2 writes `decision.json` + `thesis.md` under D004
  4. `python pipeline/freeze.py pilot <T> <date>` — for INELIGIBLE events too
- The S2 window in Singapore time is **02:30–03:50 SGT the next calendar day** (ET = SGT − 12 until
  Nov 1).
- **Automated (Jacob approved 2026-09-17):** scheduled task `earnings-pilot-s2-window`, **02:35 SGT
  Tue–Sat**, runs steps 1–4, re-checks the PENDING events, updates STATE and commits. It runs only while
  the Claude app is open and the PC is awake; a missed window is recorded as `missed_window`, never faked.
  Disable it after the pilot. Season A needs its own schedule, and **after Nov 1 (US DST ends) the S2
  window moves to 03:30 SGT**.

## Next actions

1. Run the S2 windows above (first: Mon Sep 21, 14:30 ET), and re-check AEHR, LEVI and APLD.
2. **Pin the EPS basis before building any beat or surprise factor.** Alpha Vantage gives ORCL's quarter
   ending 2026-08-31 two consensus figures — 1.39 (earnings history) and 1.74 (estimates history).
   - Check whether "N days ago" in estimates history is anchored to the report date or to today.
   - Lead (2026-09-14): the release gives GAAP EPS **$1.56** and non-GAAP **$1.92**. yfinance gives 1.74
     estimated against 1.92 reported, so **1.74 is the non-GAAP consensus**.
   - Lead (2026-09-17): Nasdaq's calendar gives the same 1.39 / 1.63 pair as Alpha Vantage earnings
     history — a shared consensus basis that is not non-GAAP. Find out what it is.
   - `factors.py` currently uses yfinance surprise, flagged "basis NOT pinned".
3. **D003 v2** for the Nov 27 early close, before 2026-10-09.
4. History study on the free factor families (A, C3–C4, D, E, F, I, J) plus the free LR candidates
   → rule v0, frozen before Oct 12.
5. External evaluator design brief → `reviews/`.
6. Probe a lead in `reviews/external_source_leads.md` only when a factor needs it (first: FINRA
   short-sale volume for LR09).

## Watch-outs

- **Alpha Vantage free key: 25 calls a day, 1 a second.** Three probes were rate-limited for firing too
  fast. The ETF-holdings endpoint the leave-one-out benchmark needs is still untested.
- The pilot screen's implied-vol column is a proxy — never reuse it as the §10 rule.
- `FRAMEWORK.md` was drafted in a chat that held PRE v1's full history. Review it with fresh eyes; the
  external evaluator is the check on that.
