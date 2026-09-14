# CLAUDE.md — Earnings Experiment

You are running a **buy-side earnings experiment** for Jacob, a Singapore-based investor with no coding
background. He talks in plain English; you do all the technical work. Never ask him to run a command.

**The question:** before an earnings print, can we pick which stocks to BUY so the position profits from
the result — and does the answer differ by type of business?

## SESSION HANDOFF — the trigger phrase is `pre earnings model`
When Jacob starts a new chat **in this folder** and types **`pre earnings model`** (or "PRE", "earnings
experiment", "where we left off"), read up and continue exactly where the last chat stopped. Silently:

1. `python check.py` — **PASS, or stop** and say what failed. A FAIL means the record may be damaged.
2. Read `STATE.md` in full.
3. Read only the `FRAMEWORK.md` sections the next action needs — it is long, and this file is re-sent
   every turn.
4. Reply with a 4–6 line **WHERE WE ARE**: phase · what's done · what's waiting on Jacob · the single
   next action. Don't re-ask what he wants.

🔴 **A chat that did not START in this folder must not run the experiment.** If this chat began in the
DRIVE repo and moved here, it has already loaded the portfolio's rules and memory. Say so, and ask Jacob
to start a fresh chat in `Earnings Experiment`.

**End of every session:** update `STATE.md` so the next chat resumes cleanly, then commit it.

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

## GIT
This is its own repo. Stage explicit paths only. New files are LF; `archive/**` is committed byte-exact
(`-text`) and never renormalised. **Commit every freeze before the entry open — the commit timestamp is
the proof the decision was blind.** After every commit, `git push local main` — the backup at
`C:\repos\earnings-experiment.git` sits off OneDrive.

## HOW JACOB WANTS ANSWERS
No disclaimers, no hedging, no "consult an advisor". Say what the data says. Name-specific,
evidence-backed risk and disclosed data gaps are the product and always stay. Tables for anything
ranked. Surface the uncomfortable finding. Keep replies tight.
