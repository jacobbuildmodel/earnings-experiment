# STATE — Earnings Experiment

**Season A live (week 2 of 6) · D015 C1 live (blind) · Max plan** · updated 2026-10-19 12:00 ET · roadmap `RESEARCH_PLAN.md` · lab notebook `JOURNAL.md` (newest first) · **history before 2026-10-14:** `ops/state_history/STATE_2026-09-14_to_2026-10-13.md` (moved verbatim 2026-10-19, so this file can be read in full).

## PLAN — Mon 2026-10-19 (today) and the next session · ~08:55 ET (committed 09:05, `22de568`) · reviewed (Sonnet: SOUND WITH CHANGES, all applied)

**Purpose this fortnight.** Season A is in week 2 of 6, and its power is decided now:
- 238 of 318 names have no confirmed date, and 153 of them are dated Oct 31–Nov 6.
- Every Season A gate so far has failed.

The job is to capture every eligible event truthfully: dates found, gates run, T2 proven, paper covered. Then to
build the counts-only evidence for Season B's gate decision (CHARTER I1), with no outcome read. **Order: power,
then truthfulness**, as CHARTER §6 ranks them.

**Status at 09:00 ET** (counts only; no outcome read)

| area | now | why it matters |
|---|---|---|
| Season A dates | 318 names: 80 confirmed, **238 PENDING** (4 dated ≤ Oct 23, 41 Oct 24–30, **153 Oct 31–Nov 6**, 40 later) | 🔴 **a detection gap, not the companies.** Confirmed names were announced a median 21 days ahead (p10 14, min 10), yet only 9 names dated Nov 3–6 are confirmed (n = 80, checked 09:00 ET) |
| S2 gates | 4 run, **0 PASS**, all `wide_spread`; the pilot had 3 PASS of 5. `gate.json` records only the first failing check. DPZ (OI 248) and VICR (28) would also fail `thin_oi`. **Only RTX was a near-miss** (put 12.8%). NOC and VICR were gated on the Nov 20 monthly | 🔴 0 T2 decisions in Season A. H-T2C needs ≥ 10 PASS-with-T2 events and ≥ 5 sessions in Season A (D005 v3) |
| snapshots ahead | this week 21 (Mon 2 · Tue 6 · Wed 8 · Fri 5); Oct 26–30: 44; the first peak snapshots are Thu Oct 29 | the projected PASS count becomes measurable |
| C1 (D015) | 78 events, 19 graded, 2 C1 on 1 date (blind) | look 1 from Dec 7 needs ~27 C1 dates |
| paper | options: NOC, RTX, VICR (v3) all filled at attempt 0. DPZ expired unclosed → **+100 DPZ shares assigned** (health RED). Long: RTX, VICR open; NOC `open_failed: platform` | first v3 closes **Tue 14:30 ET**. Open-fill trigger: options 0/3, long 1/3 |
| infra | push runner OK. **Fri: "runner lost communication"** (GitHub). The long account went uncovered ~14:52–15:37 ET, and the job looked "running" all along. Ubuntu 26 probe PASS (262 tests). T2 cloud routine enabled, last run green 10:21 UTC today | a dead runner is invisible to health |
| 🔴 **Actions AI step** | **refused every night since Oct 15**: "Your organization has disabled Claude subscription access for Claude Code". The job stays green and health missed it | 3 nights of PENDING re-checks lost. The Actions T2 fallback is dead; the cloud T2 path is unexercised since 10-08 |

**Today, by clock** (ET · SGT = ET + 12 until Nov 1)

| ET | SGT | what | who |
|---|---|---|---|
| now–14:00 | –02:00 | **Date detection.** Hand re-check the 4 names dated ≤ Oct 23 (SMMT, GE, GLXY, CORZ), then the 41 dated Oct 24–30. **Recall audit:** 10 random PENDING names dated Oct 31–Nov 6; for each, does a company source already state the date? A miss rate > 2/10 is a `find_dates` defect, to fix this week | this session |
| 09:30 → | 21:30 → | **DPZ shares** (decision 1) | Jacob |
| ~10:45 | 22:45 | routine push → the runner holds both accounts to 15:56. The first sync settles DPZ at intrinsic (`held_past_expiry`, simulated) | code |
| before 14:30 | before 02:30 | **commit expectations for Tue's first v3 closes** (below) | this session |
| 14:30–15:50 | 02:30–03:50 | ABT and PEGA gates. A PASS freezes stage 1, and the cloud T2 runs 17:20, 21:20, 01:20 and 06:20 ET. Paper opens follow every gate | code |
| 15:25–15:55 | 03:25–03:55 | C1 capture for R = Tue Oct 20 | code |

**Expectations for Tue's first v3 closes** (committed before they happen; descriptive, not a rule). There are 5
closes: NOC, RTX, VICR butterflies (F) and RTX, VICR straddles (L).
- All 6 real opens filled at attempt 0, 3–56¢ inside the indicative far side. DPZ's v1 closes failed with 4 legs,
  including wings with no bid, which v3 now drops.
- **Expect ≥ 4 of 5 to fill at attempt 0.**
- If ≥ 2 need a concession, the indicative-feed cause gains; if they fill at 0, the zero-bid/multi-leg cause does.
- **If any is unfilled at 15:10 on its expiry day, that is an incident.**

**Decisions for Jacob** (recommended default first)

1. **DPZ's 100 assigned shares (paper account).** **Recommended: you place one market sell in the Alpaca paper
   dashboard today, and I log it as non-experiment housekeeping.** The D011 result is already fixed by rule:
   intrinsic on the Oct 16 close, simulated. The shares are leftover exposure no code closes. They tie up ~$30k of
   buying power before the peak, and they keep health RED, which hides a real RED. I then confirm the RED clears,
   and that the fill re-check and the report views ignore an order that isn't in a ledger.
2. **How the nightly AI housekeeping runs again.**
   - **(a) Recommended:** a new `CLAUDE_CODE_OAUTH_TOKEN` from your Max account, which you paste into the GitHub
     secret yourself. It shares your plan's limits with your chats, but housekeeping costs ~$0.2 a night.
   - **(b)** Move it to a cloud routine. That needs the cloud environment's Network access set to Full, and it loses
     the Actions-side guards.
   - **(c)** Laptop sessions do it by hand: no action from you, but only on days a session runs.
   - **Meanwhile, (c) runs from today.**

**Next session — Tue Oct 20. Start it by 06:35 ET (18:35 SGT) if ABT or PEGA passed.**
1. Start-up: pull, check, STATE, `ops/health/latest.md`.
2. **T2 deadline, 09:15 ET.** For a Monday PASS, `manifest_t2.json` must exist. If it is missing by 06:35 ET, run
   the same protocol from the laptop by 08:45: `T2_ALLOW_LOCAL=1 python pipeline/t2_stage2.py run --backend claude`.
   **Never substitute T2G** (D005 v3). Any miss is an incident (`ops/incidents/`, expectations first).
3. **Before 14:30 ET (before any NOC/RTX/VICR paper P&L is read), freeze D016, the gate audit, counts only.**
   - It reads only `events/**/gate.json` and `option_chain.json`, with a test that it never opens `outcomes/`.
   - It re-runs the **full check cascade** on every Season A gate and reports counts per check, plus pass rate by
     price bucket.
   - Alternatives are only what the stored chain supports: the better of the two nearest strikes, and a
     dollar-spread floor for cheap options. A mid-window spread and a next-expiry gate need a forward capture in a
     separate file.
   - **Disclosed:** the design was informed by the first four failures. No Season A return selects or justifies
     the rule (rule 6; D005 v3's interim clause). Pooled H-T2C will mix two gate versions.
   - The decision rule turns counts into a D003 v5 proposal for Season B. Run it Fri Oct 23 evening.
4. Date detection: the re-checks still owed, and a fix if today's recall audit found a `find_dates` defect.
5. **After 15:56 ET:** the first v3 closes against the expectations above. Count the open-fill trigger with
   Monday's opens. Run `paper_options_report_v2.py --write`.
6. Build three alarms in `health.py`:
   - **AI step refused** (`is_error` in the runlog);
   - **dates stale** (no PENDING status change in 30 h while names dated within 7 days exist);
   - **runner not acting**: an Alpaca order live past its rule's cancel limit (v3 close 2 min, v1 15 min) + 5
     minutes, inside the window, while a window job claims to run. It must cancel the stale run before
     re-dispatching. This checks the broker, not commits: healthy ledger commits cluster ~18 minutes apart.
7. End: STATE and JOURNAL.

**To Gate 1 (early Dec), by charter lever**
- **Power:**
  - Date-detection recall first: it gates every track.
  - **The projected PASS-with-T2 count by Nov 20** against Season A's minimum of 10 plus 20% headroom (12), and ≥ 5
    sessions.
  - D016 → a D003 v5 proposal for Season B (Jacob's call before the Season B screen, on counts only).
- **Confirmation checkpoints** on the lead-time curve: by **Oct 22** ≥ 70% of names dated Oct 31–Nov 6 confirmed;
  by **Oct 25** ≥ 90%. Each session, a hand audit of 10 random PENDING names measures recall.
- **Peak capacity, computed by Oct 27:**
  - the maximum concurrent paper structures times their margin, against equity;
  - `held_by_cap` counted as an outcome;
  - gates, T2 and C1 at ~165 prints Nov 3–5.
- **DST, by Oct 28:** inventory every cron and routine from UTC to ET. **Mon Nov 2 is a watch day:** the first EST
  session, the day before the peak.
- **Truthfulness:** the housekeeping path restored, the three alarms live, T2 proven on the first PASS, DPZ cleaned
  up.
- **Signal:** C1 stays blind. Look 1 is written by code from Dec 7, Season A alone at p < 0.005.
- **Calibration:** write, test (synthetic) and register the pooled H-T2C code before the Season B screen (owed
  since 10-06).
- **Speed:** a Gate 1 report dry run on structure only (no outcome printed) by mid-Nov.

**What would change this plan**
- **Projected PASS-with-T2 by Nov 20 < 12** (or < 5 sessions): H-T2C is at risk for Season A, and RQ3/RQ5 cannot be
  answered from it. Gate 1 then rests on the shadows (SH-M, SH-X, C1, H-S0), and D003 v5 becomes Season B's first
  decision.
- **T2's cloud call fails on the first PASS:** an incident, and the backend is decided before the next PASS.
- **A checkpoint missed** (Oct 22 < 70%, Oct 25 < 90%), or recall misses > 2/10: date-finding becomes the
  session's only task until fixed.

## Standing rules for every session (consolidated 2026-10-19 from the dated entries; each source is in the log or history)

- **Hash lists bind edits.** `check.py` FAILS on an unregistered edit to the D004 v4 files: `dossier.py`,
  `t2_stage2.py`, `freeze.py`, `due.py`, `grade.py` and `t2-queue.yml`. It FAILS the same way for D015 v1, which
  includes the shared `shadow.py`, `sessions.py`, `common.py` and `s1_screen.py`. A change there needs a dated
  line in that list.
  - A list frozen in `registry/FROZEN.sha256` (e.g. D011 v4) is never edited. Add a new file plus a frozen addendum
    instead, as `paper-window-push.yml` and `D011_implementation_v4_addendum1.md` did.
- **T2 is bound for Season B** (D005 v3). Editing `dossier.py` or `t2_stage2.py`, even as a bug fix, ends the A + B
  pooling of H-T2C and obliges a v4 shadow. The Season B confirmatory file must NOT register `T2_confidence`.
- **C1 is blind** until a look. `shadow_c1.py status` prints counts only. Never print a C1 mean, t or p. Look 1 is
  written once by code from 2026-12-07.
- **Paper numbers** go out at fill, mid, halfway and far side; all trades vs v3 only; with and without DPZ
  (`paper_options_report_v2.py --write`). The mid flatters: every real open paid 91–99% of the half-spread.
- **Count the open-fill trigger** (`registry/D011_open_fill_trigger_v1.md`) each session until each account has 6.
  2 or more `platform` failures on an account → draft D011 v4 for opens.
- **Before hand-dispatching any paper workflow while a window job runs**, `gh run cancel` the window job first.
  GitHub keeps one waiting run per group.
- **No commits 14:30–15:56 ET on a weekday** (the S2 gates, the paper window, the C1 capture).
- **DST ends Sun Nov 1.** ET = SGT − 13 from Mon Nov 2. The routine pushes land at 09:45, 10:45, 13:45 and 14:45 EST.
  - `paper-window-push.yml`: the 09:45 push covers the morning, the 13:45 push the afternoon.
  - The fill re-check runs 07:30 and 16:50 EST.
- **The repo is public** (free Actions minutes). If it is ever made private, the waiting jobs exhaust the minutes:
  move every trigger to routine pushes first.
- **Owed before the Season B screen:**
  - the pooled H-T2C code, tested on synthetic data, reviewed and hashed (D005 v3);
  - `D005_confirmatory_seasonB.json` without `T2_confidence`;
  - the D003 v5 decision (CHARTER I1, Jacob's call, on counts only).

## Waiting on Jacob

1. **DPZ's 100 assigned shares** in the paper options account. Recommended: flatten with one market sell at the
   open, recorded in JOURNAL. (Plan, decision 1.)
2. **The Actions AI token**, `CLAUDE_CODE_OAUTH_TOKEN`, refused since Oct 15: "organization has disabled Claude
   subscription access for Claude Code". Recommended: re-issue it from his own Max account. (Plan, decision 2.)
3. **Before the Season B screen:** the D003 v5 gate change, if D016 supports one.
4. **Before Gate 2 (Mar 2027):** the real-money sleeve and its loss limit (D008 v2).
- Closed: an Anthropic API key (declined 2026-10-08, no new money until results); Fable credits (the same rule).

## Where things are

| what | where |
|---|---|
| this project | `C:\Users\jacob\OneDrive\Desktop\Jacob\Earnings Experiment` — its own git repo |
| backup | `C:\repos\earnings-experiment.git`, remote `local` — push after every commit |
| GitHub | `jacobbuildmodel/earnings-experiment` (public); per-event runs in Actions; routines push `claude/s2-trigger` |
| cloud routines | `earnings-s2-trigger` (pushes 14:45, 15:45, 18:45, 19:45 UTC) · `earnings-t2-cloud` (`trig_01H4HJJ2uPLZXUwfi7q5fXr3`, 01:20, 05:20, 10:20, 21:20 UTC) · `earnings-t2-models` (`trig_017LGhgRnK6WZ3SwHFNK4Gyb`) |
| history before 2026-10-14 | `ops/state_history/STATE_2026-09-14_to_2026-10-13.md` (verbatim) |
| PRE v1 | `archive/PRE_v1_closed/`, byte-exact and fenced — never read it while designing (`archive/README.md`) |
| DRIVE | PRE was removed there in commit `ea4d32d`; a DRIVE chat that hears `pre earnings model` sends Jacob here |

## Log — newest first (2026-10-14 onward)

**2026-10-19 (Mon) ~12:00 ET — date detection: a recall audit, four `find_dates` defects fixed, 35 names confirmed.**
- **Recall audit** (10 random PENDING names dated Oct 31–Nov 6, read-only): **3 had a company date that code missed**,
  over the plan's 2/10 limit. So it was a defect, fixed the same morning. The 13 urgent names read by hand showed
  more.
  - **Fixes** (all tested; `find_dates.py` is in no hash list; D003 §6 unchanged):
    1. `0fa8506`: only dates from today on count. A release's own dateline counted as a second date → "ambiguous"
       (GLXY, CORZ, EEFT, BDC, IDCC, YUMC, LYFT).
    2. `48f00db`: the ACCESS Newswire dateline (MRNA's own release was skipped as "not a release").
    3. `33cf370`: "US" / "U.S ." in after-close wording (STX, GDDY); "before trading begins" (TEL).
    4. `33cf370`: release wording on one date outranks the next session's call (CLS, TER, PLXS, MUSA, VSEC). A
       results date with no wording plus a call stays ambiguous.
- **Confirmed (`5d88d4f`):** 32 by code with the fixes, plus 3 by hand from the company's words (FTAI, LOGI,
  JMKE). SMMT retired `unconfirmed`. GE has no company date (its second sources say BMO Oct 20, snapshot passed);
  it stays PENDING until today's window closes.
  - **Season A: 111 CONFIRMED + 4 FROZEN (was 76 + 4), 202 PENDING (was 238).**
- 🔴 **The peak is still dark:** 16 of 152 names dated Oct 31–Nov 6 are confirmed (11%), against the plan's ≥ 70% by
  Oct 22. The 202 PENDING:
  - **132 `no_date_announced`** on the feed code reads (not yet audited against the company sites);
  - **50 `found`**, where the company states date and session but no second source agrees yet (e.g. EW and NET:
    yfinance stamps 15:00, Nasdaq after-hours, which counts as a disagreement);
  - 10 no session, 5 ambiguous, 3 no feed, 2 intraday call.
  - **Next session's first power task: the 50 `found`.** Are the second sources lagging (they confirm themselves),
    or is yfinance's stamp wrong (a rule question for the second-source check)? Then a hand audit of 10
    `no_date_announced` names against the company IR sites.
- Today's evening run (Actions, 23:00 UTC) has all four fixes and takes the 32 names this pass left.
- **Jacob, today:** selling DPZ's 100 paper shares; re-issuing `CLAUDE_CODE_OAUTH_TOKEN` (the sign-in is open in the
  Terminal tab "Claude token for GitHub"). After the token: dispatch one housekeeping run to prove it.

**2026-10-16 (Fri) ~21:30 ET — the promised paper report views are built, reviewed and FROZEN (`d424bca`).**
- **What:** `registry/D011_report_views_v1.md` and `pipeline/paper_options_report_v2.py`.
  - Run: `python pipeline/paper_options_report_v2.py seasonA --write`. It writes
    `outcomes/paper/options_report_v2_seasonA_<date>.md` and `.json`. The first is the 10-16 one.
  - The frozen report (`paper_options_report.py`, implementation v3) is byte-identical and stays the report of
    record. A test guards it.
  - **Views:**
    - every P&L figure at the fill, mid, halfway and far side; the headline is the trades priced at all four;
    - all trades, v3 only, and without DPZ;
    - fill rate from order records only: opens at attempt 0 / attempt 1 / platform, v3 closes by concession step;
    - the open-fill trigger's counts (ties within one run go by the order the frozen code sent them);
    - execution against each order's own quotes;
    - each order against real exchange prints.
  - **Real prints:** `pipeline/paper_fill_recheck.py` and `.github/workflows/paper-fill-recheck.yml`.
    - Runs at 07:30 EST / 08:30 EDT and 16:50 EST / 17:50 EDT; never in the paper window.
    - Fetches each order 12 h after its window ends. Raw and write-once in `paper/fill_recheck/seasonA/`.
    - It checks its own hashes (`registry/D011_report_views_implementation_v1.sha256`) before fetching.
    - **First live fetch (run 38990228211):** 20 DPZ orders stored and pushed. The 16 orders of 10-16 wait for the
      12 h rule.
- **Probe (free plan; `ops/probes/alpaca_options_history_2026-10-16.json`):**
  - Historical 1-minute bars and trades answer, also for expired contracts.
  - There is no historical quotes endpoint (404). **What the real quote was can never be checked after the fact.**
  - The latest OPRA trade, and a daily range ending today, return 403 "OPRA agreement is not signed".
- **First look (descriptive; 6 real opens, one day):** every open filled 3–56¢ better than its limit (the indicative
  far side), and paid 91–99% of the half-spread. **The mid column will flatter every result.**
- **DPZ's failed v1 exit against real prints** (19 closes, Oct 13–15; one trade, descriptive):
  - Of the 30 legs that printed while a close was live, 29 printed at or through our recorded far side.
  - No close ever had prints on all four legs, so whether the whole order was marketable is unknown.
  - So no leg's price looks to have been the obstacle.
- **Open-fill trigger tonight:**
  - options: 3 of 6 counted, all filled at attempt 0;
  - long: 3 of 6, 2 at attempt 0 and NOC `open_failed: platform`.
  - Neither has fired; 2 platform failures among an account's first 6 fire it.
- **Review:** Sonnet, read-only, two passes. Both SHIP WITH FIXES, all applied (listed in the spec). The tie rule was
  checked by brute force on 4,000 random ledgers.
- **Tests:** 261 passed, 1 skipped. `check.py` PASS.
- 🔴 **From Mon 10-19:**
  - Every D011 P&L number goes out at fill / mid / halfway / natural, all vs v3 only, with DPZ in and out. Run the
    report with `--write` when reporting, and commit its outputs.
  - Count the trigger from its table each session until 6 per account.
- 🔴 **Watch Sat 10-17 08:30 ET:** the scheduled fetch should store the 16 orders of 10-16. If it drops, dispatch
  `paper-fill-recheck.yml` (it catches up).

**2026-10-15 (Thu) ~20:50 ET — evening check: the push runner covered both accounts; the first C1 grade (blind counts).**
- **Paper window, first live day of `paper-window-push.yml`:**
  - **long:** the 10:45 push's job ran 10:48–15:56.
  - **options:** the 10:45 push's job waited behind the 10:23 hand dispatch and was cancelled at 11:46, exactly as
    the review predicted. The 11:45 push's job ran 12:00–15:56.
  - Health at 19:41: both "done". The "cancelled" runs in Actions are those waiting starts, not failures.
  - `paper-window.yml`'s crons: 2 waiting starts were cancelled, and 4 began 16:34–18:19 ET, after the window.
  - The laptop's 12:05 backup dispatch failed (exit 4 after its sleep; nothing sent). Laptop background jobs are
    no backup.
- **DPZ (v1):** 19 closes sent, none filled. At 19:41 it had 4 legs and no open order.
  - DPZ closed at 303.09, so the short 310 put is ~$7 in the money.
  - Fri Oct 16 is expiry, and closes continue all day.
  - **If it never fills:** the ledger settles it at intrinsic on the expiry close, labelled simulated (D011 v1 rule).
    Alpaca will likely assign the put, so expect **+100 DPZ shares in the options account Mon Oct 19**, and health
    RED "assigned shares".
  - Then flatten the shares on the paper account with one market sell, recorded in JOURNAL. That has no effect on
    any result.
- **C1 (D015), first grade:** the 18:50 grade cron had not landed by 20:35. It was dispatched by hand (run
  38830571544). Grading is retry-safe: any later run grades every settled R.
  - **R = Oct 15:** 12 events. 8 graded, 3 void `not_domestic_foreign`, 1 void `print_contradicted`.
  - Blind counts only: 6 with |gap| ≥ 1%, 5 with an implied move, **2 C1 events, on 1 date**.
  - **Capture 10-15 (for R = Oct 16): 9/12.** INDB and WAFD `no_quote`, SFNC `no_strike`.
- 🔴 **Watch Fri Oct 16:**
  - the 10:45 push should hold both accounts 10:48–15:56; the 14:45 health run checks it
  - DPZ's last resends
  - NOC/RTX/VICR gates from 14:30, then the first v3 opens
  - the C1 capture for R = Mon Oct 19
  - Mon: DPZ assignment, shares to flatten
- **~21:15 ET, refinements from a review of the Experiment sessions (`4cb5ec4`):**
  - **Opening fills now have a pre-committed trigger** (`registry/D011_open_fill_trigger_v1.md`, frozen). Count each
    account's first 6 opens from snapshot 10-16 as filled at attempt 0, filled at attempt 1, or
    `open_failed: platform`. 2+ failures on an account → draft D011 v4 (v3's close ladder for opens). Fill counts
    only, never P&L. 🔴 **Count them each session until 6 per account.**
  - **CLAUDE.md:** start must-happen jobs from the routine push; one waiting run per concurrency group; the laptop's
    `gh` drops while it sleeps.
  - **`legs_exploratory.json` committed** (D007's input), so check.py runs with 0 warnings.
  - ✅ **Built and frozen 10-16 (`d424bca`, entry above). Promised on 10-14 and not built:** the paper report's three prices (mid, halfway, far side), with and
    without DPZ, v3-only, fill rate as an outcome, and a re-check of fills against real exchange data. Needed
    before the first v3 numbers are reported (closes from Mon Oct 19).

**2026-10-15 (Thu) ~11:45 ET — two new health alarms: paper window coverage, and Alpaca positions vs the ledgers (`169530a`).**
- **Why:** nothing alarmed on 10-14 when every cron start of the window runner landed after the window. The paper
  ledgers had never been checked against the accounts' real positions (backlog item, 10-14 research).
- **Paper window coverage** (`pipeline/health.py` `paper_window`). Full sessions only, from 14:40 ET. Per account
  (options and long), it reads today's runs and job steps from the Actions API.
  - **GREEN:** a `paper-window-push.yml` or `paper-window.yml` afternoon step started by 14:45 and is running (once
    the window is over: it ran to 15:56).
  - **AMBER LATE:** the step started after 14:45.
  - **AMBER NOT RUNNING:** no window step, but a frozen `paper-options.yml` / `paper-long.yml` run completed in the
    last 25 minutes.
  - **RED NOT COVERED:** neither, while the window is open. The message says to dispatch `paper-window-push.yml`.
    Once the window is over, the same finding is AMBER.
  - **Replay of the real 10-14 record:** RED at 14:46, AMBER at 15:20 and 16:20. The frozen runs landed 14:46,
    14:52, 15:16 and 15:46, and the spec makes frozen-only coverage AMBER.
- **Positions vs ledgers** (`positions_check`). Read-only GET `/v2/positions` and `/v2/orders?status=open&nested=true`.
  - **Options account** (`APCA_*`): `options_ledger.json` **plus `ledger.json`**, because paper.py's T0 shares trade
    on the same account.
  - **Long account** (`APCA_L_*`): `long_ledger.json`.
  - Holdings are computed per contract from every filled order's `legs_filled`, so a v3 close's dropped long leg
    stays expected.
  - **RED** needs the same mismatch on a second look 2 minutes later, with the account and the git-fetched ledgers
    re-read:
    - a position or open order no ledger shows live
    - a live ledger position the account lacks
    - an open order the ledger records as ended
  - **A live ledger order on the symbol** makes a mismatch information while the order is young (options 30 min,
    shares 26 h), AMBER up to 24 h, then RED "LEDGER STALE".
  - **Smaller cases:**
    - an unknown open order under 15 minutes old is information
    - options are no longer expected after their expiry-day close; one still listed the next day is AMBER
    - assigned shares are RED: real stock exposure that no code will close
- **`health.yml`:**
  - The Alpaca paper keys are on the health step only.
  - It now also runs on the routine's `claude/s2-trigger` pushes, so one health run lands at 14:45 ET in EDT and
    EST, inside the window.
  - `workflow_dispatch` takes `dry: true`: it prints the report plus `--shapes` (each account's open orders and
    positions) in the log, with no commit and no issue.
- **Review:** Sonnet (independent, read-only) said SHIP WITH FIXES. Applied:
  - age-bounded lag (a frozen ledger was excused forever)
  - a crashing check becomes AMBER
  - AMBER once the window is over
  - nested multi-leg children skipped
  - only running steps count inside the window (a 2-second step at 14:44 had read as coverage)
  - one API retry
  - step names bound to the YAML by a test
  - young unknown orders are information
- **Tests:** 49 health tests on recorded Actions fixtures (10-14 and 10-15) and the real DPZ trade record. Full
  suite 210 passed, 1 skipped. `check.py` PASS.
- 🔴 **Watch:**
  - ✅ **First dry dispatch, run 38762134094 (11:38 ET): both accounts match the ledgers.**
    - Options: 4 DPZ legs and open close r12, one rolled-up `mleg` order with its legs nested.
    - Long: flat.
    - No leftover probe positions.
    - The shape is recorded in `tests/fixtures/health_alpaca_shapes_2026-10-15.json` and tested.
  - **Fri Oct 16, 14:45 ET push run:** paper window GREEN.
  - **Fri Oct 16 evening, DPZ expiry:** if the short 310 put is assigned, the next health run is RED, showing DPZ
    shares no ledger holds. That is correct; a person has to close them.

**2026-10-15 (Thu) ~10:40 ET — the paper window runner now starts from the routine push (`f4f3c20`).**
- **Why:** `paper-window.yml` starts only from GitHub cron, and its fires never landed in time.
  - 10-14: the 4 afternoon fires began 21:00–22:18 UTC, after the 15:56 ET end.
  - 10-15: neither morning fire had started by 10:23 ET.
  - DPZ's v1 close was retried only by the frozen 10-minute crons and by hand.
- **Today, by hand:**
  - The morning window was dispatched at 10:23 ET (run 38750990764). DPZ's 9th close went out at 10:24 ET at a
    10.73 natural debit, against 15.60 at 15:46 yesterday.
  - A laptop background job dispatches `paper-window.yml` afternoon at 12:05 ET, as a backup. It dies if the app
    closes.
- **The fix:** `.github/workflows/paper-window-push.yml`, registered as `registry/D011_implementation_v4_addendum1.md`
  (frozen). `paper-window.yml` and every D011 v4 file are byte-identical.
  - It starts on the `earnings-s2-trigger` pushes (14:45, 15:45, 18:45, 19:45 UTC) and picks the window by the ET
    clock: morning before 12:00, and afternoon from a 10:30 start, waiting inside the job.
  - In EDT the 10:45 push covers both windows. In EST the 09:45 push covers the morning and the 13:45 push the
    afternoon.
  - A 150 s settle job comes first, so the push's own frozen paper run (queued ~17 s after the push, 20–35 s long)
    cannot evict it from the one-pending-per-group queue.
  - Sonnet review: SHIP WITH FIXES, all applied.
- 🔴 **Ops rule:** before hand-dispatching any paper workflow while a window job runs, `gh run cancel` it.
  Otherwise the dispatch waits hours behind it, or is cancelled.
- 🔴 **Watch:**
  - the 10:45 ET push today (the long account should start; options waits behind the hand dispatch)
  - Fri Oct 16: the 10:45 push should hold `paper-options` through 15:56. That day has DPZ's expiry (v1, last
    resend), NOC/RTX/VICR gates and the first v3 opens.

**2026-10-14 (Wed) 12:09 ET — D015 v1 FROZEN (`bd67722`): C1 live, the confirmatory test of D014's one survivor.**
- **What:** `registry/D015_c1_live_v1.md`. C1 is "fade a pre-market gap bigger than the options-implied move". It
  is tested on fresh data, graded after the fact from Alpaca history with D014's own code (imported unchanged).
  No order is sent.
  - **Population:** every SH-M event (market-wide, ≥ $2B) of Season A + B whose reaction session opens after
    `bd67722`. The first is Thu Oct 15.
  - **The live implied move:** written once to `shadow/c1/im/<P>.json`, 15:25–15:55 ET on the session before the
    reaction. Contract: the first **monthly** expiry strictly after R, nearest strike, mid / spot. That is D014's
    instrument: 82% of its implied moves were third-Friday monthlies. The nearest expiry is a secondary.
    AAPL today: 6.6% monthly vs 2.5% weekly.
  - **H-C1:** mean y_30 < 0 in the C1 group, CR1 by R date, Student t with G − 1 df.
    - **Look 1:** Season A alone, from 2026-12-07, at p < 0.005.
    - **Final:** A + B pooled, at p < 0.045.
    - Power at VALIDATION's −0.9%: ~20% at look 1, ~85% final.
  - 🔴 **BLIND until a look:** `status` shows counts and coverage only. Never print a C1 mean, t or p before the
    look; looks are written once by code.
- **Guards:**
  - `check.py` verifies the 12-file `D015_implementation_v1.sha256`. That includes `shadow.py`, `sessions.py`,
    `common.py` and `s1_screen.py`, so **an edit to those now needs a dated line in that list**.
  - Captures are write-once. The code refuses to run on drift. Health is AMBER if the latest session has no C1
    capture.
- **Review:** Opus 5.5 said FREEZE WITH FIXES, 11 findings, all applied. Critical: the monthly expiry. Major:
  blinding; Student t; SEC failures can't block a date; the sample-defining code is now hash-checked. 171 tests
  pass.
- **Workflow:** `c1-shadow.yml`.
  - **Capture:** the routine pushes plus 5 cron backups; one job waits for the window.
  - **Grade:** 18:50 EDT plus a 21:20 backup.
  - **Probe:** manual, a pre-registration R only.
  - Today's capture was dispatched by hand at 12:09 ET (run 38595673105) and waits for 15:25.
- 🔴 **Watch:**
  - ✅ **First capture landed:** `shadow/c1/im/2026-10-14.json`, commit `441fd49` at 15:54 ET Oct 14 (run
    38595673105 green).
    - 10/12 implied moves, at 15:25 ET. HOMB `no_strike` (no puts listed) and WIT `no_quote`, after 30 retry passes.
    - Committed after `bd67722` and before Oct 15 09:27, so its events count.
  - Thu Oct 15 18:50 ET: the first grade, with `outcomes/shadow/seasonA/c1.json` counts only.
  - ✅ **Probe run 38595680182 (R = Oct 13, pre-registration, coverage only):**
    - 9 SH-M events, 45 requests, 0 failures. Opens and closes are auction prints. Pre-market prices are at
      09:25–09:26. Quotes 4/4, retail entry ok.
    - FBK is void `no_premarket`.
    - **All 9 timing `unverified`:** big banks and others file the 2.02 8-K at 10:28–11:32 ET, after the open; the
      wire release is ~07:00. So: no acceptance floor, kept and flagged. D014 had 1 such event in 3,536. The
      "timing verified" secondary will be thin among large financials.

**2026-10-14 (Wed) ~12:30 ET: the DPZ incident; D011 v3 FROZEN (paper closes); the window runner; exit alarms.**
- **The incident:** `ops/incidents/2026-10-13_DPZ_exit.md`. Expectations were committed before the outcome
  (`27c1109`).
  - DPZ's on-time exit would have been +$32 (natural) or +$328 (mid). The missed exit stands at about −$770
    (natural, Oct 14).
  - Three v1 closes at the indicative natural went unfilled. DPZ stays v1: it is retried until expiry on Oct 16,
    then settled at intrinsic.
- **D011 v3** (`registry/D011_paper_options_v3.md`, implementation v4; Opus review FREEZE WITH FIXES, all
  applied): every trade with a snapshot on or after 2026-10-15.
  - Long legs with a zero bid are dropped from the close.
  - The concession steps 0%, 5% … 25%.
  - A live close is cancelled after 2 minutes.
  - A single remaining leg goes as a simple order.
  - On expiry day the last close is sent at 15:10.
  - Dropped legs' value at expiry is recorded, with an alert if in the money.
  - **Report every D011 number twice: all trades, and v3 only.**
- **Ops:**
  - `paper-window.yml` (every 2 minutes, 14:27–15:56 ET; mornings while live). Tested live: it resent DPZ at
    11:07 ET.
  - `health.py` raises EXIT NOT FILLED as RED from 15:15 ET.
  - D011 exit audit v1 (`pipeline/paper_exit_audit.py`).
  - CLAUDE.md: the cron and indicative-feed facts.
- **D014 control days:** the cost at the open is mostly the open itself, not the print (`analysis/d014/CONTROL.md`).
- 🔴 **Watch Fri Oct 16:**
  - the first Season A gates (NOC, RTX, VICR), the first v3 trades
  - opening fill rate: v1's 15-minute open cancel now really happens
  - Mon Oct 19 onward: the first v3 closes. Do they fill at attempt 0, which tests the zero-bid hypothesis,
    or only after concessions, which tests the indicative-feed hypothesis?
- **Backlog from the research:**
  - re-grade paper fills against free OPRA bars after the fact
  - P&L at three cost levels
  - fill rate as an outcome
  - ✅ a positions-vs-ledger health check (done 2026-10-15, `health.py` `positions_check`)

## Cloud run log

The Actions AI step (`ops/actions_prompt.md`) appends one line per ET day here. Lines from 2026-09-20 to 2026-10-14
are in the history file. 🔴 Since 2026-10-15 the step has been refused ("organization has disabled Claude
subscription access for Claude Code"), so laptop sessions add the line by hand until it runs again.
- **2026-10-19 (Mon), by hand (laptop):** the AI step was refused again overnight. 35 dates confirmed (32 by code with four `find_dates` fixes, 3 by hand: FTAI, LOGI, JMKE), SMMT retired `unconfirmed`, GE re-checked (no company date). Nothing gated or frozen before 12:00 ET; ABT and PEGA gate from 14:30.
