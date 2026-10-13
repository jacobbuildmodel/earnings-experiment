# STATE — Earnings Experiment

**Season A live · D013 (Opus / Sonnet-replicate shadows) frozen · Max plan** · updated 2026-10-13 08:00 ET · roadmap `RESEARCH_PLAN.md` · lab notebook `JOURNAL.md` (newest entries first).

**2026-10-13 (Tue) ~10:45 ET — D014 FROZEN (`b5e081b`): the first hour after the print, on history.**
- Jacob's post-print idea, passed on from the DRIVE chat (no holdings in it; rule 9 intact). Spec
  `registry/D014_exploration_postprint_v1.md`, code `analysis/d014/`, implementation hashes
  `registry/D014_implementation_v1.sha256` (the workflow checks them). Opus pre-freeze review: FREEZE WITH
  FIXES, all applied.
- **Fetch running** in Actions (`d014.yml`, step `fetch`, run 38415697890, ~2.5 h, resumable). Then run it
  with step `analyse`. A month that failed is retried by a rerun of `fetch`.
- **Then:** read `analysis/d014/REPORT.md`. Any CANDIDATE → propose a live paper track in shares (Alpaca
  paper, automatic at the open), registered before its first reaction day. Otherwise it is negative
  knowledge for the charter.
- **Owed to the DRIVE chat via Jacob:** a short note on what D014 found, dead ends included.
- **D014 v2 FROZEN (`640ad4b`)** while v1's fetch ran, before any D014 number was seen. It covers the second
  DRIVE note's ideas: 5-day washout (≤ −8%) vs run-up (≥ +8%) before the print, and the sector ETF's week vs
  SPY, among gap-ups, at 5, 30 and 60 minutes (18 tests). Plus 13 bp small-ticket costs as a secondary.
  - **Order:** v1 `fetch` → v1 `analyse` → `d014-v2.yml` `fetch` → v2 `analyse`.
- **D014 v3 FROZEN** (retail entry, no new test). moomoo SG documents no opening-auction order (DRIVE
  checked moomoo's pages), so v1/v2 survivors are re-priced at the first minute's VWAP worsened by half the
  first post-open spread. Labels: executable (retail), executable at small tickets, or auction-only (that
  needs a broker with MOO, e.g. POEMS or IBKR: Jacob's call, no new money before paper results).
  - **Full order:** v1 analyse → v2 fetch + analyse → v3 fetch + analyse.
  - **Confirmed by Jacob's own app (screenshots, 2026-10-14 00:57 SGT):** his moomoo SG account offers
    Limit, Market and Market On Close; Stop, Limit-If-Touched, Market-If-Touched, Trailing Stop and
    Trailing Stop Limit; OCO; TWAP, VWAP and POV algos; Grid and Martingale. **There is no Market-On-Open or
    Limit-On-Open order.** v3's retail entry is his real entry. The VWAP algo sits near v3's plain-VWAP
    variant (b), which is descriptive only.
  - **DST:** 09:30 ET = 22:30 SGT from 2 Nov.
  - **Idea:** a verifiable customer→supplier map from 10-K "10% customer" sentences that name the customer
    (EDGAR full-text search). DRIVE may build one and pass the edges on as ideas. DRIVE's own hyperscaler
    basket is judgment, not disclosure; not used (rule 9 spirit).
  - **Customer → supplier read-across deferred:** there is no verifiable map. It goes to the backlog
    beside FRAMEWORK F4.

**2026-10-13 (Tue) ~08:30 ET — paper-options report frozen (D011 impl v3, `fc0ba41`); daily health check live.**
- `pipeline/paper_options_report.py`: D011 §8 + v2 §3. Run it: `python pipeline/paper_options_report.py seasonA
  --write`. Opus review: FREEZE after fixes. (It is v3: v2's name was already the long straddle's.)
- **Health check** (`pipeline/health.py`, `.github/workflows/health.yml`), code only, no AI:
  - GREEN, AMBER or RED goes to `ops/health/latest.md` (plus one file a day).
  - RED opens or comments on ONE GitHub issue, "Health RED", which GitHub e-mails to Jacob. It closes on
    GREEN.
  - Checks: check.py, missed snapshot windows, stage 1 not frozen, T2 missing or **at risk (< 14 h)**, D013
    shadows, Actions failures, paper halts and alerts, the SH-M capture.
  - Runs at 23:30, 03:30, 11:30, 13:30 and 21:15 UTC.
  - The first CI run passed (AMBER: the old 10-12 runup.yml failure, which ages out in 24 h).
- **New test:** every workflow YAML must parse. Two YAML/escaping slips today; GitHub fails such a file
  silently.
- 🔴 **Next session, start with `ops/health/latest.md`.**

**2026-10-13 (Tue) ~08:00 ET — Jacob upgraded to Max; D013 FROZEN (`3e5f47f`): T2 model shadows.**
- **Tracks**, on every T2 dossier, exactly D004 v4 stage 2 (`pipeline/t2_models.py`; `t2_stage2.py` is not
  edited):
  - **T2O** = Opus 5.5
  - **T2R** = a second Sonnet 5.5 run, T2's test–retest
  - **T2M** = the mean of T2, T2R and T2O when all three froze
  - SHADOW only. T2 is untouched.
- **Fable 5.1 refused** by the account through the isolated CLI: "requires usage credits" (paid extra usage).
  **A question for Jacob** whether to enable it; adding it would be D013 v2.
- **Guards:** T2 first, then a code budget (12 a run, 80 per 7 days per backend), a model check and a drift
  check (refuses if `t2_models.py` or `t2_stage2.py` change). `check.py` now WARNs (never FAILs) on D013
  shadow files.
- **Opus 5.5 review:** FREEZE WITH FIXES; all fixes applied. 88 repo tests pass.
- **Cloud routine `earnings-t2-models`** (`trig_017LGhgRnK6WZ3SwHFNK4Gyb`), cron `50 1,5,10,21 * * *` UTC,
  Haiku outer and Bash only. Its guard line is in CLAUDE.md. Test-fired 2026-10-13 11:46 UTC.
- 🔴 **The app still reports the plan as "Pro"** (get_usage, 2026-10-13). Jacob may need to restart or
  sign in again.
- **Watch Fri Oct 16 night:** the first Season A T2, then T2R and T2O. Check `manifest_t2r.json` and
  `manifest_t2o.json` commits, and `list_runs` of both routines.
- **To do:** `t2_models.py report seasonA` once events are graded (descriptive).

**2026-10-13 — D010 v2 (pre-registered `458cd3f`, results `a39a7df`, `analysis/d010/REPORT_v2.md`).**
- 🔴 **Data defect found:** yfinance's "unadjusted" Close is retroactively split- and spin-off-adjusted. 16 of
  1,249 events have spot and strike on different scales (KLAC, APH, WDC, ANET), so the as-frozen
  hold-to-expiry results are invalid. A disclosed, outcome-free fix drops strike / spot outside
  [0.8, 1.25]. v1 is barely affected (−3.22% → −3.27%), and the live pipeline is not.
- **Hold to expiry (fixed):**
  - short −0.80% (t −2.9); liquid −0.51% (n 160); at mid +1.03% all / −0.17% liquid
  - long −2.85% (t −9.3)
  - **The edge sits in the crush at the print.** Exit at the R close, liquid, at mid: +1.13% (review). Holding
    the median 15 days to expiry gives it back.
  - Expiry ≤ 7 d with liquid: only 12 events, insufficient. The live H-XT and SH-X structure cannot be priced
    on history.
- **IV spread (LR12) as a selector:** slope and T3−T1 are not significant.
  - Z4 (rich-call third, +1.98%, t 4.15) passes the frozen finding rule, but the average event rose
    +1.46% vs SPY in the reaction session (survivor sample, 2024–26). So it is mostly the premium, not the
    signal.
  - **Keep LR12 live. Do not make it Season B's best option signal.**
- **Gate 1 idea:** an SH-X variant exiting at the R close (D011's paper butterfly already does this) as a
  registered shadow statistic.

**2026-10-12 (Mon) 13:00 ET — both owed code paths written and registered (Jacob: "write now").**
- **H-XT (D012 impl v1, `8698ccf`):** `pipeline/shadow_xt.py` filters D009's graded SH-X rows to gates with
  both legs ≤ 10% spread and runs D009's mean_test as "H-XT". shadow.py is not edited. 4 tests.
- **SH-RU (D009 impl v3, `4f95f9f`)**, registered before the first X (~Nov 6). The 🔴 TO DO is done.
  - `pipeline/shadow_runup.py` (its own module; shadow.py untouched), plus a golden fixture
    `tests/fixtures/runup_*` with hand-derived E, D_exp, D_act, X, β and returns. 10 tests.
  - **Size gate:** the block bootstrap's size is 11–16% at a nominal 5%, which FAILS the 7% bar. So **KV
    fixed-b NW (lag 20) is primary**, with size 4.2–5.1%. Decided on synthetic data only.
  - Sonnet review said REGISTER WITH FIXES; all fixes applied. A failed price fetch is retried, and 10
    failed dates make it `price_unavailable`. The significance gate fails closed. The MDE uses the
    primary's se. The dependencies are pinned. One event per CIK. 8-K/A is ignored.
  - **Season A: 38 events with open windows (10 AI hardware), 276 `window_not_open`, 4 with no expected
    date.**
  - The registered `runup.yml` had a bash `-e` bug (no seasonB). It is disabled and kept as the record.
    **`runup-daily.yml` runs SH-RU** (addendum `D009_implementation_v3_addendum.md`, frozen). The first CI
    run was clean.
- 81 repo tests pass.

**2026-10-12 (Mon) 12:40 ET — D010 reviewed and merged; D012 (H-XT) frozen (`9bef05d`).**
- **D010 verified:** 200 sampled events re-derived from `raw/` (0 mismatches); a deterministic rerun.
  Review: `analysis/d010/REVIEW_2026-10-12.md`.
- **Result, all 1,249 valid events (2025–26-heavy; 2019 has no calendar rows):** neither side pays after
  costs. Short −3.22% (t −19), long −4.03% (t −20), short at mid +0.40% (t 2.95). No finding.
- **But the costs are illiquid names:** the median leg spread is 21% (P) and 31% (Q) of the option price.
  Post-hoc, on the gate's own ≤ 10% spread rule (n 168, 114 dates): short at mid **+1.13% (t 3.44)**,
  short after both spreads +0.05%, **long −2.20% (t −6.4)**.
- **D012 v1 FROZEN: H-XT** = SH-X on gates with both legs `rel_spread` ≤ 0.10. Confirmatory, own family
  m = 1, verdict on A + B pooled.
  - ✅ The H-XT code is registered (`D012_implementation_v1.sha256`, 2026-10-12).
- **Next automatic events:**
  - Tue Oct 13: DPZ butterfly exit from 14:30 ET.
  - Fri Oct 16: first 3 Season A gates, and the first PX-L long straddles.

**2026-10-09 (Fri) 20:50 ET — Actions was blocked; the repo is now PUBLIC. D011 v2 (long straddle) frozen.**
- 🔴 **From 16:03 ET Fri, GitHub refused to start ANY job**: "recent account payments have failed or your
  spending limit needs to be increased". The private repo had used its 2,000 free minutes for October
  (~2,500 by wall time).
  - S2 window: 1,338 min. Its early fires WAIT up to ~3.5 h for the window, billed throughout.
  - D007 exploration: 762 min (one-off). Season screen: 196.
  - Lost: Fri evening grade, shadow, housekeeping and paper runs only. Nothing frozen was lost; DPZ had
    frozen INELIGIBLE at 14:3x ET.
- **Jacob chose: make the repo public** (offered: a $15/mo cap, or cut waste and wait for the reset).
  - Public repos get Actions free on standard runners.
  - Scanned the full history first: no keys or tokens, no holdings or account data. What is public: the
    code, the record, and Jacob's name and email in commits. Secrets stay secret. No workflow has a
    pull_request trigger.
  - `gh repo edit --visibility public` at 20:39 ET. Every re-run passed (grade, shadow, paper, paper
    options); S2 housekeeping re-dispatched.
  - If it is ever made private again, the S2 waiting design will exhaust the minutes again. Move the gate
    trigger to the routine pushes only.
- ✅ **D011 v1, first trade: DPZ** (gate INELIGIBLE; v1 trades any status).
  - Butterfly 310 / wings 260–360 Oct 16, n = 1. Filled −17.60 vs natural −17.56 (4¢ better).
  - **`convention_verified`**: the mleg sign is right, so the 3-trade cap is lifted.
  - Exit Tue Oct 13 from 14:30 ET.
- **D011 v2 FROZEN (`be337fd`): the LONG straddle on a SECOND paper account.**
  - `pipeline/paper_long.py` runs v1's frozen code with structure L, its own ledger
    `paper/long_ledger.json` and workflow `paper-long.yml`, paired event by event with v1.
  - It counts from gates snapshotting 2026-10-12 on.
  - ✅ **LIVE since 21:27 ET Fri.** Jacob added the `APCA_L_*` secrets. The second account is ACTIVE, options
    level 3, equity $100,000, separate from the first. A first sync ran clean and the ledger is created.
    The first eligible gates are Fri Oct 16 (3 names).
  - No second-model review: it is a 60-line wrapper over reviewed code, with 5 tests. Disclosed in JOURNAL.

**2026-10-09 (Fri) 11:45 ET — D011 FROZEN: paper straddles on Alpaca (`f84849d`). Details in JOURNAL.**
- **Jacob asked for paper straddles.** Alpaca paper refuses naked short calls, so the traded form is the
  **short iron butterfly** (SH-X + wings at ±2 straddle prices).
  - Opened on the snapshot session right after the gate; closed on the reaction session from 14:30 ET.
  - Every live-season gate SH-X takes, any gate status. Descriptive; no new test.
  - Ledger `paper/options_ledger.json`; workflow `paper-options.yml` (every 10 min 18–20 UTC, after each
    S2-window run, 14:40/15:40 UTC).
- **The long straddle is NOT traded:** one account nets the same contracts and refuses the second order.
  **Question for Jacob:** open a second Alpaca paper account (free) for the long side? Not a blocker.
- **Sign guard:** only 3 trades get orders until one real fill proves the mleg limit-price sign. A bad
  fill sets `halt` in the ledger: new opens stop, exits continue, the run goes red.
- 🔴 **Watch today:**
  - DPZ (BMO Oct 13) gates 14:30 ET. Its butterfly should open by ~15:55 ET.
  - Check `paper/options_ledger.json` for `convention_verified`, and for any `alerts` or `halt`.
  - Exit Tue Oct 13 from 14:30 ET.
- **TO DO before the 10th round trip:** `paper_options.py report` (D011 §8), registered as impl v2.
- The probes (`paper.py options-probe`, `pipeline/paper_options_probe.py`) stay. They only run by hand.

**2026-10-02 afternoon** (Jacob: "too passive, not hungry enough"). Details in JOURNAL.
- **The earlier "Phase 1 done" was false.** The T0-wide shadow, the straddle shadow and the H-S0 test
  were not in code. They are now.
- **D009 frozen** (`registry/D009_shadow_tracks_v1.md`, `pipeline/shadow.py`, `.github/workflows/shadow.yml`):
  - **SH-W**, T0-wide: every company-confirmed allowlist date. Descriptive.
  - **SH-M**, market-wide: ≥ $2B, any industry, ~1,300 events a season. Dated by a write-once daily
    Nasdaq capture in `shadow/calendar/`.
  - **SH-X**: the exact short straddle from the gate's quotes.
  - Tests: H-M, H-X, H-VOL, Holm m = 3; verdict on A+B pooled.
  - The first capture is 2026-10-02.
  - Outcomes go to `outcomes/shadow/` (fenced from T2).
- **Power finding:** entry sessions bind, not events. The gated track's expected t is ~0.8 a season and
  ~1.1 after A+B, so **D008's Gate 2 is very likely underpowered.** CHARTER I12: decide at Gate 1.
- **H-S0 now in `report.py`** (D005 implementation v3, registered together with the unregistered 09-23
  grade.py change).
- **🔴 The token's weekly limit was exhausted on 2026-10-02.** It is shared with Jacob's chats; every model
  was refused, "resets 12am (UTC)".
  - The `t2` job now retries a refused decision on `ANTHROPIC_API_KEY` if that secret exists. It does
    not exist yet: **a question for Jacob.**
  - `max-parallel` 5 → 10.
  - A Haiku 10-way concurrency test runs from cron at 01:15 UTC Oct 3. **Read its results:**
    `gh run list --workflow t2-loadtest.yml`.
  - The 23:00 UTC housekeeping AI step will likely fail tonight; code steps still run.
- **Independent review** (Sonnet, read-only): no leak; 16 fixes applied before the freeze. Still open:
  - the fallback path has never run, so test it once a key exists
  - a pooled A+B report for D009 must be written before Season B's end
  - SH-X dependence between overlapping straddles is understated (disclosed)

**2026-10-08 20:40 ET — D010 running in the cloud; cloud runs share the Pro plan's limits.**
- **D010 v1 frozen** (`4f80f9a`) before any price was pulled: the earnings straddle on 2019–2026
  history, 22 tests.
  - It runs as cloud routine `earnings-d010-backtest` (`trig_01DvnwRbtgYR6Y2kjPQzTdjx`, session
    `cse_01XFhj9Lk7PHfY5fWA5t4m61`).
  - It cloned DoltHub `options` (8.2 GB) and `earnings` (1.8 GB) with `dolt clone`, and is computing.
  - Output goes to branch `claude/d010-backtest` → `analysis/d010/REPORT.md`, `results.json`. **Review it
    on the laptop before merging** (check the code against D010 §3–§5, determinism, void counts).
- 🔴 **Cloud sessions use the SAME Pro plan limits as the laptop chats**, not a separate $100 pool. The
  backtest was stopped at 14:20 UTC by "session limit, resets 4:10pm (UTC)", the laptop chat's window.
  It resumed at 00:37 UTC when Jacob typed "Try again" in it.
  - Weekly was 66% used at 00:40 UTC Oct 9, resetting **Oct 12 06:00 UTC**.
  - T2 for the Oct 9 snapshots (deadline Oct 12 09:15 ET) is covered even if the week runs out: the
    05:20 and 10:20 UTC cloud runs on Oct 12 fall after the reset, and the token fallback runs from
    11:00 UTC (its week resets Oct 10).
  - **Keep laptop chats short until Oct 12.**
- **Season A screen done** (`93f106d`): 318 names PENDING. First snapshots Fri Oct 9, 14:30 ET.

**2026-10-08 (Thu) 09:40 ET — T2 now runs free on Jacob's cloud allowance. No API key (Jacob: no new money
until results).**
- **Cloud routine `earnings-t2-cloud`** (`trig_01H4HJJ2uPLZXUwfi7q5fXr3`, env `env_01JfLgj93yjfX4k198b7durh`):
  - cron `20 1,5,10,21 * * *` UTC; outer model Haiku, Bash only
  - runs `T2_ALLOW_LOCAL=1 python3 pipeline/t2_stage2.py run --backend claude`, the same code (D004 v4 and
    the H-T2C protocol are unchanged)
- **Probed 10-08:** the real code on a scratch NKE dossier passed isolation (no tools, no MCP, 1 turn).
  - It gave the Actions answer (NO_BUY 0.50) for $0.09.
  - GitHub, PyPI and the TSAs (DigiCert, Sectigo) are reachable; FreeTSA 403 and Nasdaq time out (not
    needed).
  - A no-op run: check PASS in the cloud, 0 waiting.
  - CLAUDE.md now has a guard line for this routine.
- **`t2-queue.yml`:** Gemini (T2G) every pass; the subscription token decides T2 only from 11:00 UTC, as a
  last resort, so the two never race. New dated hash line.
- **The API-key fallback stays wired and inert.**
- **Which allowance pays is unknown:** the $100 cloud credit, or the Pro plan of the laptop chats.
  - The Pro plan was 38% → 56% weekly from 10-07 to 10-08, mostly this long laptop chat.
  - **Check `get_usage` after the first real batch** (Oct 9 night). Keep laptop chats short in season.
- **Watch Fri Oct 9:** the gate at 14:30 ET, then `earnings-t2-cloud` at 21:20 UTC. Check `list_runs` and
  the `manifest_t2.json` commits.
- **Results Jacob can see before funding:** live samples are tiny (pilot SH-W 6 graded, 0 wins, −4.5% net;
  SH-X 2 graded, +5.6%). The fastest large-sample answer is D010 on DoltHub's 2019–2026 options history,
  pre-registered first. **Cloud sessions are blocked from DoltHub, SEC, Nasdaq and Yahoo unless Jacob
  sets the cloud environment's Network access to Full.**

**2026-10-07 (Wed) — laptop session: the pilot ended, and four pre-Season-A fixes. Details in JOURNAL.**
- **Pilot, final two events.**
  - LEVI: INELIGIBLE `wide_spread` at its 14:31 ET gate (a rule outcome).
  - 🔴 **APLD: PASS, but T2 MISSING.** All 10 attempts were refused with "You've hit your weekly limit ·
    resets Oct 10, 12am (UTC)". It froze at 21:55 ET with T0 and T1 intact.
  - The housekeeping AI was refused too, so no PENDING re-checks ran. Nothing was PENDING in the pilot.
- 🔴 **Capacity, the binding risk for Season A.**
  - The account behind `CLAUDE_CODE_OAUTH_TOKEN` ran out of its WEEKLY limit on ~$5.5 of logged work:
    PENG's Opus T2 ≈ $3.3 plus 3 housekeeping runs ≈ $2.0, and small tests.
  - It is **not** the account of the laptop chats: that one is Pro, 38% used, resetting Oct 12.
  - The cloud routines kept firing after the limit, so they draw on another allowance.
  - **Season A needs:** ~$0.085 a T2 decision (×~150–300 PASS events) plus ~$0.66 a housekeeping run.
    The Nov 3–5 peak alone (~165 prints) cannot fit this token's week.
  - **Fix wired, inert** (`2dbde27`). If the GitHub secret `ANTHROPIC_API_KEY` exists:
    - `t2-queue.yml` re-runs what the subscription left undecided on that key
    - a refused housekeeping run is repeated once on it
    - Same model, flags, prompt and code, so the H-T2C protocol is unchanged. New dated hash line for
      `t2-queue.yml`.
  - **Decision for Jacob:** create the key with a monthly spend limit (~$50). The estimate is ~$20–50 a
    season, against the $450–950 quoted for agentic Opus on 10-02.
- ✅ **find_dates v3 (`1a0ef26`):** the Nasdaq copy of the company's own wire release is now a fallback
  company source.
  - Measured on the 329 preview names: IR feeds readable for 162 (49%) → **326 (99%)** with the fallback.
  - 32 more names already give a confirmable date and session.
  - Wire-dateline pages only, with the header cut. It agrees with the IR feed on all 4 overlaps, and a
    second source must still agree.
  - Tests: `tests/test_find_dates_nasdaq.py`.
- ✅ **Busy-day rehearsal** (scratch clone, 40 real names, 4 workers): **9.0 min** wall, 0 crashes, 40/40
  dossiers built (1 missing MD&A heading), no SEC refusals.
  - Median per event: gate 11 s, factors 14 s, dossier 24.5 s (max 87 s).
  - A ~55-event day takes ~12–15 min of the 80-min window.
  - (38 gates said `no_quote` only because they ran at 09:37 ET, before quotes fill; real gates run
    14:30–15:50.)
  - The first run once lost LRCX's gate under load; it did not recur in 40 more. **Watch** for a PASS-day
    capture with no `gate.json`.
- ✅ **D009 v3 FROZEN (`513cd9b`): SH-RU, the 20-session run-up into the print.**
  - Candidate relayed by Jacob from the DRIVE chat (AI-hardware +3.4% vs SPY, t 2.7; disclosed, not
    evidence), plus LR01.
  - Beta-adjusted, with a pre-window shrunk β; calendar-time portfolio with a circular block bootstrap
    (block 20); Holm m = 2 (H-RU, H-RU-AIH); verdict on A + B pooled.
  - Only windows with E after this commit count, so only Season A prints from about Nov 9.
  - Sonnet review: FREEZE WITH FIXES, all applied.
  - **"Insufficient" is the stated expected result for AI hardware.**
  - 🔴 **TO DO before the first exit (~Nov 9):** write `shadow.py runup`, a golden fixture and the
    size gate (≤ 7% at 30/45/60 events). Register them in `D009_implementation_v3.sha256`, or the
    completed windows become descriptive only.
- **Jacob's other two DRIVE points:**
  - DoltHub options: already planned as D010. Pre-register it, then run it from the laptop during
    Season A (not a blocker).
  - de Silva, Smith & So, *Review of Finance* 2025: verified bibliographically. The 5–14% loss figure
    is from secondary summaries only (V2). It supports H-X's side; no change.
- `s1-screen.yml`'s new push trigger was verified: the 18:45 and 19:45 UTC pushes on 10-06 ran `when`
  and skipped cleanly. On Oct 8 they will start the screen.

**2026-10-06 07:45 ET (Tue) — laptop check.** `check.py` PASS (1 warning: the untracked
`analysis/history/legs_exploratory.json`, written 09-30, referenced by nothing; left uncommitted).
- ✅ **The `T2 v4 smoke test` passed on the Actions runner** (run 37400449552; it fired 01:41 UTC, ~4 h 40 m
  late). On NKE: the Sonnet stage-2 call ran isolated (`tools: []`, `mcp_servers: []`, 1 turn, no web use),
  leak probe "I don't know", $0.085 equivalent. Gemini `gemini-3.8-flash` also answered this time (no 503).
  NKE's dossier had no headline dated ≥ 15 min before the snapshot; it was recorded as missing, as designed.
- **Today: LEVI and APLD, snapshot 14:30–15:50 ET.** These are the pilot's last two events. Both run agentic
  Opus under D004 v1, in parallel, on the shared token, so the second may be refused by the 5-hour limit.
  **That is not fatal.** The pilot T2 deadline is the entry open (Oct 7 09:30 ET). The evening
  housekeeping run, which usually arrives 01:00–02:40 UTC after the limit has reset, plans T2 again and
  runs it before `finalize --last-chance`. T2 MISSING only follows if that retry is refused too.
- **Season A's first day: the "BMO Oct 12" hole is empty.** Oct 12 is Columbus Day, and the Nasdaq
  calendar lists one reporter that day (RMCF, $8M). No rule change is needed.
- 🔴→✅ **The real gap, fixed 08:30 ET: dates confirmed too late.** Code confirmed company dates only in
  the evening run (`find_dates apply`), and refused any date whose snapshot session was that same day.
  Season A's screen slot runs 16:00 ET Oct 8 → 09:30 ET Oct 9. If the screen finished after Oct 8's
  evening run, **no Oct 9 snapshot event (AMC Oct 12, BMO Oct 13) could be confirmed in time**, so the
  first day would be lost. The same was true all season for a company that announced its date late.
  - **`find_dates` v2 adds `--urgent`:** names dated within two sessions, run 10:00–12:00 ET, stopping
    5 min before the window opens. A date found then counts for today's gate. The evening run is unchanged.
  - **`s2-window.yml`:** the precheck wakes a morning run when an urgent PENDING name exists, and a
    code-only step runs the pass before `due.py wait`, with `continue-on-error`.
  - Tested: `tests/test_find_dates_urgent.py` (4 cases), all 39 tests pass, and the pilot is a no-op
    (nothing written). No rule and no hashed file was touched (`find_dates.py` and `s2-window.yml` are in
    no hash list).
  - **Watch Fri Oct 9 10:45 ET:** the first live urgent pass on Season A.

**✅ 2026-10-06 ~08:10 ET — D005 v3 FROZEN: H-T2C, T2's confidence tested on Seasons A + B pooled**
(`registry/D005_evaluation_v3.md` + `D005_confirmatory_pooled_AB.json`). It is frozen before any Season A
data exist.
- **Why:** v1 §7 pre-commits to pooling via a new version, and the confidence test is the one that keeps
  its power (~40% a season). Registered for Season B alone, it would discard Season A's decisions.
- **The rule:**
  - a family of one, at one-sided α 0.05
  - `wild_p_k` with season intercepts kept
  - per-season minimums of 10 events and 5 sessions
  - a DEGENERATE rule if SD(confidence) < 0.05
  - a `no_price` VOID sensitivity run
  - "same protocol" means model, system prompt, `dossier.py` and `t2_stage2.py` hashes, and call
    parameters
  - a change keeps the old protocol running as a shadow; if no track can run in Season B, H-T2C is
    UNTESTABLE and is never tested on Season A alone
- **Review:** Sonnet said FREEZE WITH FIXES. Its 2 critical and 8 other findings are all applied.
- 🔴 **This binds T2 for Season B.** Changing `dossier.py` or `t2_stage2.py`, even as a bug fix, ends
  pooling and obliges the v4 shadow. The Season B confirmatory file must NOT register `T2_confidence`.
- **To do before Season B's screen:** write the pooled run, test it on synthetic data, review it, and
  register its hash.
- **Also today:** `s1-screen.yml` now also starts on the cloud routine's 18:45 and 19:45 UTC pushes on
  Oct 8 and waits for the slot (`acbd9f9`). **Check at 10:45 ET today** that the routine's push ran
  s1-screen's `when` job and skipped cleanly.

**✅ 2026-10-05 ~10:45 ET — D004 v4 FROZEN: the free capacity fix** (`registry/D004_decision_protocol_v4.md`).
Jacob: no paid API for now.
- **Stage 1, at the snapshot:** code builds `dossier.json`:
  - the EX-99.1 earnings release
  - the MD&A, correct on 18/18 filings
  - 8-Ks with their EX-99.1
  - Yahoo RSS headlines at least 15 min before the snapshot
  - the gate, factors and base rates

  Every item is timestamped before `captured_et`, and the event is frozen at once (T0, T1, dossier).
- **Stage 2:** a leak-probe call with nothing in context, then ONE isolated decision call
  (`claude-sonnet-5-5`; `--safe-mode --tools ""`, with a no-tools/no-MCP check). Code sets BUY ⇔ > 0.50.
  - `t2.json` + `manifest_t2.json` + RFC 3161 tokens, frozen before entry open − 15 min.
  - The queue is `.github/workflows/t2-queue.yml`, every 30 min overnight.
  - About $0.08–0.10 a decision, against $3.14 for the agentic run.
- **The method is hashed:** `registry/D004_implementation_v4.sha256` lists `dossier.py`, `t2_stage2.py`,
  `freeze.py`, `due.py`, `grade.py` and `t2-queue.yml`. **check.py FAILS on any edit without a new dated
  line.** Remember this when touching those files.
- **Shadows:**
  - **T2G:** Gemini `gemini-3.8-flash`, free. `GEMINI_API_KEY` was set by Jacob on 10-05. The key
    works, but the free tier answered **503 "high demand"** all morning, so it retries each run.
  - **T2E:** the mean of T2 and T2G.
- **Independent review** (Sonnet): no look-ahead. Its findings 1–15 are fixed or disclosed. Rehearsed
  end to end twice in scratch clones: stage 1 and 2 BLIND, 8 tokens, check PASS, the laptop guard
  refuses. **The pilot path is unchanged:** PENG, LEVI and APLD run agentic Opus under v1.
- **Housekeeping AI moved to Sonnet**, to save allowance.
- **Watch:**
  1. `T2 v4 smoke test` at 17:00 ET today (21:00 UTC): the stage-2 call on the Actions runner itself,
     with the npm CLI, the OAuth token and the flags. Read its log.
  2. The first real Season A snapshot (BMO Oct 12 → snapshot Thu Oct 8): the stage-1 freeze, then
     `t2-queue` decisions overnight.
  3. A known gap: `paper.py` records T2 as None for stage-2 events (the paper ledger trades S0, so it
     is cosmetic).

**🔴 2026-10-05 07:40 ET — the weekend Haiku load test (Sat 06:28 UTC):**
- 8 of 10 jobs were refused: "You've hit your **session** limit · resets 6:30am (UTC)". 2 ran: ~$0.15
  and ~70 s each.
- That 5-hour window began at ~01:30 UTC, when Friday's housekeeping run (one Opus run, 41 tool calls)
  started. **One Opus run nearly used up a whole 5-hour session allowance.**
- The account behind `CLAUDE_CODE_OAUTH_TOKEN` can therefore carry about 1–2 Opus T2 decisions per
  5 hours. **Season A's ~50 a day on peak days are impossible on it**, and `max-parallel` does not matter.
- Before the first Season A snapshot (~Oct 9), one of these must happen:
  - an `ANTHROPIC_API_KEY` secret (the fallback is wired)
  - a token from an account with much larger limits
- The pilot (1–2 events a day) is fine.

**2026-10-02 late — the cloud session (PR #1, $100 cloud credit, expires 11-05) merged; D009 v2 frozen.**
- **Cloud work, merged:**
  - `shadow.py report-pooled` (D009 §5's A+B verdict; tests: ~5% size, 93% power at +2%)
  - `pipeline/gate1.py` (the Gate 1 report builder)
  - `tests/`: 30 tests, all pass on the laptop
- **D009 v2 frozen** (`registry/D009_shadow_tracks_v2.md`):
  - **SH-MO**, the off-season market-wide shadow. First window: Nov 23 → Jan 8, screened Nov 18 from the
    Nasdaq screener (probed: 7,073 listings).
  - **H-MY**: its own test over every market-wide event from clock **2026-10-05**.
  - About +24–40% information a year. Not a fix for Gate 1 or Gate 2.
  - It runs from the `shadow.yml` evening step `shadow_offseason.py due`.
- **Cloud environment:** SEC, Nasdaq, NYSE, Yahoo and DoltHub are still blocked (`ops/cloud_probe_2026-10.md`).
  Jacob can set **Network access: Full** in the cloud environment settings; a cloud session can then do
  data work. Brief: `ops/cloud_session_prompt.md`.
- **The pilot "fence breach"** (housekeeping 2026-09-30) is a **false positive**: a STATE.md edit whose text
  named the T1 rule. It was not a T2 run, and no T1 file was read. Cleared.
- **Not done** (network): D010, exploration batch 2. Pre-register it before any data is pulled.

**Earlier, 10-02:**
- **D007: no candidates.** 20 signals on 2,771 prints; none beats buying everything. The likely graduate
  is S0, the premium harvest (D008, H-S0).
- **NKE: −8.2%.** T0 and T2 (BUY 0.52) both lose. Paper −$475 booked as **simulated**: Alpaca paper does
  not fill `opg` orders, so paper now queues DAY market orders.
- **Parallel-gate load test passed:** 16 events in 48 s.
- **Triggers:** cloud routines `earnings-s2-trigger` (gate) and `earnings-paper-trigger` (paper); the
  laptop task is a backup. The routines run on the same weekly-limited account.

**Next:**
- Sat Oct 3: read the Haiku load test. Confirm `shadow.yml` ran its first evening grade (22:40 UTC Fri) and
  that the capture/grade commits look right.
- Mon Oct 5 PENG: the first real queued paper fill (`paper/ledger.json`), and the first live shadow
  capture by Actions (10:45 ET fire).
- Tue Oct 6 LEVI + APLD: the first two-event day; check both `t2` jobs and both freezes.
- Oct 8–9 Season A screen. Once its `raw/yfinance_market.json` is committed, check the SH-M universe:
  `python pipeline/shadow.py grade seasonA --no-fetch`.
- During Season A: daily health checks; the shadow report `python pipeline/shadow.py report seasonA`.

**Waiting on Jacob:**
1. ~~An Anthropic API key~~ **declined 2026-10-08 (no new money until results); T2 runs on the cloud routine instead.** Was: an Anthropic API key with a monthly spend limit (~$50), as GitHub secret `ANTHROPIC_API_KEY`. Under D004 v4
   it costs ~$0.085 per T2 decision → ~$20–50 a season. The fallback is wired and inert until it exists (2026-10-07).
2. The real-money sleeve and loss limit (D008 v2), before Gate 2.

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
    that day's close → AMC Oct 7, snapshot Oct 6. **AEHR never resolved — retired INELIGIBLE
    `unconfirmed` by the 2026-10-02 housekeeping run**, after both snapshot sessions its Oct 5 calendar
    date allowed (Oct 1 BMO, Oct 2 AMC) closed with no company announcement, and with no in-window
    calendar row left. Nothing is PENDING; the pilot universe is final at 12 events.
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

- **2026-09-29 14:36 ET — housekeeping (this run, the second fire of the same ET day; the first was the
  14:31–14:35 gate-and-housekeeping run above).** `check.py` PASS. `due.py t2-list` empty — MU is frozen
  INELIGIBLE and no other event has a snapshot session of 2026-09-29, so nothing was awaiting T2, no
  decision was written, and this step gated nothing and froze nothing. Today's four commits are all from
  the earlier run: `6da4a56` (Freeze MU) · `ed76268` (housekeeping) · `6b5feb1` (status sync) · `ba0e8b3`
  (AI tool log). Not a Friday, so no mid-season screen.
  - **AEHR stays PENDING** — re-checked again two minutes after the last re-check, and nothing had moved.
    aehr.com/newsroom (HTTP 200) newest item still 2026-09-28, the CEO Investor Summit release — an
    investor conference, not an earnings date; newest Financial News item still the 2026-07-14 FY26 Q4
    results release. SEC EDGAR (CIK 0001040470) as the second company source: newest filings ARS
    2026-09-10 and DEF 14A 2026-09-09, annual-meeting material, **no 8-K carrying a date**. yfinance
    unchanged at 2026-11-02 15:00 ET, intraday and outside the window. Nasdaq unchanged at 2026-10-05
    `time-not-supplied` (fiscal quarter ending Aug/2026), and AEHR is on no Oct 1, Oct 6 or Oct 7 row.
    Earliest possible snapshot session **2026-10-01** — one housekeeping run left before code marks it
    INELIGIBLE `unconfirmed`. Expect that.
  - Two fires per ET day means the second one duplicates the first one's re-check. That is cheap, but the
    re-check list is now mostly repetition; worth collapsing to one PENDING re-check per ET day when the
    workflow is next edited from a laptop session.

- **2026-09-29 21:45 ET — housekeeping (this run, the third fire of the same ET day).** The 23:00 UTC fire
  arrived **2 h 45 min late** (19:00 ET due, 21:45 ET started) — the same lateness measured every day since
  09-21. Nothing was due: `due.py t2-list` empty, no event has a snapshot session of 2026-09-29 still open
  (MU was gated and frozen at 14:31 ET by the first fire), so this step gated nothing, froze nothing and
  wrote no decision. `find events -name gate.json` returns **1** — MU is still the only gate in the pilot's
  history. Not a Friday, so no mid-season screen. Today's later commits are all from the laptop session and
  from code, none from this step: `ef0d148` grade run (20:40 ET) · `e2f0f12` the `season-a-readiness` merge
  (20:41) · `e3f0d7a` **D003 v4** (20:42) · `c2853d6` `actions: read` (20:42) · `6d3cff5` S2 also starts on
  a push to `claude/s2-trigger` (20:44) · `4131ed7` code's `find_dates apply`, **0 confirmed** (21:44).
  - 🔴 **`check.py` cannot be used as the health check inside the fenced AI checkout — it reports FAIL.**
    Run here it says `frozen registry file(s) changed: ['D006_history_study_v1.md (missing)',
    'T1_rule_v0.json (missing)']`. Both are *deliberately* absent: `.git/info/sparse-checkout` excludes
    `registry/T1_rule_v0.json`, `registry/D006_history_study_v1.md`, `registry/D006_implementation_v1.sha256`,
    `registry/README.md`, `analysis/history/`, `outcomes/` and `archive/` (D004 v3's T1 fence). `check.py`
    cannot tell "fenced out" from "deleted", so it will FAIL on every T2 and housekeeping run from now on.
    **The record is not damaged** — code ran the real health check in the full checkout before this step, and
    `git ls-files` confirms all three files are still tracked. Fix from a laptop session: make `check.py`
    skip a frozen file that sparse-checkout excludes (and say so), or stop the AI step running it at all.
  - 🔴 **`actions: read` did not take effect on this run.** `gh run list` still returns **HTTP 403 Resource
    not accessible by integration**, although `c2853d6` added the grant to the `s2` job three hours earlier.
    The token was minted from the workflow definition in force when the run started, so the grant should
    apply on the next run — re-test then. Until it does, the 09-28-style "did the fire arrive or did the code
    crash" question still cannot be answered from inside the runner.
  - **AEHR stays PENDING, now two days late against its own pattern.** Code went first and recorded
    `no_feed` — AEHR has no Q4-style IR feed and `investors.aehr.com` does not resolve — so this re-check is
    the AI's, as on every previous day. `www.aehr.com/newsroom` (HTTP 200): newest item still 2026-09-28,
    the CEO Investor Summit release — an investor conference, **not** an earnings date; the newest Financial
    News item is still the 2026-07-14 FY26 Q4 results release and the newest "to Announce … Financial
    Results" item is still 2026-07-07. SEC EDGAR (CIK 0001040470) as the second company source: newest
    filings ARS 2026-09-10 and DEF 14A 2026-09-09, annual-meeting material, then Forms 4/144 — **no 8-K
    carrying a date**. yfinance unchanged at 2026-11-02 15:00 ET, intraday and outside the window; Nasdaq
    unchanged at 2026-10-05 `time-not-supplied` (fiscalQuarterEnding Aug/2026, epsForecast $0.05) and absent
    from the Oct 1, Oct 2, Oct 6 and Oct 7 rows. Its ~7-day lead implied an announcement on 2026-09-28.
    Earliest possible snapshot session **2026-10-01** — **one housekeeping run left** (Wed 2026-09-30) before
    code marks it INELIGIBLE `unconfirmed`. Expect that.
  - **NKE is tomorrow (snapshot Wed Sep 30, AMC Oct 1)** — the first event that can reach a T2 decision, and
    the first live test of the per-event `t2` job and the laptop dispatch trigger.

- **2026-09-30 21:42 ET (Wed) — housekeeping (this run, Actions run 36802227081, `schedule`).** The 23:00 UTC
  fire arrived **2 h 42 min late** again (19:00 ET due, 21:42 ET started). `due.py t2-list` **empty** — the
  workflow's prompt names no event awaiting T2, so this step wrote no `decision.json`, gated nothing and froze
  nothing. Not a Friday, so no mid-season screen.
  - **What code did on this ET day — the first complete chain:** `075ddb7` **14:31 ET** `Capture NKE
    2026-10-01: S2 gate PASS and factor snapshot - awaiting T2` → the per-event `t2` job (run 36731470987)
    decided it → `a2f6a47` **14:40 ET** `Freeze NKE 2026-10-01 (PASS)`, manifest `frozen_et`
    2026-09-30T14:40:04 ET against `entry_open_et` 2026-10-01T09:30 ET → **BLIND**, with both RFC 3161 tokens
    (`manifest.tsr_digicert`, `manifest.tsr_freetsa`) and six hashed files. Then `4eb0b96` the AI tool log
    (49 calls, 0 fence breaches) and `868f8a1` the status sync — NKE now reads `FROZEN`. Code also ran the
    nightly grade job (`94e6491`, 20:41 ET) and two paper-ledger runs (`3fe0fb8` 10:41 ET, `6e1f35e`
    20:17 ET); no outcome figure is read or written here (rule 4). `find_dates apply` ran just before this
    step (`e8ab482`, 21:41 ET) and confirmed **0** dates. `find events -name gate.json` now returns **2**
    (MU, NKE).
  - **AEHR stays PENDING — and this was the last housekeeping run before its deadline.** Code went first and
    recorded `no_feed` (`find_dates probe AEHR`, 21:42 ET: no Q4-style IR feed, `investors.aehr.com` does not
    resolve), so the re-check is the AI's, as on every previous day. `www.aehr.com/newsroom` (HTTP 200):
    newest item still 2026-09-28, the CEO Investor Summit release — an investor conference, **not** an
    earnings date; newest Financial News item still the 2026-07-14 FY26 Q4 results release, newest "to
    Announce … Financial Results" item still 2026-07-07. **`www.aehr.com/events/` read for the first time**
    (HTTP 200, redirected from `/newsroom/category/events/`): trade-show and conference listings only, no
    earnings call. SEC EDGAR (CIK 0001040470) as the second company source: newest filings ARS 2026-09-10 and
    DEF 14A 2026-09-09, then Forms 4/144 — **no 8-K carrying a date**. Second sources unchanged: yfinance
    2026-11-02 15:00 ET, intraday and outside the window; Nasdaq 2026-10-05 `time-not-supplied`
    (fiscalQuarterEnding Aug/2026, epsForecast $0.05), and AEHR is on no Oct 1 or Oct 2 row. Its ~7-day lead
    implied an announcement on 2026-09-28; it is two days late. **Earliest possible snapshot session is
    2026-10-01 (tomorrow)**, so once that window closes code marks AEHR INELIGIBLE `unconfirmed`. Expect that,
    and expect the pilot to end with no AEHR event.
  - 🔴 **`actions: read` still does not reach the AI step — re-tested as the 09-29 entry asked, and it failed.**
    `gh run list` and a raw `curl` on `/actions/runs` both return **HTTP 403**, with
    `x-accepted-github-permissions: actions=read`. The grant is correctly declared on the `s2` job
    (`.github/workflows/s2-window.yml:125`) and the YAML is at the right level. The token in this step's
    environment is a `ghs_` token scoped to this repository alone, and it **does** have contents read
    (`/repos/…` returns 200) — so a working token is present but is missing exactly the one scope that was
    added. Most likely cause: `anthropics/claude-code-action@v1` is given no `github_token:` input
    (lines 208–210), so it mints its own GitHub App token and overwrites `GITHUB_TOKEN`/`GH_TOKEN` in the
    step env; a job-level `permissions:` block cannot change that token's scopes. Fix from a laptop session
    (the AI step may not edit `.github/`): pass `github_token: ${{ github.token }}` to the action, **or**
    expose the job token under another name in the step env (e.g. `RUN_HISTORY_TOKEN: ${{ github.token }}`),
    which `permissions` does govern. Until then the 09-28-style question "did the fire arrive, or did the code
    crash" still cannot be answered from inside the runner.
  - ✅ **The `ALPHAVANTAGE_API_KEY` gap in this workflow is closed in the file** — the `s2` job now sets it in
    `env:` (lines 126–130), so the next Friday mid-season screen should stop recording `alphavantage: not
    pulled`. Nothing to verify tonight: Wednesday runs no mid-season screen. **Confirm it on Fri Oct 2.**

- **2026-10-01 21:53 ET (Thu) — no housekeeping log line: the AI step hit the weekly token limit.** Run
  36952974201's runlog records `tool_calls: 0`, `is_error: true`, text "You've hit your weekly limit ·
  resets 12am (UTC)". So no PENDING re-check and no log line for that ET day; code's own commits that day
  were unaffected (`a0a1a8a` find_dates, 0 confirmed). The limit had reset by tonight's run.

- **2026-10-02 21:34 ET (Fri) — housekeeping (this run). AEHR retired: the pilot's last PENDING name is
  gone, and the pilot universe is now final.** `check.py` PASS. `due.py t2-list` **empty** — the workflow's
  prompt names no event awaiting T2, so this step wrote no `decision.json`, gated nothing and froze nothing.
  - **What code did on this ET day:** no snapshot session was due (the next is PENG, Mon Oct 5), so there is
    **no `Capture …` and no `Freeze …` commit** — correct, not a miss. Friday, so the **mid-season screen
    ran**: `030cb15` 21:33 ET, `universe/pilot/midseason/2026-10-02.json` — 44 calendar names, one new name
    tested (**RELL**, Nasdaq 2026-10-07 `time-after-hours`), excluded on `size` ($282M market cap), **0
    added**. Then `find_dates apply` (`1d525bb` 21:33 ET) confirmed **0** dates. Code also ran the nightly
    grade (`9b570da` 20:37 ET), the D009 shadow grade (`f526a7f` 21:23 ET) and four paper-ledger runs
    (01:40, 07:17, 12:39, 20:16 ET). No outcome figure is read or written here (rule 4).
  - ✅ **The `ALPHAVANTAGE_API_KEY` gap is confirmed closed**, as the 09-30 entry asked: tonight's screen
    records `"alphavantage": "pulled: 38 rows in window"`, not `not pulled`. The mid-season screen now sees
    both calendar sources again.
  - 🔴 **AEHR → INELIGIBLE `unconfirmed`, written by this step, because code cannot do it.** Both possible
    snapshot sessions for its 2026-10-05 calendar date have now passed with no company confirmation:
    **2026-10-01** (D−2, the BMO case) and **2026-10-02** (D−1, the AMC case, which closed this afternoon).
    AEHR is on no Nasdaq row 2026-10-06 → 2026-10-09, so **no eligible snapshot session remains inside the
    pilot window** (ends 2026-10-09). Tonight's final re-check: `www.aehr.com/newsroom` HTTP 200, newest item
    still 2026-09-28 (CEO Investor Summit — a conference, not an earnings date), newest Financial News item
    still the 2026-07-14 FY26 Q4 release, newest "to Announce … Financial Results" item still 2026-07-07;
    SEC EDGAR CIK 0001040470 newest filings are seven Forms 4 of 2026-10-02 plus one 2026-10-01
    (insider/grant filings after the 2026-09-09 DEF 14A) — **no 8-K carrying a date**; Nasdaq unchanged at
    2026-10-05 `time-not-supplied`; yfinance unchanged at 2026-11-02, intraday and outside the window. Code
    went first and recorded `no_feed` (`find_dates probe AEHR`, 21:34:57 ET), as on every night since 09-29.
    Fifteen company re-checks over 16 days, and the company never announced a date.
  - 🔴 **The gap this exposes, for Season A:** `pipeline/s2_gate.py` reaches the `unconfirmed` branch only
    for an event the **gate actually fires on**, and the gate only fires on an event with a confirmed
    snapshot session. **A PENDING name that never gets a date is therefore never retired by code** — it sits
    PENDING past every deadline until a housekeeping AI step retires it by hand, which is exactly what the
    09-28 → 09-30 entries kept predicting code would do and it never did. One missed AI run (as on 10-01,
    the weekly limit) leaves a stale PENDING row in the universe. **Candidate for Season A: `due.py` marks a
    PENDING event INELIGIBLE `unconfirmed` once the latest snapshot session consistent with its calendar
    date has closed.** The AI step may not edit `pipeline/`'s rule surface here; this is a laptop change.
  - **Pilot universe final: 12 events — 2 FROZEN (MU, NKE) · 3 CONFIRMED still ahead (PENG snapshot Mon
    Oct 5 · LEVI and APLD snapshot Tue Oct 6) · 7 INELIGIBLE** (5 `missed_window`: PAYX, DRI, BB, AIR, JBL ·
    2 `unconfirmed`: CHRN, AEHR). Nothing is PENDING. The pilot can add no further events; the Season A
    screen is 2026-10-09.

- **2026-10-05 22:36 ET (Mon) — housekeeping.** `due.py t2-list` empty for this run, so no `decision.json`
  written by this step. Nothing is PENDING (pilot universe final: MU, NKE, PENG FROZEN · LEVI, APLD
  CONFIRMED for snapshot Tue Oct 6 · 7 INELIGIBLE), so there was no date re-check to do; `find_dates apply`
  (`4a95c1c`) confirmed 0. Code today: `985a1e2` Capture PENG (gate PASS) → `9b72921` Freeze PENG before
  entry open 2026-10-06, plus grade, D009 shadow grade and paper-ledger runs. Nothing failed. No outcome
  figure is read or written here (rule 4).

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
- **2026-10-13 (Tue) housekeeping run:** nothing gated or frozen by this run; no T2 decision awaited. Season A status: 246 PENDING, 71 CONFIRMED, 1 FROZEN (DPZ, ineligible: wide_spread). Probed the six most urgent PENDING names (SMMT, GE, GLXY, PEGA, HXL, DECK): none confirmable (no date announced, no session stated, or ambiguous dates for PEGA/HXL); earliest snapshot sessions have not yet passed, so all stay PENDING. Nothing failed.

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

- ~~Connect GitHub to Claude~~ **done 2026-09-30.** The cloud routine `earnings-s2-trigger`
  (`trig_01QDoKoFrXFk2siYQpqNwDnZ`, https://claude.ai/code/routines/trig_01QDoKoFrXFk2siYQpqNwDnZ):
  - weekdays at 14:45, 15:45, 18:45 and 19:45 UTC; model Haiku; Bash only; no connectors
  - it pushes one empty commit to `claude/s2-trigger`, and a push starts `s2-window.yml` within seconds
  - test fire 2026-09-30 13:43 UTC: pushed `49c87fb`, the run started 6 s later, one Bash call and no
    file reads
  - the laptop task `earnings-s2-dispatch` stays as a backup. Duplicate starts queue behind the
    workflow lock and find nothing to do.
- The Alpha Vantage secret was added 2026-09-21. Confirm on the first grading run: prices should no
  longer be `single_source`.

## 🔴 Laptop sessions 2026-09-28/29 — the cause is settled, Season A is built (branch → main)

**Why AIR and JBL were lost (settled from the Actions API, 2026-09-29):**
- On Mon Sep 28 the **first scheduled run of the day began at 21:11 UTC (17:11 ET)**. Every fire from
  15:07 UTC onward was dropped or delayed past the window.
- Earlier days' first runs were no better: 09-23 18:58 · 09-24 19:00 · 09-25 19:12 UTC.
- Waiting only helps a run that arrives early, and none do. **GitHub's cron is not a usable trigger
  for this repository.**
- A `workflow_dispatch` starts within seconds (09-23: 13:40 UTC, ran at once).

**The trigger now:**
- **Windows task `earnings-s2-dispatch`** on the laptop, weekdays 22:45 and 23:45 SGT, set to wake the
  computer. It runs `ops/dispatch_s2.ps1`: one `gh workflow run … -f purpose=gate`. The run then waits
  for the window.
  - 22:45 SGT = 10:45 ET until Nov 1; after Nov 1 the 23:45 fire does it.
  - Needs the laptop on, or asleep with wake timers allowed. A closed lid on battery may not wake.
- **MU on 09-29** was dispatched from the session (10:36 and 14:33 ET).
- The cron stays as a backup.
- **More robust (needs Jacob):** connect GitHub to Claude at https://claude.ai/connect-github. A cloud
  routine can then push a trigger at 14:33 ET with no laptop at all.

**Frozen 2026-09-29 (all before any Season A data exists):**

| file | what |
|---|---|
| `D006_history_study_v1` | the procedure, frozen 09:12 ET before any history outcome was computed (commit `6c5a22f`) |
| `T1_rule_v0.json` | R-LIT, **FAILED VALIDATION**. No factor cleared t > 3 / BH q < 0.10 on TRAIN; best was H1 (12-month winner, lift +3.0 pts, t 2.56, q 0.063). Composite lift −0.2 pts TRAIN, −0.7 pts VALIDATION, against buy-everything at 54.1% / 54.2%. Frozen anyway, as pre-committed. See `analysis/history/report.md` |
| `D003 v3` | one event per issuer (GOOG/GOOGL, Z/ZG) |
| `D004 v3` | T1 by code · T2 fenced from T1 · hash-random T2 order under capacity · outside-view `prior` + `leak_probe` required · stage revenue tag · base-rate card `D004_base_rates_v3.json` |

**Uncomfortable findings:**
- Buying every event won ~54% of the time with a mean exit-A return of +0.7% to +1.2% before costs.
  That is the opponent.
- In history, **semis were the one cluster where buying everything lost (47.9%)**. Descriptive, a
  candidate only.

**Branch `season-a-readiness` → merged to main after the 09-29 window.**
- An independent code review found 2 critical and 11 other defects, all fixed:
  - T2 freezes would have crashed inside the fenced checkout
  - parallel pushes could lose freezes
  - `find_dates` could confirm a wrong date in some phrasings
- An end-to-end rehearsal in a scratch clone passed: a decision without a prior was held back, and a
  valid one froze with T1 by code, two timestamps and a push.
- **First live test of the new workflow: NKE, snapshot Wed Sep 30**, dispatched by the laptop task.

**The roadmap is `RESEARCH_PLAN.md` (2026-09-30):** the end goal, research questions RQ1–RQ6, gates to
real money (Gate 2, Mar 2027), draft graduation criteria (D008), and the asks of Jacob. Phase 1, due by
Oct 11, before any Season A outcome:
- pre-register D007 and run it on history
- freeze D008
- add the T0-wide shadow, the live option features and the straddle shadow

**Next actions:**
1. ~~D003 v4: replace the single-strike open-interest floor~~ **done 2026-09-29** (`e3f0d7a`): ±2% band, frozen before the Oct 9 screen.
2. **Wed/Thu:** confirm NKE (snapshot 09-30) has `gate.json` and a manifest. Read the logs of the new
   `t2` and `finalize` jobs.
3. ~~Durable trigger~~ done: cloud routine `earnings-s2-trigger` (2026-09-30). Check its first scheduled fires today (14:45 UTC) gate NKE.
4. `find_dates` coverage is ~50% of feeds, because many IR sites return HTTP 403 to scripts. The AI
   housekeeping step covers the rest, most urgent first. Watch the PENDING backlog after the Oct 9
   screen.
5. **Season A screen:** the slot opens Oct 8 16:00 ET, with 8 cron fires plus laptop dispatches (task
   `earnings-seasonA-screen-dispatch`, Oct 9 08:07 and 19:07 SGT).
6. Known limitations, disclosed:
   - live H1–H5 use the intraday snapshot bar
   - the T1 reference median is scored in-sample on its own four quarters
   - companies with no fresh share count (NKE) miss H8
   - git history still contains the T1 rule (a read is flagged in the run log, not blocked)
7. Confirm on Fri Oct 2 that the mid-season capture no longer says `alphavantage: not pulled`.
8. Before Season B's screening date: register `D005_confirmatory_seasonB.json` **without** `T2_confidence` (D005 v3 owns it, pooled A+B), and write and review the pooled H-T2C code.

Jacob asked for the ORCL/CPRT/ADBE read-throughs from the CLAUDE folder: declined (rule 9).

## Watch-outs

- **Alpha Vantage free key: 25 calls a day, 1 a second.** Three probes were rate-limited for firing too
  fast. The ETF-holdings endpoint the leave-one-out benchmark needs is still untested.
- The pilot screen's implied-vol column is a proxy — never reuse it as the §10 rule.
- `FRAMEWORK.md` was drafted in a chat that held PRE v1's full history. Review it with fresh eyes; the
  external evaluator is the check on that.
