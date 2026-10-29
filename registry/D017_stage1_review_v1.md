# D017 · Stage 1 funding review (interim, descriptive) · v1 — FROZEN 2026-10-29 (ET)

> Frozen **before any Season A outcome is read in a chat**. Jacob asked on 2026-10-29 for a Stage 1 review on
> **Tue 2026-11-03 (SGT)**: is this model useful, not redundant, and worth funding? This file fixes in advance
> what is computed, from which data, what each result is called, and what it may and may not decide.
> The commit timestamp is the proof. Plan and timeline: `ops/stage1_plan_2026-11.md`.

## 1. What Stage 1 can and cannot show — said before the data

- History's per-event Sharpe is **0.087** (D006). At n live events a real premium shows a t of about
  **0.087 × √n**: about 0.9 at n = 100 and 1.2 at n = 200. Gate 2 needs ~250 events and 40 sessions (D008).
- So **Stage 1 cannot prove the premium**, in either direction. Expect a small t even if the premium is real.
- It **can** show that the record is truthful, whether the live premium agrees with history so far, what
  the machine costs to run, and what has already been learned.
- No result here carries a verdict word. "Works" and "no effect" are forbidden (rule 7). Every figure is
  labelled **INTERIM**.

## 2. Data cut and how it is run

- **Sample:** every Season A event, gated or shadow, whose exit-A open falls on or before **Fri 2026-10-30**.
  Each is graded by code (`grade.py`, D005 implementation v3; shadow tracks by `shadow.py`).
- **Paper:** trades closed by Fri 2026-10-30, through `paper_options_report_v2.py --write`.
- **Code:** `pipeline/stage1.py`, written and **committed before its first run**. It is run once, after the
  weekly reset (Mon 2026-11-02 06:00 UTC), and its output is committed as `outcomes/reports/stage1_2026-10-30.md`.
  - It calls `report.run` and `shadow.report_`. Its only new statistic is §3's excess over SPY.
  - A bug fix after the first run is a new commit beside the first output. The first output is never replaced.

## 3. The six pillars — what each reports, and the words it may use

**P1 · Truthful record.**
- check.py PASS at the run; decisions frozen after their entry open (must be 0); VOID rate (< 5%).
- Also reported: missed windows and T2 missing (the CHARTER §6 health numbers).
- **PASS** = check.py PASS, 0 late freezes, VOID < 5%.
- A missed window or a missing T2 decision caused by the AI allowance or the refused Actions token is reported
  as a **capacity** finding (P6), not a truthfulness failure.

**P2 · The premium, live.** Primary read: **SH-W** (T0-wide: every allowlist event, gate or no gate; this is
RQ1's universe). Secondaries: gated S0 (H-S0's statistic) and SH-M (market-wide). Each read reports:
- n events and n entry sessions;
- the raw mean, the mean net of 0.20% round trip, and the win rate;
- the mean excess over SPY, i.e. the event return minus SPY's open-to-open return over the same entry → exit-A
  window, with SPY's daily opens from yfinance;
- a cluster-robust standard error by entry session, and a 95% interval (mean ± 1.96 SE).

The primary read gets exactly one of these words, on its net mean:

| word | condition |
|---|---|
| INSUFFICIENT | under 30 events or under 10 entry sessions |
| CONTRADICTS HISTORY | the upper 95% bound is below **+0.65%** (D006's net mean) |
| ALIVE | net mean > 0 **and** mean excess over SPY > 0 |
| NOT YET VISIBLE | anything else (consistent with history, not yet separable from noise) |

**P3 · Selection over buy-all.** On gated events, T1 and T2 against T0: the BUY count, the win rate and mean
return of BUYs against all, and the T2R / T2O / T2G decision agreement with T2. Exploratory (D005 v2). Under
30 BUYs or 10 sessions it is INSUFFICIENT.

**P4 · Execution.**
- Paper shares: the median absolute paper fill against the official open, in bp, and n.
- Paper F and L P&L at fill, mid, halfway and far, with and without DPZ.
- The open-fill trigger counts.

**P5 · Knowledge already banked.** D006, D007, D010 and D014 as closed (HYPOTHESES §3). No new computation.

**P6 · Cost and capacity.** The weekly allowance's path in Season A, the measured cost per T2 decision, the T2
decisions lost to limits or the token, and the tracks that compete for the allowance.

## 4. Never shown at Stage 1

- **C1 / H-C1:** blind until look 1 from 2026-12-07 (D015). Counts only.
- **H-T2C's slope b and any T2-confidence-vs-outcome view:** Gate 1 only (D005 v3, "When it is decided").
- Per-name outcome tables beyond what P2–P4 need. The deck shows aggregates.

## 5. The firewall — what the results may decide

- **They may inform Jacob's funding decision only**: continue, add capacity, or stop.
- **They never change** a registered test, a rule version, the Season B screen, universe or BUY rule (rules 5
  and 6; D005 v3). The pooled A + B tests keep their alpha: this look decides nothing about them.
- **D003 v5 is decided before the run, on counts only.** The D016 §5 rule picks **A4**. If Jacob has not said
  otherwise by the run, A4 is adopted by this file's default, and that is recorded before the run.

**What the evidence supports** (fixed now; the decision is Jacob's):

| P1 | P2 primary | the evidence supports |
|---|---|---|
| FAIL | any | **repair first**: no new money until the record is clean |
| PASS | CONTRADICTS HISTORY | **no new money**: finish Season A on current means and decide at Gate 1 |
| PASS | ALIVE, NOT YET VISIBLE or INSUFFICIENT | **fund to Gate 1 and Season B**: the record is sound and nothing contradicts the premium |

## 6. Global multiplicity view (HYPOTHESES idea A), registered here as a secondary

- At Gate 1 and Gate 2, beside each family's own verdict, report a Holm and a Benjamini–Hochberg adjustment
  across all 10 confirmatory tests of HYPOTHESES §1, one-sided α = 0.05.
- It is secondary: it never overturns a family's registered verdict. It is printed beside it so that a lone
  "pass" that would not survive the global view is visible.
- Registered before any outcome look, as idea A required.
