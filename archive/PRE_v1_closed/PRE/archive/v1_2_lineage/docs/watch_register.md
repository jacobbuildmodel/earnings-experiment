# WATCH register — candidate rule changes (NOT canonical)

Rules here are drafted and code-complete but **OFF by default**. Each needs
2 independent, non-anomaly holdout confirmations + Jacob sign-off before its
default flips on (a LOGIC change under the outcome-equivalence rule). Flipping
the default is the only step that moves logged verdicts.

---

## [W1] Fundamental-Inflection Override — status: WATCH (1/2 holdouts)

**Failure case:** AVAV, 2026-06-29 (AMC). Model NO TRADE (DS 0); stock idio
+18.6%. Taxonomy C (genuine operational surprise: rev +133%, bookings $2.7B).
The long was suppressed by the REV-gate/falling-knife guard zeroing SAT even
though the operating KPI (VEL +1, backlog +51% YoY) was accelerating.

**Hypothesis:** analyst revisions (REV) LAG the operational turn on deeply
beaten-down names. When an accelerating KPI (VEL ≥ +1) confirms a real
inflection, a lagging-negative REV should not veto SAT's cheapness/vacuum
signal. VEL is the value-trap filter — it separates AVAV (real catalysts:
drone demand, gov contracts, physical-AI, space/directed-energy) from a name
that is merely cheap.

**Mechanism (code-complete, `inflection_override` flag, default OFF):**
in `score_sat`, when `inflection_override` AND `vel_score ≥ +1` AND
`below_52w_high_pct > 25`: SAT(a) vacuum +1 and SAT(b) +1 fire despite REV<0.

**Stress test (2026-06-30):**
| name | VEL | SAT off | SAT on | result |
|---|---|---|---|---|
| AVAV | +1 | 0 | **+2** | promoted (DS 0→+2; INCOMPLETE, capped by CBR block) |
| NKE  |  0 | 0 |  0 | unchanged (DS −2) — correctly NOT promoted |
| Intel-type (VEL 0) | 0 | 0 | 0 | value-trap: still guarded |
| Boeing-type (VEL −1) | −1 | 0 | 0 | value-trap: still guarded |
| UA-type (VEL 0) | 0 | 0 | 0 | value-trap: still guarded |

**Holdouts:** 1/2.
- ✅ AVAV 2026-06-29 (Type C, operational).
- ✗ NKE 2026-06-30 — does NOT count: classified ANOMALY (SCOTUS tariff-refund
  windfall), frozen. The stock's first reaction was −8%; the bounce was
  exogenous, not the inflection pattern.
- Need 1 more independent, non-anomaly beaten-down + VEL≥+1 name that rises.

**Parameter cost:** +1 (override condition) → 23 → 24. Pre-nominated for
ablation on promotion: REACT (standing pre-nominee, repeatedly unverifiable).

**Caveat:** even with W1, AVAV reaches only DS +2, not a BUY — the CBR block
(BlueHalo M&A + goodwill) and unverified GG/REACT still cap it. A clean
"BUY med" for AVAV additionally requires the CBR re-look (not yet opened) and
T-1-verified GG/REACT. W1 alone is necessary, not sufficient.

**Do NOT flip default until:** 2nd holdout confirms AND Jacob signs off AND the
REACT ablation is confirmed (parameter ceiling).
