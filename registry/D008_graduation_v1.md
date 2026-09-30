# D008 · Graduation criteria — when real money may go in · v1 — FROZEN 2026-09-30 (ET)

> Frozen **before any Season A event exists** (the Season A screen is 2026-10-09). This sets what the
> live record must show before real money is used (RESEARCH_PLAN §6, Gate 2, March 2027).
> **Two numbers are Jacob's** — the real-money sleeve and its loss limit. They must be set in a D008 v2
> before the first live trade. Everything else here is fixed and never edited (rule 5).

## 1. The strategy under test

**S0, the premium harvest**, exactly as `pipeline/paper.py` trades it:
- **What:** buy every frozen PASS event (T0) at the entry open with a market-on-open order; sell at
  the exit-A open.
- **Sizing:** notional = equity × 0.5% ÷ the gate's implied move, capped at 10% of equity per name.
- **Paper:** from Season A as a shadow; formal from Season B.

Selection layers (a D007 survivor, T1, T2) may be **added to S0** only as registered at Gate 1, before
the Season B screen, and only if each passes its own Holm-corrected test (D005).

## 2. Hypothesis H-S0, registered now, so it is confirmatory from Season A

H-S0: **S0's mean exit-A raw return, net of 0.20% round trip, is greater than 0.**
- It comes from the D006 history: +0.85% raw, +0.65% net, clustered t 3.6.
- It is registered before any live event, so Season A counts as out of sample for it.
- **Test:** one-sided, the D005 wild cluster bootstrap by entry session.
- **Sample:** every graded PASS event of Seasons A and B pooled (the gated universe S0 trades).
- **Supporting evidence, not the test:** the same statistic on gated-out events is reported as a
  secondary.

## 3. Gate 2 — ALL must hold to put real money in

| # | criterion | measure |
|---|---|---|
| 1 | **Evidence** | H-S0 rejected at one-sided p < 0.05 on at least 250 graded events over at least 40 entry sessions, pooled A + B |
| 2 | **Stability** | the net mean is > 0 in at least one of A and B, and negative in neither beyond −1 standard error |
| 3 | **Consistency with history** | same sign as D006; the live net mean is not below −0.5% |
| 4 | **Execution** | at least 50 paper round trips; the median absolute difference between the paper fill and the official open (grade.py) is ≤ 15 bp; mean slippage is included in the net return |
| 5 | **Process** | missed windows = 0 and VOID < 5% in Season B; every paper trade traces to a freeze committed before its entry open |
| 6 | **Risk** | on the paper record, the worst drawdown of cumulative S0 P&L is within Jacob's loss limit (set in v2) scaled to the sleeve |
| 7 | **Layers** | any selection layer is included only if it passed its own confirmatory test; otherwise S0 alone |

**If Gate 2 fails:** no real money. The report says which criterion failed. The next step is decided at
Gate 2: another season of paper, the options route (RQ4), or the no-edge verdict.

## 4. Live money — the kill switch (applies from the first real trade)

Stop real trading, return to paper and report on **any** of:
- cumulative real P&L below its expectation by more than 2 standard deviations after 50 trades
- a real trade not traceable to a freeze made before its entry open
- two health numbers breached in one season
- the loss limit (v2) reached

Restarting needs a new Gate-2-style review.

## 5. Deliberately left open for v2 (Jacob)

- the real-money sleeve (amount)
- the maximum loss of the sleeve before the kill switch
- the broker for real orders (paper is Alpaca)
