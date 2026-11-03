# Committee assessment of PRE's answers: round 1 of 1

> Assesses `PRE_QA_answers.md` (`4fa6d03`, `a6e8cf8`) against `PRE_QA.md` Part D, which fixed in advance which
> answers would move the decision. The claims that matter were re-checked against git and the r2 output.
> **Outcome: the recommendation stands, B · REFRAME. Confidence rises from ~80% to ~85%. The rating stays 2.5 / 10.**
> One factual correction to `REPORT.md` is accepted (P0's mechanism).

## Verdict on the answers

PRE answered every question honestly and with citations. It held its own firewall (D017 §4, rules 9 and 10) and
refused to over-reach where it lacked data. Its concessions are the evidence:
- history's +0.65% is a ceiling, not an estimate;
- there is no mechanism evidence;
- the execution criterion already fails;
- Gate 2 cannot be met on time.

## Answer by answer

| # | PRE's answer | committee check | effect on the decision |
|---|---|---|---|
| P0 | CONFIRMED; fixed `stage1.py` (`4383102`, `a6f7cc6`, tested); r2 on the full cut matches the committee exactly | **verified**: SH-W n 104, net −1.50%, [−3.28%, +0.27%]; SH-M n 696, raw −0.18%, net [−0.92%, +0.17%]; pending 0 | strengthens it. **Correction accepted:** `c2dc357` was the newest grade on `main` at the run (the next, `4d9affc`, is Mon 18:16 ET). The defect was `stage1.py` dropping ungraded events silently, not a stale pull. `REPORT.md` concern 11 is reworded |
| P1 | cannot re-run with free data; the oldest events (most survivor-filtered) show the smallest premium: +0.25% vs +1.07% / +1.13% | logic accepted as **weak** evidence. The age split is confounded with regime, as PRE says. It also cuts the other way: the period most exposed to survivorship earns +0.25% raw, about +0.05% net | neutral. Part D's "bias < 0.2 pts" bar is not met, and neither is "bias near the full premium" |
| P2 | **concedes** +0.65% is an upper bound; no mechanism evidence | — | strengthens it |
| P3a | cannot answer until registered; daily closes are retrievable later, so nothing is lost by waiting | accepted. This makes §12.3 cheap: a new script beside the hash-listed `shadow.py` | none |
| P3b | **confirms** +91 bp round trip (sells +105 bp, 20 of 23 adverse); D008 §3 criterion 4 (≤ 15 bp) already fails | matches the committee recompute | strengthens it |
| P4 | gated S0 reaches 250 events only in **May–Aug 2027**; **D008 Gate 2 #1 cannot be met in Mar 2027**; RESEARCH_PLAN ("T0 or T0-wide") and D008 (H-S0) disagree | new to the committee and material: the only registered path to money is closed for at least two more seasons | strengthens it. The market-wide SH-M, not gated S0, is the only sample that can answer in time, as §12 already chose |
| P5 | the shadow T2 tracks, paper options, C1 and D018 serve **no** Gate 2 criterion; laptop chats are the largest draw | agrees with §12's stop list | strengthens it |
| P6 | no weekly ledger; ~$0.41 API-equivalent per gated event for the T2 tracks; laptop chats unattributed | accepted; data gap disclosed | none |
| P7 | Layer 1 not recorded; not a deliberate choice; capture costs $0 | accepted | adds one keep item (below) |
| P8, P9 | held to Gate 1; P9 counts: 32 PASS of 143 with a chain (22.4%); weeklies pass 38%, monthlies 10% | accepted | none |
| P10 | no predictor has evidence; the one item is Layer-1 actuals, which moves no Gate 2 criterion | accepted | none |

## Where the evidence now stands against the kill bars

- **Gate 1 bar (fixed in `REPORT.md` §12 before r2 was read):** SH-M raw mean's upper 95% bound, t with clusters − 1
  df, ≥ +0.50%.
- **On r2 (14 sessions):** raw −0.18%, SE 0.28% → upper bound about **+0.42%** (t, 13 df). That is already below the
  bar.
- **What is left:** Season A's remaining sessions (the peak, Nov 2–20) decide it at Gate 1. The likeliest outcome is
  termination in December. The monitor is code-only and nearly free, so stopping it now would discard the season's
  largest weeks for no saving. That is the case for B over A today.
- **The deck's funding row:** on r2, SH-W's upper bound (+0.27%) is below +0.65%. Only the session count (9 of 10)
  keeps D017 §5 at "fund to Gate 1" rather than "no new money". The committee's recommendation does not rest on that
  row.

## Changes to the plan from this round

1. **Add to §12's keep list:** a Layer-1 capture script, $0 and code-only: the reported EPS and surprise from
   `get_earnings_dates()` after each print, and revenue actuals from EDGAR. It diagnoses the reaction layer at Gate 1.
2. **Settle the D008 / RESEARCH_PLAN conflict before Season B** (P4) by naming SH-M as the premium's primary read. If
   Jacob approves §12, this is part of the same new version.
3. **Still owed by PRE** (confirmed in its answers, not fixed): the health counter ("T2 missing 0 of 32") and the P6 cost
   line reading `decision.json` instead of `t2.json`.

## What Jacob decides now

The §12 stops (paper options, the shadow T2 tracks, D018, main T2 after Season A) need his word. PRE has correctly
not acted on them. Nothing else is waiting.
