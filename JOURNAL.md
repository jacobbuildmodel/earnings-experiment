# JOURNAL — the lab notebook

> Dated observations: what happened, what it taught us, what changed. Newest first. This is where
> surprises, failures and hunches are written down *as they happen*, so nothing is reconstructed
> later from memory.
> - Not evidence: findings live in `analysis/` and graded outcomes in `outcomes/`.
> - Not rules: rules live in `registry/`.
> - Each entry says which research question (`RESEARCH_PLAN.md`, RQ1–RQ6) or gate it touches.

---

## 2026-10-09 (Fri) evening — the free minutes ran out; the repo went public

- **What happened:** from 16:03 ET every GitHub Actions job was refused before it started. The private
  repo had spent its 2,000 free minutes for the month by the 9th.
- **Where they went:** the S2 window's "wait for the window" design.
  - It was the right fix for dropped cron fires (PAYX, DRI and BB, Sep 21–22), but a waiting runner bills
    every minute it sleeps: 1,338 min in 9 days.
  - Add the one-off D007 batch (762 min).
- **Lesson: every reliability fix has a meter.** Nobody had counted runner minutes as a budget, and the
  failure was silent: a 3-second "failure" with the reason only in a check-run annotation, not the log.
  **Check annotations whenever a run fails in under 10 seconds.**
- **Jacob chose public over a $15 cap.** Public Actions minutes are free. Side benefit: the
  pre-registrations and their commit timestamps are now publicly checkable.
  - The history was scanned first: no secrets, no portfolio data.
- **DPZ, D011's first fill:** the butterfly filled 4¢ better than the far-side quotes, which verifies the
  limit-price sign. One fill says nothing about edge.
- **D011 v2 (the long straddle on a second account) frozen.** It waits for Jacob's keys.
  - Not sent to a second-model review: it is a thin wrapper over the reviewed v1 code, and that wrapper is
    covered by tests. The risk is accepted and written down here.

## 2026-10-08/09 — paper straddles: the account cannot hold the trade we test (RQ4, RQ6)

- Jacob: "add paper straddles now".
- **Probe first, build second.** Read-only checks plus orders placed while the market was closed, each
  one cancelled.
  - The Alpaca paper account is options level 3, but it **refuses a naked short call**. So SH-X's exact
    trade, a naked short straddle, cannot be placed there.
  - It also refuses an order against an opposite open order ("wash trade"). A long and a short straddle
    on the same contracts cannot coexist in one account.
  - It accepted both signs of an `mleg` limit, so the price convention is unproven.
- **What we built:** D011, the short iron butterfly, which is SH-X plus wings at ±2 straddle prices.
  - It is placed minutes after each gate and closed on the reaction session from 14:30 ET.
  - It is descriptive and adds no test. It measures whether SH-X's bid fills are real, the tradeable
    P&L, and capacity.
- **First number, a dry build on live AAPL quotes:** opening and closing at the same quotes costs $0.57 of
  a $9.60 credit (~6%). That is the spread toll on every round trip, before any edge.
- **The review earned its cost.** An independent reviewer (Sonnet) said DO NOT FREEZE, with three
  blockers:
  - a cancel racing a fill could double a position
  - a lost ledger push would resend the same order
  - a failed exit would strand a real position
  - **Lesson:** an order-sending loop must treat the broker, not our file, as the source of truth.
  - The rewrite looks up every client id before sending. The re-review said FREEZE WITH FIXES, the fixes
    are in, and 20 offline tests pass.
- **Frozen 11:39 ET Fri (`f84849d`)**, before the first Season A gate. DPZ, at 14:30 ET today, is the
  first candidate trade.

## 2026-10-08 (Thu) — free capacity found: the cloud session runs the decision call

- Jacob: no new money until there are results.
- The hint was in the logs: the cloud trigger routines kept firing after the decision token's weekly
  limit, so they draw on another allowance.
- **Probe, then the real code:** a claude.ai cloud session can run the same isolated `claude -p` call.
  It passed every isolation check, matched the Actions answer, and cost $0.09.
- T2 now runs there four times a night. The token stays as a last resort.
- Lesson: before asking for money, inventory every allowance the person already has. The $100 cloud
  credit was noted in STATE on 10-02 and never used for capacity.
- **Open:** whether the cloud runs bill the credit or the Pro plan. Measure it on the first real batch.

## 2026-10-07 (Wed) — the pilot ends on a capacity refusal; four fixes before Season A

- **APLD lost its T2 to a WEEKLY limit on a separate, small account.** It froze with T0 and T1 intact.
  - The decisive measurement was the reset time. The token's account resets Oct 10, but the laptop
    chat's account is at 38% and resets Oct 12. They are different pools.
  - Only ~$5.5 of logged work emptied the token's pool, so **Season A cannot run on it.**
  - A workflow-only API-key fallback is now wired. The money decision is Jacob's.
  - Lesson: "the queue spreads work over 5-hour windows" solved the wrong limit. The weekly one binds
    (RQ1).
- **Date coverage was the biggest silent leak, and it was half the universe.**
  - Code could read only 49% of the companies' own IR feeds: 403 bot walls, JS sites, wrong hosts.
  - The same releases are on Nasdaq as wire copies, and with that fallback coverage is 99%.
  - Lesson: measure a pipeline step's coverage on the real universe before the season, not from a
    pilot of 12.
- **The busy-day rehearsal passed:** 40 events in 9 minutes. Gate capacity is not the constraint.
- **Jacob relayed a run-up finding from the DRIVE chat.** It was registered as a shadow (D009 v3, SH-RU),
  never as evidence.
  - The reviewer's main catch: a beta-1 SPY benchmark in a rally year turns high-beta names into a
    "run-up". The primary is now a pre-window shrunk beta.
  - The honest expectation: the AI-hardware subset will be "insufficient".

## 2026-10-06 (Tue, 07:45 ET) — v4 stage 2 works on the runner; a structural hole at Season A's start

- **The D004 v4 stage-2 call works where it has to.** The smoke test on the Actions runner used the real
  CLI, the token and the flags. It returned an isolated one-turn decision for $0.085 equivalent, about
  1/37 of the agentic Opus run. That is the capacity fix in practice (RQ1, power: more decided events per
  season).
- **The cron is still late:** it fired 4 h 40 m after 21:00 UTC. That cost nothing here, because the queue
  is the trigger for real decisions. It is one more reason never to rely on GitHub cron timing.
- **Check the first day of a season against the screen date, then count what is actually there.** A BMO
  reporter on Mon Oct 12 can never be gated, because its snapshot is Thu Oct 8, before the screen. But
  Oct 12 is Columbus Day and lists one micro-cap. A structural hole with nothing in it needs no rule.
- **The real hole was one level down: *when* code confirms dates.** Confirmation ran only in the evening
  run and never counted for a same-day snapshot. So a screen that finished late on Oct 8 would have
  silently cost the whole first snapshot day. The same was true of any company that announced late.
  Fixed with a code-only morning pass (`find_dates --urgent`), before the gate window. The lesson for
  every pipeline step: trace the *latest* time each input can arrive, not the usual one (RQ1: events lost
  to plumbing are power lost).
- Correction to this morning's note: a refused pilot T2 is retried by the evening run before the
  last-chance freeze, so "the second may be MISSING" was too pessimistic.

## 2026-10-03 (Sat, early UTC) — cloud session: pooled D009 report, D009 v2 draft, Gate 1 builder

A claude.ai cloud session (`ops/cloud_session_prompt.md`), on branch `claude/great-lamport-tor2q4`.
Nothing on `main`, nothing under events/ universe/ outcomes/ shadow/ paper/ or workflows touched.

**Network still blocked (infrastructure).** SEC, Nasdaq, NYSE, Yahoo and DoltHub all return a proxy 403
(`ops/cloud_probe_2026-10.md`). That is the same as 09-17. The fix is Jacob's: set the environment's
network access to Full. T4 (D010 exploration batch 2) and the off-season print count were not done.

**T1 — `shadow.py report-pooled seasonA seasonB` (D009 §5's registered verdict).**
- The statistics core was moved into `stats_()`. The single-season report on the pilot is
  byte-identical before and after.
- `tests/test_shadow_stats.py`: the intercept-only wild bootstrap holds its size at **3.95–5.4% at 8,
  10, 12, 30 and 40 clusters** (2,000 replications each), including fat-tailed noise. It has 93% power
  at a +2% true mean on 30 × 10.
- Holm stays m = 3 with a missing or NaN test counted as p = 1.
- *Lesson:* an early 400-rep run showed 7.5% at 8 clusters; at 2,000 reps it was 5.2%. Check a size
  test's own noise before calling the test oversized.

**T2 — D009 v2 DRAFT, the year-round market-wide shadow (RQ1, power).**
`reviews/proposals/D009_v2_yearround_DRAFT.md`; analysis in `analysis/d009v2/`.
- **Off-season sessions add ~+10–25% information a year**, but only **+0.07 to +0.15 expected t** to
  the A+B verdict (2.19 → 2.26–2.34 at +0.65%). An accumulator, not a power fix.
- **Off-season reporters are another population:** net +0.27% (t 0.5) against +0.59% in-season; the
  difference has t −0.56.
- **The suggested universe (last season's S1 capture) would miss ~99% of off-season prints.** Only 5 of
  389 came from a ticker that printed in the preceding season. Firms report on a fixed lag from their
  own quarter end, so off-season reporters stay off-season.
  → The draft uses a fixed-date screen: the Nasdaq stock screener plus the window's calendar, then v1's
  S1 filters.
- The code (`pipeline/shadow_offseason.py`) refuses to run until v2 is frozen.
- **Clock:** Season A's SH-M enters H-MY only if v2 is frozen before Oct 12's open.

**T3 — `pipeline/gate1.py`.** It assembles D005 (T1, T2, the confidence test, calibration), H-S0, D009
and the CHARTER §6 health numbers, then lists the Gate 1 decisions. It was tested on the pilot (to a
temp path) and on a synthetic season.
- *Surfaced on the pilot:* 5 missed windows (known), and **1 runlog fence flag** on 09-30 housekeeping.
  It is a pattern match on a STATE.md edit, so a false positive, but the health line reads 1 until a
  human clears it.

**For the laptop session:**
- review the PR
- register the new `shadow.py` hash (D009 implementation v2)
- probe the Nasdaq screener, then decide and freeze D009 v2 (before Oct 12 to include Season A)
- add the off-season steps to `shadow.yml`

---

## 2026-10-05 (Mon) — D004 v4: the AI's capacity problem, solved without paying

- **What happened:**
  - The weekend Haiku load test: 8/10 refused with "session limit". One Opus housekeeping run had used
    up the 5-hour allowance.
  - Jacob declined a paid API key and asked for a free workaround.
  - The GitHub research found:
    - GitHub Models **retired 2026-07-30** (search results were stale)
    - Gemini CLI personal use retired
    - OpenRouter's free tier is 50 requests a day
    - the Gemini API free tier is alive
- **What it taught:** the cost was the *method*, not the model. An agent re-reads its growing context
  on every one of ~50 turns. Code gathering the inputs and ONE call costs about 38× less ($0.08 against
  $3.14). It also makes T2's information set exactly reproducible and timestamp-verified, which is
  stronger than v3 for truthfulness.
- **What changed:** D004 v4 frozen. Stage 1 freezes a code-built dossier at the snapshot; stage 2 makes
  one isolated no-tools call; the deadline moves to entry open − 15 min; the queue runs overnight; and
  Gemini (T2G) and the mean of the two (T2E) are free shadows.
- **The process worked:**
  - The rehearsal caught stage 2 overwriting stage 1's timestamp tokens.
  - The independent review caught:
    - an unfrozen method
    - laptop settings leaking into the call
    - MD&A extraction wrong on 6 of 10 filings
    - transient SEC errors being frozen in
    - a queue that one bad reply could stall

  All are fixed before the freeze.
- **Uncomfortable:**
  - T2 is now Sonnet with a fixed dossier, not Opus doing its own research. Pilot T2 is not comparable
    and is never pooled with Season A.
  - Gemini's free tier said "high demand" (503) for every 3.x Flash model all morning, so T2G coverage
    may be patchy.

---

## 2026-10-02 (Fri, late) — the first cloud session, reviewed

- **What happened:** Jacob's $100 claude.ai credit pays for cloud sessions only, not for Actions,
  Routines or an API key. A session briefed by `ops/cloud_session_prompt.md` opened PR #1:
  - the pooled D009 report
  - a draft of the year-round shadow
  - the Gate 1 report builder
  - 30 tests
- **Its uncomfortable findings, which hold:**
  - Off-season reporters are a separate population: only 1% printed in the preceding season. A
    season's own universe cannot cover the off-season.
  - The off-season premium in history is +0.27% net (t 0.5), against +0.59% in-season.
- **Laptop review:**
  - the tests pass, and there is no look-ahead
  - the Nasdaq screener works (7,073 listings)
  - last year's off-season averaged ~8 prints ≥ $2B on days with any, so the gain is about +24–40%
    of information a year
- **What changed:** **D009 v2 frozen before Season A's first entry**, clock 2026-10-05, so all of Season
  A's market-wide events count toward H-MY.
- **What it taught:** cloud sessions are a good fit for no-network build and analysis work. With
  network access set to Full, they could take data work off Jacob's weekly limit.

---

## 2026-10-02 (Fri, afternoon) — "too passive": a push for power

Jacob: "we too passive in experimenting and not hungry enough for results"; also asked why the
cloud/tokens weren't being used.

**Phase 1 was reported done; it wasn't (truthfulness).**
- RESEARCH_PLAN Phase 1 required the T0-wide shadow, the straddle shadow and the live option features.
  None was in code.
- D008's H-S0, the graduation hypothesis, was frozen on 09-30 but computed nowhere.
- grade.py had changed on 09-23 without its implementation hash being appended.
- *Lesson:* verify in code before reporting a phase complete.

**Two shortcuts to power tested on history (RQ1); both negative.**

| test | clustered t, net premium |
|---|---|
| equal weight (as D008 tests it) | 2.76 |
| sized 1/volatility | 2.11 |
| minus SPY | 2.25 |
| minus sector ETF | 2.57 |

- *Why both fail:* the premium sits in the volatile names, and each stock's own move dominates.
- *By-product:* paper.py sizes S0 by 1/implied move, so the paper P&L will understate the premium S0
  harvests. Its job is risk control, not the test.

**The binding constraint is entry sessions, not events (power).**
- Variance splits into ~1.8–1.9% shared by a session and ~9.2–9.6% per stock.
- Expected one-season t at the history premium:

| track | events / season | expected t |
|---|---|---|
| gated | ~150 | ~0.8 |
| T0-wide | ~250 | ~1.0 |
| market-wide | ~1,300 | ~1.5 (ceiling ~1.8) |

- *Uncomfortable:* **D008's Gate 2 test on gated events has expected t ~1.1 after A+B.** It will most
  likely read "no evidence" even if the premium is real. → CHARTER I12, a decision for Gate 1.
- Last year's same six weeks: 1,776 Nasdaq-calendar prints ≥ $2B. Off-season: ~60% of weekdays carry one.

**Built and frozen: D009 shadow tracks** (`pipeline/shadow.py`, `shadow.yml`).

| track | what it is |
|---|---|
| SH-W | T0-wide: every company-confirmed allowlist date, gate or not |
| SH-M | market-wide, ≥ $2B, any industry, dated by a write-once daily Nasdaq capture taken on the snapshot session |
| SH-X | the exact short straddle: the gate's bid quotes held to expiry, intrinsic value paid at the expiry close |

- Family: H-M, H-X, H-VOL. Holm m = 3; MDE on every result; verdict on A+B pooled.
- **Pilot functional test, SH-W: 0 wins in 5 graded** (PAYX, DRI, JBL, MU, BB). Mean −3.7% net, −3.2%
  over SPY. Pilot = bugs, not findings.

**The SEC timing check caught a wrong company date.**
- AAR (AIR) told us "after the close on Tuesday, September 29".
- Its results 8-K (Item 2.02) was accepted at **20:58 ET on Sep 28**, a day early.
- A 1.01/3.02 8-K (a material agreement and an unregistered sale of shares) followed at 01:13 ET.
- A company-confirmed date can still move. The 8-K check is what catches it.

**Independent review (Sonnet, adversarial, 2026-10-02).** No leakage. Fixed before the freeze:
- a failed capture would have been locked in for the day
- SH-X skipped the timing void (a late print would hand it a free premium)
- Holm ran over whichever tests produced a p, not over the fixed family
- the `late` rule voided an 8-K that merely lagged its release
- SEC errors became final
- splits were not handled
- the universe file's commit time was not checked
- vol60 did not match H4
- the fallback lacked provenance
- H-W was power-free inside the family → made descriptive
- The reviewer corrected an overstatement: "the only lever is more events" holds only up to ~25
  events per session.

**The tokens: the weekly limit was exhausted (RQ5 / infrastructure).**
- A 12-way T2 load test on the Actions token: **all 12 refused at the first call, $0 spent.**
- The message: "You've hit your weekly limit · resets 12am (UTC)". It was the same for Sonnet 5.5,
  Opus 5.5 and Haiku 4.5.
- The subscription token that T2 uses shares one weekly budget with Jacob's own chats, and this week's
  chats used it up.
- *Consequences:*
  - tonight's 23:00 UTC housekeeping AI step will fail (before the reset)
  - if this happens in a Season A peak week, T2 goes MISSING for the rest of the week
  - the claude.ai trigger routines are on the same account, so the laptop and cron backups matter
- *Changed:*
  - the `t2` job retries a 429-refused decision once on `ANTHROPIC_API_KEY` (inert until Jacob adds one)
  - the retry clears the partial files first; its log is marked `_apikey`
  - `max-parallel` 5 → 10 (~50 → ~100 decisions before the 16:00 deadline; D004 v3's hash order unchanged)
  - a one-off Haiku 10-way concurrency test is scheduled for 01:15 UTC Oct 3, after the reset

**T2 ensemble (CHARTER I2): deferred.** With the weekly budget binding, extra AI runs would take
capacity from T2 itself.

---

## 2026-10-02 (Fri)

**D007 exploration batch 1: NO candidates (RQ2/RQ3, negative knowledge).**

| signal | lift, pts | t | note |
|---|---|---|---|
| E1 short-selling pressure (5d vs 60d) | +1.7 | +1.61 | closest; same sign in both halves; far below t 3 |
| E2 peer read-through | −1.5 | −1.29 | wrong way vs the literature, weak |
| E3 VIX · E4 SPY trend | +0.8 · +0.1 | 0.7 · 0.1 | no regime effect on the hit rate |
| E5 Wikipedia attention | −1.4 | −1.23 | wrong way, weak |
| E6 early vs late reporter | −0.4 | −0.40 | nothing |
| E7 IV/HV · E9 call−put IV | −0.5 · −0.1 | ~0 | nothing |
| **E10 put skew** | **−2.4** | **−2.12** | **opposite** to Xing-Zhang-Zhao: steep put skew did slightly *better*. Weak, but a surprise worth one line |
| E8 IV run-up | +5.0 | +3.91 | **insufficient**: DoltHub's `iv_month_ago` is mostly empty, so only 76 events over 14 dates |

- *What it taught us:* none of the free, point-in-time signals, from the literature plus the
  vol-selling repos, selects within the earnings premium on 2,771 prints. With the 10 D006 factors,
  **20 ideas have now been tested; none survives.** The likely graduate is the plain premium harvest
  (S0), not selection.
- *What it leaves:* the live weekly-option capture (exact straddle, open interest, volume), which no free
  history has, and T2. Both are measured only in Season A onward.

**NKE (pilot), the first live outcome: −8.2%.**
- The official opens: $35.45 (Oct 1) → $32.55 (Oct 2).
- T0 BUY and T2 BUY (0.52) both lose. Paper: −$475 on simulated legs (the order had expired).
- *Observation:* the loss was inside the 8.6% implied move: a normal-sized miss, not a tail.
- T2's stated deciding variable was the China / fiscal-2027 commentary; grading the reason is not
  done (rule 4), only the outcome.
- One event says nothing (pilot = bugs, not findings).

**Parallel-gate load test (live quotes, 14:15 ET): 16 events through 4 workers in 48 s**, no errors, no
rate limits. That projects to ~80 events in ~4 minutes, inside the 80-minute window. The empty T1
factors in the test are an artifact: the dry run used future snapshot dates.

---

## 2026-10-01 (Thu)

**NKE paper buy expired unfilled (RQ6, execution).**
- *What happened:* the market-on-open order was accepted at 20:17 ET Sep 30 and routed 04:00 ET, then
  **expired at 09:30:37 ET with 0 filled.** Diagnosed with a read-only order query.
- *What it taught us:* Alpaca's paper simulator does not fill opening-auction ("opg") orders, and its
  docs don't say so. This is a paper-vs-live gap to remember: real money would use a true auction order.
- *What changed:*
  - paper now queues market DAY orders while the market is closed; they execute at the next open
    (`31d56f1`)
  - Jacob's rule: a platform failure is booked at the official open, labelled *simulated*
    (`77f4666`). NKE's simulated buy: 164 @ $35.45, the Oct 1 official open.
  - simulated legs are excluded from the D008 §3 fill-quality test
- *Next test:* PENG, queued Mon Oct 5 evening.

**D007 option-chain download stalled (infrastructure).**
- DoltHub answers 3-ticker queries in ~20 s, but busy dates (up to 58 tickers in one query) time out.
  The runner looped, restarting with no progress.
- *Fixed:* groups of 3, plus a stall guard. Implied-volatility history is complete: 509/509 snapshot
  dates.
- *Lesson:* every self-repeating job needs a "no progress → stop and say so" guard.

**Season A screen pre-flight passed (scratch clone).** D003 v4's one-ticker-per-issuer works (GOOGL and
ZG out, GOOG and Z in); the foreign filer TSM is out; the resumable capture and init-status work.

---

## 2026-09-30 (Wed)

**First full chain, NKE (AMC Oct 1). Every step worked:**
- gate PASS 14:31 ET (implied move 8.6%; open interest 4,037 at the strike)
- per-event AI job: **T2 BUY, confidence 0.52**
- frozen at 14:40 ET with two RFC 3161 timestamps
- *T2's reasoning, abridged:*
  - It started from the history base rate: consumer cluster 55.5%, AMC 53.8%.
  - It nudged up for a washed-out stock: −47% over 12 months, a consensus already cut, and four
    straight EPS beats.
  - It marked down for company-stated headwinds: the 10-K's Greater China and Converse warning through
    fiscal 2027, a one-off tariff recovery inflating the last quarter, a new CFO's first call, and two
    of the last four reactions at −10%.
  - Its stated deciding variable: forward commentary on China and the fiscal-2027 trajectory, not the
    EPS surprise.
- *Observation:* given the base-rate card, T2 anchored on it and moved only a little. That is the
  calibrated behaviour D004 v3 asked for. Whether a 0.52 "barely a coin flip" adds information is RQ5,
  answered only over many events.

**Where the premium lives (RQ1, history, exploratory description).**
- +0.79% of the +0.85% per-event mean comes from the overnight reaction; the session before the print
  adds ~0.
- Market-adjusted it is +0.73% over SPY. Clustered by entry date, t = 3.6.
- Busy dates (≥ 10 prints): +1.02%; quiet dates: +0.45%.
- *Pitfall caught:* equal-weighting each date gives t ≈ 1, because quiet days carry few, noisy events.
  The right statistic is the clustered per-event mean.

**Open-source review (5 repos).**
- The public "earnings edge" world sells volatility; nobody measures directional selection.
- The earnings-call NLP repo "predicts" with the call transcript released *with* the results: look-ahead.
- **Found: DoltHub's free historical options** (IV/HV for 2,331 stocks from 2019, and chains). It
  replaced the planned $40 data purchase.

**Frozen:**
- D007 (10 exploration signals), before its data was pulled
- D008 (graduation criteria; H-S0 is confirmatory from Season A)

---

## 2026-09-29 (Tue)

**The cause of the lost events, settled.**
- GitHub's scheduled runs never land in the 14:30–15:50 ET window. On Sep 28 the first run of the day
  began at 17:11 ET.
- *Fix:* a dispatched run that waits (laptop, then a cloud routine). MU was gated at 14:31 ET, **the
  first gate in the pilot's history.**

**MU rejected `thin_oi`, a rule flaw (RQ1 power).**
- 260 contracts at the single nearest strike, while the expiry held 309,771.
- A single-strike floor scales with share price, so it excludes liquid high-priced names.
- Fixed for Season A in D003 v4 (a ±2% band). The pilot and MU's record are unchanged (rule 5).

**History study (D006):**
- No free factor beats buying everything.
- T1 rule v0 is frozen as "failed validation" (lift −0.7 pts in VALIDATION).
- Semis' overnight reaction wins only 46.9% of the time: a candidate, not a finding.

---

## 2026-09-28 (Mon)

**Season A preview: 317 candidates, 165 prints on Nov 3–5.** The pipeline was built for 12. That
prompted:
- parallel gating
- per-event T2 jobs
- code-confirmed dates
- a 300-minute, resumable season screen (the old 60-minute limit could never have finished ~4,300
  names)

**AIR and JBL lost:** the wait-for-the-window fix needed a run to arrive early, and none did.
