# JOURNAL — the lab notebook

> Dated observations: what happened, what it taught us, what changed. Newest first. This is where
> surprises, failures and hunches are written down *as they happen*, so nothing is reconstructed
> later from memory.
> - Not evidence: findings live in `analysis/` and graded outcomes in `outcomes/`.
> - Not rules: rules live in `registry/`.
> - Each entry says which research question (`RESEARCH_PLAN.md`, RQ1–RQ6) or gate it touches.

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
