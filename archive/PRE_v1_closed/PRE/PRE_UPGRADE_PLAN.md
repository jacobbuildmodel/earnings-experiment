# PRE v1.2 → v1.3 — Tiered Upgrade Plan (canonical)

**Status:** built and shadow-tested. Sealed core reconstructed from `MODEL_DISCLOSURE.md` §14;
governed upgrades implemented in `pre_engine.py` v1.5.0; assertions in `pre_selftest.py` (32),
`calcrisk_selftest.py` (46) and `ledger_selftest.py` (12) — **90/90 pass**.
**Prime directive:** anti-overfitting. At n≈3, a change justified by 2–3 vivid trades is overfitting,
not learning. No change here weakens a protection.

> ⚠️ There is **no `pre_engine.py` in the original workspace** and **no historical dataset**. This
> engine is a faithful reconstruction; validation is **forward** (frozen pre-registration + holdouts),
> never historical replay. Any "backtest" language below is market-data-only or aspirational, flagged as such.

---

## 1. Evaluation verification (accepted / disputed / evaluator-errors)

| Auditor claim | Verdict | Note |
|---|---|---|
| Sign-only can't serve skew philosophy (comeback/sell-the-news/AVGO) | **Accept** | Model's own §15.1. STRUCTURAL. |
| Judgment layer is the real, unaudited risk surface; AEHR was input-not-logic | **Accept** | §8.1. Drives C1/C4. |
| Worst-case band defends *declared* UNAVAILABLE only, not silently-wrong inputs | **Accept** | → C4 (reconcile) + C5 (CONFIDENCE). |
| Both dampers multiply → 0.25× in the worst regime | **Accept** | → C9 kill. |
| n=1–2 thresholds (SAT ±20/−10, REV-gate, ±3, VEL 400bps) | **Accept** | Response = **freeze**, not tune. |
| "DS max +8 / bear −8" | **Evaluator error** | True bound **[−9, +7]** (FLAG subtract-only). Disclosure's own "≈[−6,+6]" also loose. Asymmetry is *larger* than claimed. |
| "~$18k position for a 21%-vol name" | **Evaluator error** | Sizing gives **~$11.9k** at 21% gap; $18k implies ~14%. Capacity conclusion survives; arithmetic wrong. |
| Benchmark ~55–65% | **Dispute (over-reach)** | Unsourced. Honest bar = **≈50% / ATM straddle, net of costs**. |
| "Input validator is plumbing" | **Evaluator error (tier)** | It moves AEHR's verdict on replay ⇒ **LOGIC**, not autonomous. |
| "ALIGN/OPPOSE conviction is small-n-safe, no rule change" | **Evaluator error** | Moves verdicts + sizing ⇒ **LOGIC**; adds a parameter. |
| "Run a 5,000-event historical backtest" (#16/#17) | **Dispute / infeasible** | Judgment layer not reconstructable at T−1 without look-ahead. Only a *market-data-only* study of SAT/gates/sizing is feasible. |
| **Band excludes REV & SAT** (both docs miss this) | **New finding** | REV→0 when coverage UNAVAILABLE but never swung in floor/ceil ⇒ C6. |

---

## 2. Governance tiers (definitions in force)

- **PLUMBING** — autonomous. Qualifies only if re-running the full log reproduces byte-identical
  component values *and* verdicts.
- **LOGIC** — moves any logged value or verdict. Requires named failure case + **2 independent
  non-anomaly holdout confirmations + owner sign-off** before it lands. *Exception:* a purely
  **conservative** change (can only turn trade→non-trade) has no *edge* to prove, so it needs
  sign-off + a false-positive check, but the 2 holdouts are **waived** ("fast-track").
- **STRUCTURAL** — new data stream / ML / EV-skew / options / portfolio model / changes what is
  optimized. Owner approval to *build*. Proposed as design; never folded in.
- **Parameter ceiling = 30** (registry-enforced in code). Any new parameter names an ablation.

---

## 3. Concrete changes — as built

| # | Change | Layer | Tier | Param cost | State in v1.3.0 |
|---|---|---|---|---|---|
| C1 | Level-1 sanity bounds → `INPUT_INVALID` | Engine | PLUMBING | 0 | **active** |
| C2 | Sub-typed NO_TRADE {LOW_CONVICTION, GATE_FAIL, LONG_BLOCKED, SHORT_BLOCKED} | Engine (log) | PLUMBING | 0 | **active** |
| C3 | Sensitivity score = frac. of ±1-bucket perturbations that flip the verdict | Engine (log) | PLUMBING | 0 | **active** |
| C11 | INCOMPLETE hygiene: re-source only from pre-registered channel, append-only row | Gov | PLUMBING | 0 | doc rule |
| C4 | Cross-source reconciliation vs. caller-supplied pinned truth → `INPUT_INVALID` | Engine boundary | LOGIC (fast-track) | 0 scoring (tol = validation layer) | **active** |
| C5 | `CONFIDENCE` per input; LOW treated as UNAVAILABLE in the band | J→E | LOGIC (fast-track) | 0 | **active** |
| C6 | Swing **REV**/**SAT** in the worst-case band when UNAVAILABLE | Engine | LOGIC (fast-track) | 0 | **active** |
| C9 | Macro-overlap **AND** vol-damper both fire → NO_TRADE (replaces 0.25×) | Engine | LOGIC (fast-track) | 0 (removes a ×) | **active** |
| C7 | SAT(b) "+1" disabled when `excess_PED ≥ +20` (reuse cutoff) or `VEL < 0` | Engine | LOGIC (canonical) | **0** (reuses SAT_SATURATION + VEL) | **shadow (`watch=True`)** |
| C8 | Require `ALIGN ≥ 3` to trade; **retire HIGH 1.5× → 1.0×** | Engine | LOGIC (canonical) | +1 ALIGN −1 HIGH_UNITS = **0** | **shadow (`watch=True`)** |
| — | REV time-decay/magnitude; CVaR sizing | Engine | LOGIC | +2–3 / +1 | **deferred (WATCH)** |
| — | Per-KPI VEL thresholds | Engine | LOGIC | **+9 → ceiling breach** | **REJECTED** |
| S1 | EV/skew overlay — **Stage 1 (diagnostic)** | New layer | STRUCTURAL (owner-approved) | 8 diagnostic params, **off scoring-budget** | **LIVE (logged, verdict-neutral)** v1.4.0 |
| S1b | EV/skew overlay — Stage 2 (veto) / Stage 3 (calc-risk) | New layer | STRUCTURAL | gated | design only → `docs/skew_overlay_design.md`; own n-bar + separate sign-off |
| S2 | Defined-risk options expressions | New instrument | STRUCTURAL | — | design only |
| S3 | Move GG/VEL/REACT bucketing into engine from raw | Engine + data | STRUCTURAL/LOGIC | — | escalate |

**Net scoring-parameter position after all *active* changes: unchanged (registry = full set, ≤ 30).**
C7 and C8 are parameter-neutral *by design* — this is the point.

### Why C7/C8 are shadow-only even though you said "just do it"
They are **canonical LOGIC**: they change verdicts/sizing without being purely conservative-by-construction
in a way that needs no evidence (C8's ALIGN gate is conservative, but its verdict-shifting still merits the
holdout to confirm it isn't over-abstaining; C7 fixes a named quirk but on n≈3). Landing them live now would
violate the model's own anti-overfit discipline. They run in `watch` mode so every future event is scored
**both ways** — accumulating the pre-designated holdout evidence to land them properly.

---

## 4. Updated decision framework

**Active now (sealed core + fast-track):**
- **BUY / SHORT** — unchanged triggers, but a thin-coverage REV or a missing SAT input can no longer
  silently carry a verdict (C6), a LOW-confidence input widens abstention (C5), a divergent input is
  refused (C4), and a macro+vol tape kills the trade (C9).
- **NO_TRADE** — now sub-typed so "high-conviction NO_TRADE" (blocked by CBR/G4/gate) is a reviewable class.
- **Conviction** — HIGH/MEDIUM labels retained; the **1.5× size privilege is retired under `watch`** until
  n proves HIGH > MEDIUM idio-sign accuracy.

**STRUCTURAL (not built — `docs/skew_overlay_design.md`):** comeback-BUY, sell-the-news/AVGO-SHORT, and the
low-IV filter are **payoff-skew** bets. A sign-only equity model cannot express them. They require the EV/skew
overlay + options data. The **calculated-risk framework** (RICH/POS/PAYOFF → 0.5-unit sizing, staged
diagnostic→veto→upgrade) is designed there; it needs data PRE does not ingest (straddle, 25Δ skew, realized
vol, reaction-magnitude history). **Not a quick edit.**

---

## 5. Forward validation & degradation (honest about n≈3)

- **No backtest of the full pipeline** (judgment layer un-reconstructable). A market-data-only study of
  SAT/gates/sizing against price history is the only legitimate "backtest" and is scoped as S4.
- **Benchmark:** idio-sign **materially > 50%**, net of half-spread + slippage + borrow + tax — i.e. beat the
  ATM straddle, not the auditor's inflated 55–65%.
- **A change "helped" (not noise)** only if pre-registered, parameter frozen, and confirmed by
  **pre-designated** holdouts (not "the next 2 that match") on beta-stripped idio-sign.
- **Minimum evidence bar before any *edge* LOGIC lands or capital scales:**

| Claim | Bar | n |
|---|---|---|
| Beats 50% / straddle, net | idio-sign materially > 50% | ≥ 15 |
| Beats trivial shadow (`REV≥+1 ∧ GG≥0 → BUY`) | ≥ several-pp margin | ≥ 15 |
| A component earns its keep | standalone ≥ 50% | n_nonzero ≥ 20 |
| HIGH is real (justifies any bump) | HIGH ≥ MEDIUM | ≥ 10 per tier |
| Learned weights | — | **≥ 100 — do not attempt earlier** |

- **Kill switches:** keep all disclosed (idio-sign <50% @ n≥15 → PAUSE; component <50% @ n_nonzero≥20;
  Type-B >2/10). **Add** (counters = PLUMBING, PAUSE-trigger = owner-approved): portfolio drawdown;
  validator firing >20% → pipeline broken; HIGH<MEDIUM inversion → suspend tier; slow-degradation
  (<55% @ n≥30). Tighten Type-B to persistence (`2/10 ∧ 4/20`).

---

## 6. What NOT to change
Sealed core arithmetic/cascade/fail-closed/INCOMPLETE/worst-case; CBR long-block; falling-knife guard;
REV-gate on SAT(a); gap-at-risk "sizing is the stop"; equal-weight integer buckets; the ±3 band and the
n=1–2 thresholds (**freeze**, don't tune). Do **not** add learned weights (n≪100), continuous scoring, a
probability layer, per-KPI VEL, or a full historical backtest presented as validation.

---

## 7. Prioritized roadmap (impact ÷ risk within tier)

**(a) PLUMBING — done / autonomous:** C1, C2, C3 (in engine); C11 (governance doc).

**(b) LOGIC — WATCH items pending pre-designated holdouts + sign-off:**
1. **C4** cross-source reconciliation — *highest impact/risk; the AEHR fix.* Active fast-track.
2. **C6** REV/SAT in band — closes a fail-closed hole. Active fast-track.
3. **C5** CONFIDENCE → band. Active fast-track.
4. **C9** both-dampers kill. Active fast-track.
5. **C7** SAT(b) parabolic fix — shadow; land after 2 holdouts.
6. **C8** ALIGN≥3 + retire HIGH 1.5× — shadow; land after 2 holdouts.
7. *(deferred)* REV decay/magnitude, CVaR sizing.

**(c) STRUCTURAL — escalate for owner approval to build:**
1. **S1 Stage 1** EV/skew overlay diagnostic — ✅ **BUILT & LIVE (v1.4.0)**, logged & verdict-neutral.
   Now accruing SKEW on every event toward the Stage-2 n≥10 bar.
2. **S1 Stage 2/3** veto + calculated-risk upgrade — pending Stage-1 sample (n≥10 / n≥25) + separate sign-off.
3. **S2** defined-risk options — express the skew edge; no short-vol until n≥50.
4. **S3** move GG/VEL/REACT bucketing into engine (reproducibility).
5. **S4** market-data-only study of SAT/gates/sizing vs. price history (the one legitimate backtest).
