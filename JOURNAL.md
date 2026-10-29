# JOURNAL — the lab notebook

> Dated observations: what happened, what it taught us, what changed. Newest first. This is where
> surprises, failures and hunches are written down *as they happen*, so nothing is reconstructed
> later from memory.
> - Not evidence: findings live in `analysis/` and graded outcomes in `outcomes/`.
> - Not rules: rules live in `registry/`.
> - Each entry says which research question (`RESEARCH_PLAN.md`, RQ1–RQ6) or gate it touches.

---

## 2026-10-29 (Thu) 09:40 ET — the funder wants results before the record can give a verdict (Gate 1, RQ1, all RQs)
- **What happened:** Jacob asked for a Stage 1 review on Tue Nov 3 (SGT): results he can use to judge whether the
  model is useful, not redundant and worth funding, presented like a PhD qualifying review. The plan put Gate 1 in
  early December, after Season A ends on Nov 20.
- **What it taught:** at history's per-event Sharpe of 0.087, a real premium shows a t of about 0.9 at 100 events.
  An honest review three weeks into the season can show that the record is truthful and whether the live premium
  contradicts history. It cannot show that the premium is real. Saying so before the data is the only way a weak t
  is not read later as failure, or a lucky one as proof.
- **The uncomfortable number:** the weekly AI allowance read 85% on Thursday morning, a day ahead of the estimate.
  The experiment outgrew the plan's allowance this week, so capacity is part of the funding question, not an aside.
- **What changed:** `registry/D017_stage1_review_v1.md` was frozen before any look. It sets the data cut, six
  pillars, the words each result may use, a firewall (the look may inform funding only) and the evidence-to-funding
  table. It also registers the global multiplicity view. Plan: `ops/stage1_plan_2026-11.md`. The build waits for
  Monday's reset.
- **09:28 ET:** Jacob chose D003 v5 = A4 on the D016 counts, before any look. The Season B gate was decided blind,
  which the look's firewall needed (`registry/D003_v5_choice_v1.md`).

---

## 2026-10-28 (Wed) 09:55 ET — an alarm that is always on reads as off (instrument reliability, all RQs)
- **What happened:** health had read RED every day since at least Oct 20. The cause was the same each time: DPZ's 100
  leftover shares (sold at 09:35 ET today) and its permanent flag, which also turned ~10 paper-options runs a day red. A new RED, such as a
  T2 about to be missed, would have looked exactly like the old one. Health now keeps a list of acknowledged alerts.
  A line is set aside only if it reads exactly as acknowledged, and a failed run only if its own log shows the
  acknowledged flag was its sole reason to fail. Against the live record, all 10 of the last day's failed runs
  qualified. Tuesday's 5 PASS names (CMG GOOG MSFT NOW QSR) froze all three AI tracks 15 h before the deadline.
- **What it taught:** "known" has to be proven per run, not assumed by name. The window runner fails for the same
  reason, yet it still alarms, because nothing yet reads its log. And a chat paused "until 11:20" resumed the next
  morning: every measurement that depends on someone prompting at the right minute gets missed.
- **The uncomfortable number:** with no chat here, weekly AI use still rose 15 points in 25 hours, double the day
  before. At that pace the 60% stop rule ends laptop work before Thursday's build day.
- **What changed:** `283515e` (the marker). Owed: the window runner's jobs; a per-PASS cost from the routine run logs,
  not from prompt timing. Jacob kept the stop rule (09:52 ET): the build day and the DST work wait for Monday's reset,
  and the first EST session is also the first day the inventory can be done.

---

## 2026-10-28 (Wed) 09:40 ET — DPZ's stray shares sold (paper account clean-up, capacity)
- **What happened:** with Jacob's yes, the 100 DPZ shares assigned from the 2026-10-13 straddle were sold by one
  market day order in the paper options account: filled $308.38 at 09:35:48 ET. The laptop holds no paper keys, so a
  new hand-run workflow (`paper-flatten.yml`, `pipeline/paper_flatten.py`) sent it. It refuses unless the account
  holds exactly the stated shares, runs in its own concurrency group, and touches no ledger or track.
- **What it taught:** a position no ledger owns still costs the experiment: it tied up the margin the peak's opens
  need (`ops/capacity_peak_2026-11.md`: ~58% of butterfly opens refused with DPZ held, ~33% without). It sat for
  15 days because the fix needed Jacob, and no deadline was attached until the capacity count put a cost on it.
- **What changed:** the margin is freed for the peak. Health's "position not in ledger" line should clear on its next
  run; the DPZ flag stays in the hash-locked ledger.

## 2026-10-27 (Tue) 08:20 ET — the guard was guarding a folder nobody used (instrument reliability, all RQs)
- **What happened:** Jacob asked for the hand-off rule to be enforced. The new guard refused nothing in its first
  live drill. The chat's hooks run the copy in the main project folder, and that folder had sat at Oct 21, 286
  commits behind, because every chat now works in a worktree and pulls only there. No guard change since Oct 21 had
  ever run. After a fast-forward the drill refused a command and allowed `git status`, as designed.
- **The paper reds:** every completed paper-options run since at least Oct 21 is red for one reason: the DPZ record's
  permanent flag. A red that never clears is not an alarm, because a new failure looks the same.
- **What it taught:** "committed and tested" is not "running". A test proves the code; only a live drill proves the
  deployment. And this chat went from 96k to 217k in 25 minutes and spent 47 points of the 5-hour window. A long chat
  costs the cloud routines' allowance too.
- **What changed:** the guard refuses all but the hand-off steps past the line (`7fd5995`). `startup.py` keeps the
  main folder current. Owed: the new-RED marker, so health reports known alerts as known.

---

## 2026-10-27 (Tue) 07:55 ET — the paper account was never sized for the peak (RQ6, D011 capacity)
- **What happened:** the peak-capacity computation found that D011's sizing rule, 0.5% of equity per event, almost
  never applies. On a ~$91k account 0.5% is $456, and any straddle dearer than $4.56 is still one contract. 23 of 26
  butterflies sat on that floor, so each took ~2.6% of equity, not ~0.7%.
  - With every gate opening a butterfly, the main account's margin passes its equity from tomorrow (Oct 27). On the
    peak's Wednesday it reaches about twice its equity.
  - A day-by-day replay refuses ~58% of the wanted opens, ~33% once DPZ's stranded shares are sold.
  - Mon's T2 fire ran clean (3 PASS, all three tracks by 17:55 ET).
  - The planned measurement of what one PASS costs in AI allowance failed: the laptop slept and killed the waiter.
- **What it taught:** a sizing rule written as "0.5% of equity" was really "one lot". Every refusal is D011's own
  question 3 answering itself: the account can't carry a peak day.
  - The refusals are not random. They fall on late-alphabet and dear names, so peak-day execution figures need that
    disclosure.
  - A timer on a sleeping laptop is not a measurement plan.
- **What changed:** the note and the script are committed; DPZ's flattening is now urgent, not tidy-up.
  - Jacob asked that the fresh-chat hand-off be enforced, not advised. This chat ran to ~215k tokens because a chat
    started by another session can't start its successor.

## 2026-10-26 (Mon) 11:30 ET — the dark peak was mostly our reader, and the allowance is a second clock (power, all RQs)
- **What happened:** for the 60 unconfirmed names reporting Nov 2–6, a random 10 were read by hand against company
  releases. Half had already announced date and session, some as early as Sep 28. The code missed them for
  ordinary reasons:
  - a release page that refused the download;
  - "financial markets" in place of "market";
  - a call replay's "available until November 19" read as a second report date.
  Fixing the three and re-running confirmed 29 names in two hours; peak coverage went from 62% to 77%. Separately,
  the cloud T2 runner was refused all Sunday night by the account's weekly limit, and the usage card says Pro, not Max.
- **What it taught:** (1) "no date announced" was mostly a statement about our parser, not the companies. One recall
  audit of 10 is worth more than days of re-running the same parser. (2) The scored decision depends on an allowance
  shared with every chat, and when that allowance is spent, nothing in the repo shows it. Last week it ran out with
  no PASS waiting. In the peak week it would cost T2s that can never be redone.
- **What changed:** find_dates v4; a usage rule for laptop chats; the allowance goes into Tuesday's capacity
  computation. D016 decided A4 for a Season B proposal. An untested lead for the Season B screen: names with only
  monthly expiries pass the gate 1 time in 15.

## 2026-10-21 (Wed) 21:05 ET — the alarm was on, and no one could hear it (instrument reliability, all RQs)
- **What happened:** from 17:21 ET every cloud routine stopped at its first git command. The sandbox's local `main` was
  a day stale in a shallow clone, and after ~107 commits `git pull --ff-only` could find no common ancestor. WDC and
  MXL were 12 hours from losing their scored T2. Health saw it ("T2 AT RISK" from 18:24 ET), but the report had been
  RED since 04:49 ET for standing items, so the new line changed nothing anyone would notice. Found at 20:45 ET by a
  resuming chat, fixed with Jacob's OK at 20:49 ET, and both T2s were frozen by 20:51 ET.
- **What it taught:** (1) the cloud copy is not the repo. 10-20 broke on its missing history, and 10-21 on its stale
  branch. Build from the fetched tip, never from a local branch. (2) An alarm that is always RED carries no
  information: the status has to say what is NEW. (3) Outcome checks (T2 AT RISK) caught a failure that left no log;
  process checks (the new "AI step refused") cannot see a run that never reached the code. Both are needed.
- **What changed:** the step 1 of three routines; three alarms in `health.py` (AI step refused, dates stale, runner
  not acting). Owed: mark RED lines new since the previous run.

## 2026-10-21 (Wed) 13:40 ET — the gate audit: where Season A's names are lost (power, RQ3/RQ5)

- **What happened.** D016 was frozen at 13:31 ET, before any count was computed and before NOC/RTX/VICR paper P&L.
  Then an interim run on the 15 gates.
- **What it taught.**
  - The spread rule is not a near-miss problem. 9 fail `wide_spread`, but 7 of them fail by far (straddle spread
    13.8–39%). Only RTX (8.5%) and TTMI (8.9%) are rescued by measuring the spread on the straddle.
  - The losses cluster in two places: names with only a monthly expiry (0 of 6 PASS) and names under $100 (0 of 4).
    Those are universe features, not gate settings. The bigger power lever is more liquid names, not a looser gate.
  - `gate.json` hid 3 double failures (DPZ, HXL, VICR also fail open interest). Recording every check matters.
- **What changed.** Nothing live. The Fri Oct 23 decision run turns counts into a D003 v5 proposal for Season B.

## 2026-10-21 (Wed) 13:15 ET — describing the experiment to outsiders without leaking it (truthfulness)
- **What happened.** Jacob asked for a full, candid description of the experiment for his LinkedIn profile and an
  SMU Economics application, with every claim labelled BUILT, PLANNED or BELIEF.
- **What it taught.**
  - The honest track record is mostly *negative knowledge*: 20 history signals tested, none beat buy-everything;
    straddles lose after costs; the first hour after a print showed nothing that validated. The live record has
    0 graded Season A events.
  - Every frozen T2 confidence on the 5 PASS events sits at 0.45–0.54. The AI itself rates these prints near coin
    flips around the base rate. The model shadows disagree on ABT and META.
  - An outside write-up is a leak route. It must report counts and closed history, not interim live numbers, or
    the owner's coming counts-only decisions (D016, D003 v5) stop being blind.
  - Authorship needs care. Jacob set the question, the outcome, the universe and the rules. AI wrote all the code
    and the registry texts. 587 of 841 commits are the automation's own.
- **What changed.** Nothing in the experiment. The brief recommends a one-event "proven blind" page for LRCX
  2026-10-21, chosen before its grade exists, so the showcase can't be cherry-picked.

## 2026-10-21 (Wed) 11:40 ET — what a fresh chat re-reads, and a leaner hand-off (infra; CHARTER: speed)
- **What happened.** The token study found the hand-off itself is the biggest waste left: ~18 extra calls of
  re-reading. I measured what those calls read. Each call's context growth was split into its own output and
  its tool results, and the results were binned by file or command. Sample: 8 fresh chats, 39 prompts in old chats.
- **What it taught.**
  - A fresh chat grows +99k before its first edit, against +13k for a new task in an old chat. 82% of it is
    three things: its own thinking over ~20 calls (31k), code and registry files (29k), and STATE.md (22k).
  - STATE.md costs twice what we thought: a full read is 19–22k, because tool output runs ~0.44 tokens per
    character. Before the Oct 19 move to history, chats read it in two passes, 45–47k.
  - This chat repeated the pattern, from a good brief: 18 calls and +87k. The brief named files but not lines,
    and the rule said "read STATE.md in full".
  - The one chat with a tight brief needed 5 calls. That is a floor, not a typical case.
- **What changed.**
  - `python ops/startup.py` does the start-up in one call and prints only STATE's NOW block, standing rules,
    Waiting on Jacob and Where things are: ~3k tokens.
  - STATE.md gained a NOW block, which every hand-off rewrites.
  - CLAUDE.md carries a brief template: TASK, DONE, DECIDED, READ ONLY (`path:lines`), FACTS, RULES THAT BITE,
    NEXT STEP, CLOCK. The context guard's hand-off text asks for it.
  - Projected: +30–35k over ~8 calls per hand-off. Not measured yet.
  - The 300k threshold stays until a re-run about Nov 4 shows the lean hand-offs are real.

## 2026-10-21 (Wed) 09:36 ET — the fresh-chat rule gets a meter (infra; CHARTER: speed)
- **What happened.** Jacob asked for the hand-off to be enforced in code, with the threshold measured, not
  guessed. I measured every laptop chat in this project: 9 chats, 1,378 API calls. Claude Code's own docs
  supplied the facts: a 1M window, auto-compact near 967k, cache reads at 0.05× input, and plan weighting
  not documented.
- **What it taught.**
  - Cache reads are 97% of all tokens, so a call's cost is set by the context it re-reads. A call at 650k
    costs ~4× one at 125k.
  - A fresh chat is not free. It takes 22 calls and +110k before its first edit, against 4 calls and +8k for
    a new task in an old chat.
  - Trading those off, the best threshold is 327–377k with today's hand-offs, and 185–230k if hand-offs
    were lean. **300k is never more than 16% from the best**; the old "50%" (500k) is up to 59% off.
  - The chats actually ran to 490–705k, because "about 50%" had no meter.
  - Uncomfortable: if the meter is price-weighted, a 300k rule would not have saved Oct 19's session limit.
    The volume of work and the costly hand-off drove it as much as length did.
- **What changed.**
  - `ops/hooks/context_guard.py` runs on every prompt and tool call. It warns at 250k, says hand off at 300k,
    and lowers the bar to 200k before the 09:15 and 14:30 ET windows. It never blocks, and stays silent in
    the cloud routines.
  - CLAUDE.md now names the hook and the 300k threshold.
  - The study is reproducible: `ops/token_study.py`.
  - Next: make hand-offs lean (briefs that carry files and decisions, a shorter start-up read), then
    re-measure.

## 2026-10-20 (Tue) early ET — the first two PASS events lost T2 to a fallback that was never a fallback (RQ5)

- **What happened:** ABT and SPCX, Season A's first PASS events, lost T2.
  - A "last resort" path in Actions fired minutes after the gate, not on the entry morning.
  - It spent all three of T2's attempts on a token that is refused, which left the working cloud path nothing to do.
- **Two lessons:**
  - **A fallback that runs first is not a fallback.** `hour >= 11` read as "the morning" but meant "any time after
    7 a.m.".
  - **A refusal that is about the account must not count as a model failure.** The protocol's attempt cap was built
    for bad replies. It cannot be changed mid-season, because `t2_stage2.py` is the protocol's hash, so the fix
    sits outside it: the workflow no longer attempts at all while the token is refused.
- **Honest cost:** two events of T2 calibration data. The shadow that re-runs the same model said NO_BUY 0.50 on ABT,
  a coin flip. The incident file states that before the outcome exists.
- **Also overnight:** a second DST trap. Yahoo's upcoming after-close stamps carry the summer offset, so they read
  15:00 in November, and the gate counted that as a disagreement. It would have failed most of the peak from Oct 30.
  It is fixed and frozen as a clarification, with the gate's code now hash-locked. With it and yesterday's four
  date-finder fixes, the peak went from 11% to 40% confirmed.
- **And a cost I caused:** this laptop session's heavy use spent the shared 5-hour allowance. The routine's 10:45 ET
  push on 10-19 was refused, so that day's paper window never started from it. In season, the laptop must stay
  light.

## 2026-10-19 (Mon) late morning ET — the date-finder was blind to its own release format (power, RQ1)

- **What I expected:** the gap was announcements arriving late. **What I found:** code was misreading announcements
  it already had.
  - In a read-only recall audit of 10 random peak names, 3 had a company date code missed.
  - Reading 13 urgent names by hand showed four separate defects. Each one cost confirmations for days:
    1. a release's own dateline counted as a second date;
    2. an unrecognised wire format (ACCESS Newswire);
    3. "US" without full stops;
    4. an after-close release plus a next-morning call read as "ambiguous".
- **All four fixed with tests from the real sentences**, re-run live, and 35 names confirmed. Season A went from 80
  confirmed or frozen events to 115.
- **The uncomfortable part:** the peak is still dark. 16 of 152 Oct 31–Nov 6 names are confirmed.
  - 50 PENDING names have a company date and session that code found, but no second source agrees yet.
  - 132 show nothing on the feed code reads.
  - That is where Season A's power now sits, and the next session starts there.
- **Lesson: measure recall, not just precision.** Code's rules were built never to confirm a wrong date. Nothing
  measured how many right dates it threw away. A 10-name hand audit found it in an hour. It should run every
  session until the peak passes.

## 2026-10-19 (Mon) morning ET — three silent failures, and a plan built around power (RQ1–RQ6, Gate 1)

- **The Actions AI step has been refused every night since Oct 15**: "Your organization has disabled Claude
  subscription access for Claude Code". The job exits green and health never looked inside the runlog. Three
  nights of PENDING re-checks never happened.
  - **Lesson: a green job is not a working step.** The alarm must read what the step produced, not the job's
    colour.
- **A dead runner looks alive.** On Fri, GitHub's "hosted runner lost communication" killed the long account's
  window job. The step stayed "in progress" ~40 minutes. NOC's second long open sat live 46 minutes against a
  15-minute rule. The coverage alarm built on Oct 15 trusts "in progress", so it could not see this.
  - The fix should check the broker, not the commit stream. The reviewer showed healthy ledger commits cluster
    ~18 minutes apart, so my first "8 minutes without a commit" idea would have alarmed all day.
- **Ubuntu 26 retired as a risk.** GitHub moves `ubuntu-latest` there from today. A probe (`runner-probe.yml`) ran
  our full setup on 26.04: Python 3.11.17, check.py PASS, 262 tests pass.
- **The power finding.**
  - Season A's first four gates all failed `wide_spread`, so there is no T2 decision yet. Only RTX was a near-miss;
    DPZ and VICR would also fail open interest.
  - More urgent: **238 of 318 names have no confirmed date.** Confirmed names were announced a median 21 days ahead
    (n = 80, p10 14), yet only 9 of the Nov 3–6 names are confirmed. That is a detection gap in our date-finding,
    not company behaviour, and it gates every track at the peak.
- **The plan** (STATE.md, top) puts date detection first. Next: the T2 deadline owned by a person and a time, three
  health alarms, and D016, a counts-only gate audit frozen before any NOC/RTX/VICR paper P&L is read.
  - A Sonnet review changed ten things: the T2 deadline owner, the heartbeat design, the audit's computable scope
    and its leak-safe sequence, thresholds tied to H-T2C's real minimum, earlier confirmation checkpoints, DST and
    margin numbers, and expectations committed before Tuesday's first v3 closes.
- **Consolidation:** STATE.md went from 1,442 to 417 lines. Everything before 2026-10-14 moved verbatim to
  `ops/state_history/`, checked character for character. A new session can now read it in full, as CLAUDE.md
  requires.

## 2026-10-16 (Fri) evening ET — the paper report's promised views, and what free data can say about a paper fill (RQ6, RQ1)

- **What:** the views promised on 10-14 and found missing on 10-15 now exist and are frozen
  (`registry/D011_report_views_v1.md`, `pipeline/paper_options_report_v2.py`). They sit beside the frozen report,
  which is byte-identical:
  - every P&L figure at the fill, the mid, halfway and the far side;
  - all trades, v3 only, and without DPZ;
  - fill rate as an outcome, read from order records only;
  - the open-fill trigger's counts;
  - each order against real exchange prints.
- **The probe: what free data can and cannot say.**
  - Alpaca's historical options bars and trades answer on the free plan, also for an expired contract.
  - There is no historical quotes endpoint. **What the real quote was while a paper order sat unfilled can never be
    checked after the fact.** Only trades can.
- **The first six real opening fills** (descriptive, one day):
  - Every one filled 3 to 56 cents BETTER than its limit, the indicative far side. The concession is a ceiling, not a
    cost, as v3 §2 guessed.
  - But every one paid 91–99% of the half-spread. **The mid column will flatter every result; read halfway and the
    far side.**
- **DPZ's failed exit, against real prints** (one trade, descriptive):
  - In 19 of its unfilled closes, 29 of the 30 legs that traded while the order was live printed at or through our
    recorded far side.
  - No close had prints on all four legs at once, so whether the whole order was marketable cannot be said.
  - It suggests the per-leg prices were not the obstacle. That fits the zero-bid-wing / multi-leg reading of the
    incident better than "the indicative prices were unmarketable". It is not proof: trades are not quotes, and n
    is 1 trade.
- **Real prints are thin.** In the dry pass (run 38987703855), 4 of the options account's 16 filled legs had a real
  trade within 15 minutes of the fill, and 1 within 60 seconds. "Missing" will be the common, honest answer.
- **Seen in passing:** the long NOC open's second attempt stayed live 46 minutes before its cancel (the rule says
  15). It still did not fill at the indicative ask sum.
- **What the review taught** (Sonnet, two passes, both SHIP WITH FIXES):
  - **A schedule written in UTC moves with the clocks.** My "16:45 ET" evening run would have fired at 15:45 EST,
    inside the paper window, from Nov 2. It is now 16:50 EST / 17:50 EDT, plus a guard that refuses to commit
    14:00–16:05 ET.
  - **One run stamps every send with the same time**, so "the first 6" is a tie more often than not. The honest
    order is the one the frozen code really sent in, which is the ledger order. When the cut falls in a tie, the
    report also shows the range over every admissible choice.
  - **"Give up after 3 days" must not swallow an account problem.** Only 400, 404 and 422 are ever stored as a
    refusal. A 403 ("OPRA agreement is not signed") keeps the run red, because it is about the account, not the
    contract.
  - **Lesson: a write-once store makes every "not yet" permanent.** Wait until the data has settled (12 hours here)
    before writing, and store a refusal only when it is about the thing itself.

## 2026-10-15 (Thu) late morning ET — alarms for an unworked paper window and for a ledger that disagrees with the broker (ops, RQ6)

- **What:** two code-only checks in `health.py`.
  - One asks the Actions API whether a window job is really running through the afternoon window.
  - The other reconciles both Alpaca paper accounts, position by position and open order by open order, against
    the ledgers.
  - The workflow now also runs on the routine push, so a health run lands at 14:45 ET. A cron alarm about crons
    being late would itself be late.
- **What the record showed when replayed:**
  - 10-14 reads RED at 14:46: nothing had worked the window since 14:27.
  - It reads AMBER from 15:20, once the frozen paper-options runs landed (14:46, 14:52, 15:16, 15:46).
  - The frozen workflow's own `*/10` cron fired once in the window. Almost all its runs come from S2 completions, and
    while a window job holds the group they are cancelled pending (both of today's were).
- **Found while reading the frozen code:** paper.py's T0 share trades use the same Alpaca account as the
  butterflies. A reconciliation against `options_ledger.json` alone would have raised RED on the first share fill.
  The check reads `ledger.json` too.
- **What the review taught** (Sonnet, SHIP WITH FIXES):
  - My lag excuse ("a live ledger order on the symbol explains the mismatch") had no age limit. A ledger that
    stopped being refreshed would have hidden every mismatch forever, which is exactly what the check exists to
    catch. Now it is information for 30 minutes, AMBER to 24 h, then RED.
  - "Ended within 3 minutes of now" counted a 2-second morning-mode step at 14:44 as afternoon coverage at the one
    run that matters. Inside the window only a running step counts now.
  - **Lesson: every excuse in an alarm needs an expiry, and every "close enough" needs a test at the run that
    decides.**
- **Verified live** (dry dispatch, run 38762134094, 11:38 ET):
  - Alpaca returns an open multi-leg order as one top-level `mleg` order with its legs nested. Shorts come back
    as `qty -1, side short`.
  - Both accounts match their ledgers: the options account holds DPZ's 4 legs plus close r12, and the long account
    is flat.
  - The shape is now a test fixture.

## 2026-10-15 (Thu) evening ET — the push runner held; the first C1 grade needed a hand (ops, RQ1)

- **The runner worked as designed, including the part the review warned about.**
  - The options account's 10:45 start waited behind this morning's hand dispatch. It was cancelled at 11:46 by a
    later waiting run. The 11:45 start then ran 12:00–15:56.
  - So a waiting start really is disposable. Coverage came from the next push, not from the queue.
  - The long account ran the whole day from the 10:45 push.
  - Every `paper-window.yml` cron start again landed after the window, or was cancelled while waiting.
- **The laptop is not a backup.** The 12:05 ET background dispatch died with exit 4 after its sleep and sent
  nothing. It wasn't needed, but anything that must happen belongs in Actions or a cloud routine.
- **C1's first grade also waited on a cron.** The 18:50 ET grade fire had not started by 20:35, so it was
  dispatched by hand.
  - Unlike the paper exits, nothing is lost by a late grade. Prices come from Alpaca history and are written once
    per R, and the SEC timing check has 10 days of patience.
  - So no fix, only a note. A push-started grade would mean editing a D015-hashed workflow, for no gain in truth.
- **The first C1 day, blind counts only:** 12 events reacted on Oct 15. 4 were voided by rule (3 foreign filers,
  1 SEC timing contradicting the stated session), 8 were graded, and 2 flagged C1.
  - One date says nothing. The cluster is the date, and look 1 needs about 27 of them.
- **DPZ is heading for assignment.** 19 v1 closes at the indicative natural, none filled. The stock closed at
  303.09 against the 310 short put. The rule's answer, settled at intrinsic and labelled simulated, is fixed. The
  account's answer is 100 shares that no code will sell, and the new positions check is built to catch exactly
  that.

## 2026-10-15 (Thu) morning ET — the paper runner's cron never landed; it now rides the routine push (ops, Gate 1)

- **What happened:** the window runner built yesterday for the DPZ incident starts only from GitHub's cron.
  - Yesterday's four afternoon fires all began after the window had closed, at 21:00–22:18 UTC against a 19:56 UTC
    end.
  - This morning's two fires had not started by 10:23 ET.
  - So the fix for "the cron drops fires" had itself been relying on the cron. CLAUDE.md already says never rely on
    a cron landing. I wrote that rule yesterday and still built a cron-only runner.
- **What changed:** a second workflow starts the same frozen runner from the cloud routine's pushes. Those land
  within seconds, and the S2 gate and C1 capture already depend on them. The frozen runner file is untouched;
  `D011_implementation_v4_addendum1.md` registers the new one.
- **What the review taught:** GitHub keeps one *pending* run per concurrency group, and a newer one cancels it. Each
  push also triggers the frozen paper workflows about 17 s later, through `workflow_run` after the S2 precheck. A
  push-started runner that had to wait would be cancelled by its own push's side effect.
  - Yesterday's logs show it. Frozen run 38592117073 queued at 15:45:22Z behind a hand dispatch. It was cancelled
    at 15:47:02Z, one second after a newer run queued behind it.
  - The fix is a 150 s settle job, so the runner queues after that short run instead.
  - **Lesson: "queue behind it" is not safe in Actions. Two waiters in a group means one is cancelled.**
- **DPZ:** the 9th v1 close went out at 10:24 ET at a 10.73 natural debit, against 15.60 yesterday. Expiry is
  tomorrow.
- **Next test:** Fri Oct 16 is the first day the runner has to work unattended. That day has DPZ's last resend,
  the first three Season A gates and the first v3 opens.

## 2026-10-14 (Wed) midday ET — D015: C1 goes live as a market-wide confirmatory shadow (RQ1, Gate 1)

- **What:** D014's one TRAIN survivor, C1 (fade a pre-market gap bigger than the options-implied move), failed
  VALIDATION (−0.90%, n 62, Holm p 0.48). Rule 6 leaves it a hunch until it holds on fresh data. D015 v1 is that
  test, frozen at 12:09 ET (`bd67722`), before the first reaction session it counts (Oct 15).
- **The power decision:** C1 flags ~15% of events with an implied move.
  - On the ~300 gated events a season that is ~35 C1 events a season, and ~35% power even pooled with Season B.
  - On the market-wide SH-M set (~1,300 a season) it is ~130 a season, and ~85% power pooled.
  - So the live implied move is captured for every SH-M event, not read from the S2 gate.
- **The instrument almost went wrong, and the review caught it.** My first draft took D010's rule text
  literally: the first expiry after R. But D010's DoltHub chains held mostly monthlies. I checked: 82% of D014's
  868 implied moves used a third-Friday expiry, a median 15 days out.
  - Live yfinance chains carry weeklies. For AAPL today, the weekly 1 day after R prices 2.5% and the monthly
    6.6%.
  - The draft would have tripled C1's rate among large caps only, and diluted the test with D014's complement
    (mean ≈ 0).
  - **Lesson: replicate the instrument's behaviour, not its rule text.** The primary is now the monthly; the
    weekly is a secondary.
- **Other review fixes (Opus 5.5, FREEZE WITH FIXES, 11 findings, all applied):**
  - **Blind until a look.** Nightly reports would have printed "CONFIRMED" on interim data. Now no C1 return is
    shown before 2026-12-07, and each look is written once.
  - **Student t with G − 1 df.** With ~27 dates, the normal is too liberal at p < 0.005.
  - **SEC failures can't block a date.** One failing lookup could have frozen a whole reaction date (the
    clustering unit). Now it waits 10 days, then voids that event only.
  - **The sample-defining code is hash-checked.** A D009-side edit to `sh_m_events` could have silently changed
    D015's sample. `check.py` now verifies `shadow.py`, `sessions.py`, `common.py` and `s1_screen.py` too.
  - **No escape hatch.** "If Season B doesn't run, the final look is Season A at 0.045" was an optional-stopping
    door; it is closed.
- **Dry capture (real chains, 12:08 ET):** 10 of 12 due names gave an implied move in 2 s. HOMB lists no puts;
  WIT's call bid is zero. Today's capture job was dispatched at 12:09 and waits for 15:25.
- **Ops lessons carried over:** one job waits inside the window (cron is best-effort); health is AMBER on a
  missing capture; `check.py` fails on an edited capture; a failed push fails the job.
- **Probe of the Alpaca path (R = Oct 13, before registration, coverage only):** clean.
  - 9 events, 45 requests, 0 failures, auction opens and closes, every quote. FBK has no pre-market trade (void).
  - Surprise: every event's SEC timing was `unverified`. JPM, GS and WFC file their 2.02 8-K at 10:28–11:32 ET,
    hours after their ~07:00 wire release.
  - D014's allowlist history had 1 such case in 3,536, so its "floor at the acceptance minute" never bit. Live,
    flooring at a 10:30 filing would void every big bank. The registered rule floors only on an acceptance
    inside the session window, which is the sensible reading.
  - **Lesson: the market-wide set has filing habits the allowlist never showed.** Watch the `unverified` share.

## 2026-10-14 (Wed) — the DPZ exit that didn't happen, scored blind; D011 v3; the open's cost is the open

- **Expectations first.** Before reading Oct 14's ledger I wrote and committed what I expected
  (`ops/incidents/2026-10-13_DPZ_exit.md`, commit `27c1109` at 10:57 ET): a fill by the close with
  P = 0.65, and P&L +1.0 per unit (80% range −2 to +4).
- **What happened:** DPZ fell another 4% on day 2. The retry's natural implied **−7.7 per unit**, against
  +0.32 on time (natural) or +3.29 (mid). **Outside my 80% range.**
  - My error: I priced a missed exit as a day of time decay. It is an unhedged directional position after
    the event.
  - Three closes at v1's natural have now gone unfilled (14:46 Oct 13; 10:45 and 11:07 Oct 14).
- **Root causes:**
  1. **GitHub's cron dropped the fires** that should have resent the close.
  2. **v1 prices from Alpaca's free "indicative" feed**, which Alpaca says is randomized. Paper fills are
     judged against real quotes, so a limit at the indicative natural may never be marketable.
  3. **The alarm and the accounting were blind:** health ran outside the exit window, and `exit_late` is set
     at send, not at fill.
- **Fixes:**
  - `paper-window.yml` runs the frozen code every 2 minutes through the window. Tested live today: the
    morning window resent DPZ's close at 11:07.
  - Health raises EXIT NOT FILLED as RED at 15:15–15:55 ET.
  - D011 exit audit v1 (descriptive): the on-time counterfactual next to every trade.
  - **D011 v3** (closes only, Season A trades from the first gate): drop no-bid long legs, a concession walk
    from 0% to 25%, a 2-minute cancel, a simple order when one leg is left, and a 15:10 cut-off on expiry day.
    Opus review: FREEZE WITH FIXES, all applied (a missing quote had been read as a worthless leg).
  - A background agent searched GitHub and the web. The evidence and the borrowed ideas are in the incident
    file.
- **D014 control days (descriptive, DRIVE's question):** is the open's cost the print or the open?
  - **Mostly the open.** The first post-open quote's median half-spread is 0.52% on ordinary days and 0.45%
    on print days (0.75% in mid-caps on both).
  - What the print adds is movement: the first minute's VWAP sits a median 0.25% from the official open on
    print days, against 0.03% on ordinary days.
  - By 09:35 the half-spread is 0.20% (ordinary) and 0.25% (print).
  - **For anyone trading at moomoo: never use a market order in the first minute, on any day.**
- **Lesson for the operator:** write the expectation before the outcome, every time. It turned a lost exit
  into a measured miss, and showed that my mental model of a failed exit was wrong.

## 2026-10-13 (Tue) afternoon ET — D014 v1/v2/v3 results: the first hour after the print (exploration)

- **Run cleanly:** 3,536 events, 15,715 requests, 0 failures. 2,885 had a pre-market gap of at least 1%
  (TRAIN 1,973 on 351 dates, VALIDATION 912 on 132 dates). 222 were void, all `no_premarket`.
- **Unconditional: no continuation and no reversal.** At 5 minutes the mean is −0.13% (t −1.9); at 30
  minutes −0.02%; at the close +0.16% (t 1.2). By minute 5 the median stock has made 87% of its whole
  reaction-day move (vs the prior close). The literature's "it lands within minutes" holds here.
- **One TRAIN signal, which failed validation: fade a gap bigger than the options-implied move (C1).**
  - TRAIN: −2.0% at every horizon, t −4.7 to −3.2, n 70 on 45 dates.
  - VALIDATION: the same sign, −0.7% to −0.9%, but n 62 on 36 dates, Holm p 0.31–0.48. **Failed
    validation.**
  - **It is thin:** the implied move exists for only 868 events (D010's straddle coverage).
- **C6** (heavy pre-market volume, fade at 5 minutes): failed.
- **v2** (washout vs run-up, sector week): nothing. Every |t| < 2. The washout and run-up groups have only
  about 75 events each.
- **v3, the retail entry: every survivor is auction-only.**
  - A market order at the open meets a median half-spread of **0.45%** on the first quote after the
    cross, about twice the 0.25% at 09:35.
  - Pricing the entry at the first minute's VWAP plus that half-spread costs about **0.8%** against the
    auction.
  - The first minute's plain VWAP sits within about 0.05% of the auction. That points to the moomoo VWAP
    algo, or a limit order, not a market order.
  - **Post-hoc, descriptive, not a test:** C1's fade at plain VWAP: TRAIN +1.2% to +1.7% net (t 2.9–3.6),
    VALIDATION +0.2% to +0.7% (t 0.5–1.0).
- **What it taught:**
  1. The post-print open is efficient on average in this universe.
  2. Only the extreme overshoot (beyond what options priced) shows a reversal, and it is too rare to
     confirm on one year.
  3. For a retail account, **how** you enter matters more than the signal: a market order at 09:30 gives
     away about 0.8%.
- **Next:** register C1 ("fade a pre-market gap beyond the implied move") as a live, history-graded
  shadow on Season A + B before Season A's first reaction day. Entry is the auction and the first-minute
  VWAP; Alpaca history grades it after the fact, so no live orders are needed. It needs a live implied
  move (the S2 gate's straddle quotes).

## 2026-10-13 (Tue) late morning — D014: after the print, not before (new question; CHARTER negative-knowledge)

- **Origin:** Jacob, through a note from the DRIVE portfolio chat (ideas and public papers only, no holdings,
  so rule 9 holds; no DRIVE file read). His question: when a stock spikes or flushes after results, is it
  justified, and can the first half hour capture it? Our primary exit A *is* the post-print open, so this
  starts exactly where the experiment's measurement stops.
- **Data probe (non-event days only):** the Alpaca free plan serves SIP 1-minute bars back to 2022-09,
  pre-market included, NBBO quotes and the official opening and closing auction prints. Free, and enough for
  all 3,536 D006 history events.
- **D014 frozen (`b5e081b`) before any reaction-day price was pulled.** 42 tests on TRAIN (2022-09 → 2025-08):
  continuation vs reversal at 5, 10, 30 and 60 minutes and the close, unconditional and inside six groups.
  The groups are big gap vs the implied move, surprise disagreeing with the gap, market against, bad news,
  mid-cap and high pre-market attention. The bar is |t| > 3 and BH q < 0.10, then one Holm-corrected look at
  VALIDATION (2025-09 → 2026-09), net of spreads.
- **The review's best catch (Opus, pre-freeze):** I had defined the gap's direction from the opening
  auction price, which is also the entry. That can't be known when a market-on-open order must be sent, and
  noise in that one price would push the result toward "reversal" by construction, a fake fade. The signal
  now comes from pre-market trades before 09:27, after the release's SEC acceptance time.
- **Other fixes:**
  - date-only `end=` parameters would have silently dropped the reaction day's auctions
  - a 1e-6 split tolerance would have voided rounding noise
  - delayed NYSE openings now blank the horizons before the open
  - a failed request no longer poisons a month for good
  - exits use quote mids, avoiding bid-ask bounce
- **Rule 10 note:** a repo-wide grep surfaced two fenced-archive lines about "intraday alpha". They were
  excluded and shaped nothing. Disclosed in D014 §0.
- **Prior (stated before the result):** the large-cap literature says most of the reaction lands within
  minutes. If there is anything, I expect it in mid-caps and big gaps, and I expect costs at the open to
  eat a lot of it. A clean "nothing capturable" is a real result.

## 2026-10-13 (Tue) morning — making failure loud (health check) and the report frozen

- **The health check exists because of Friday.** The billing outage stopped every job for hours, and
  nothing said so. It is now a free code-only job that reads the record and emails Jacob (via one GitHub
  issue) only when an event or a T2 decision is being lost, or is about to be.
- **The review's best catch:** "T2 missing" only after the deadline is an obituary, not an alarm. It now
  fires "AT RISK" within 14 hours of the deadline, while the loss can still be prevented.
- **Second catch:** a committed status file could stand in for a crashed run, a false GREEN.
- **Process lesson:** two invalid workflow files in one day, both from escaping layers (Python inside bash
  heredocs). GitHub fails such a file silently. A test now parses every workflow.

## 2026-10-13 (Tue) — Max plan: capacity spent on the core asset (RQ5, CHARTER I2)

- Jacob moved to Max and asked that it be used well. The constraint that had shaped T2 was capacity, which
  is why D004 v4 chose Sonnet over Opus and deferred the ensemble. **T2 itself cannot switch models without
  ending its pooled A + B record**, so the capacity went to shadows: Opus on the identical dossier, a second
  Sonnet run (T2's test–retest), and their ensemble.
- **The probe mattered:** Fable 5.1 is refused without paid credits, which a spec written from memory would
  have missed.
- **The review mattered more:** the real risk to T2 was never shared code. It was a shared *allowance*. A
  peak night of Opus shadows could exhaust the weekly cap and leave T2 MISSING the next morning, as with APLD
  on 10-07. Now there is a code budget, not "an operator may pause".
- Smaller catches: a silent model substitution, a hash lock nothing enforced, and a shadow file able to fail
  the health check that gates T2's own queue.

## 2026-10-13 — D010 v2: a units bug hiding in "unadjusted" prices (RQ1, RQ4)

- **The surprise was the size.** Liquid short straddles held to expiry came out at −12.9% of spot, and the
  long side at +12.2%: impossible magnitudes.
  - Cause: yfinance `auto_adjust=False` still rewrites history for later splits and spin-offs. KLAC's $690
    strike sat against a "close" of $69.
  - v1 survived because it only used ratios of option quotes. Any formula mixing a stock price level with
    a strike breaks.
- **Lesson: "unadjusted" from a vendor is a claim to verify. Before trusting any price-level formula,
  check strike / spot ≈ 1 on every row.** 16 of 1,249 events failed that check.
- **Handling:** v2 is reported exactly as frozen (Y invalid), plus a disclosed outcome-free correction. Not
  a silent fix.
- **Findings:**
  - Holding to expiry doesn't save the short side.
  - Buyers keep losing.
  - The famous call–put IV spread adds little as a selector.
  - The one "finding" under the frozen rule (Z4) is mostly the average earnings-session premium. The
    frozen rule can certify a test whose interpretation is still mundane.

## 2026-10-12 (Mon) afternoon — the size gate earned its keep (RQ1, SH-RU)

- **The registered primary test failed its own pre-check.** With 20-session windows and a season of ~30
  portfolio sessions, a block bootstrap with block 20 has only 2–3 blocks. Under a true null it rejects
  11–16% of the time at a nominal 5%.
- The rule (written 10-07) said: check the size on synthetic data first, and switch to KV fixed-b if it
  fails. Fixed-b's size is 4–5%. **Without the gate, SH-RU would have run at roughly 2.5× its stated false-
  positive rate.**
- **Lesson:** a resampling test on short overlapping series needs its size measured, not assumed. Write
  the fallback into the rule before any data exists.
- **Second lesson, smaller:** the registered workflow failed on its first CI run, a bash `-e` trap on a
  season that does not exist yet. A test of the workflow before hashing it would have caught it. It is
  now fixed by an addendum and a disabled original; nothing had run.
- An independent review caught that a failed price download would have permanently voided an event. That
  failure is correlated with delisting, so it would have been a survivorship bias. It is fixed before
  registration.

## 2026-10-12 (Mon) — D010: the straddle's edge is the size of its spread (RQ4)

- **The headline was misleading until I asked why the costs were so large.** Both sides lose 3–4% of spot
  after costs. But DoltHub's end-of-day legs have a median spread of 21–31% of the option price, against
  ~4% at our live 14:30 gates. D010 traded every name, including ones our gate refuses.
- **Restricted to the gate's ≤ 10% spread rule:**
  - selling earns +1.13% at mid (t 3.44) and ~0 after paying the spread twice
  - buying loses 2.2% (t −6.4)
  - The cut was chosen after looking, so it is a candidate, now **D012 H-XT** for Season A + B.
- **Lesson: read a backtest's cost line against live quotes before reading its verdict.** A cost
  assumption can be the whole result.
- **What it changes:** execution is the strategy. SH-X holding to expiry skips the second spread, and
  D011's real fills will show what is really paid. The buy side looks structurally bad.

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
