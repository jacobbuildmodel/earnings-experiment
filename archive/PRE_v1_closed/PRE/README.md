# PRE — pre-earnings directional-sign classifier

Separate system from DRIVE (which fills the parent folder). Built here from the supplied
`MODEL_DISCLOSURE.md` v1.2.2 spec because no `pre_engine.py` existed in the workspace.

## Files
- `pre_engine.py` — sealed core (§14 spec) + governed v1.5.0 upgrades. Tiers tagged inline.
- `pre_ledger.py` — frozen pre-registration + append-only outcome log + kill-switch dashboard.
- `pre_calcrisk.py` — calculated-risk payoff layer v1.1.0 (PRIMARY output; BUY/SHORT/NO_TRADE).
- `pre_selftest.py` — 32 engine assertions (§11 AEHR walkthrough, C4 loss-catch, Stage-1 skew).
- `calcrisk_selftest.py` — 46 calc-risk assertions, each pinned to a NAMED post-mortem failure.
- `ledger_selftest.py` — ledger round-trip smoke test (uses a temp file; real ledger untouched).
- `PRE_UPGRADE_PLAN.md` — canonical tiered plan, evaluator verification, forward-validation bar, roadmap.
- `docs/skew_overlay_design.md` — STRUCTURAL EV/skew + calculated-risk design (Stage 1 built; 2/3 not).
- `ledger.jsonl` — the live forward-validation record (created on first real run).

## Ledger workflow (the forward-validation loop)
```python
from pre_engine import Judgment, Market, Truth, Skew
from pre_ledger import pre_register, record_outcome

# 1) BEFORE the print: freeze the pre-registration (integrity-hashed, append-only)
rec = pre_register("NVDA", judgment, market, truth=truth, skew=skew,
                   event_date="2026-08-27", note="Q2")
print(rec["verdict"]["action"], rec["id"])

# 2) AFTER the open: log the beta-stripped outcome (idio = stock_open - etf_open)
record_outcome(rec["id"], stock_open_pct=..., etf_open_pct=...,
               classification="NORMAL", taxonomy=None)   # 'B' = saturation misread
```
```
python pre_ledger.py stats      # kill-switch dashboard + Stage-2 skew n-count
python pre_ledger.py show 10    # last 10 frozen entries
python pre_ledger.py outcomes   # entries still awaiting an outcome
```
Kill switches auto-arm at their n-bars (idio-sign <50% @ n>=15 -> PAUSE, component <50% @ n>=20 ->
ablate, Type-B >2/10 -> SAT recalibrate, HIGH<MEDIUM inversion @ n_HIGH>=10). ANOMALY outcomes are
frozen out of all tuning stats. Stage-1 skew is logged on every entry; Stage-2 veto stays OFF until
>=10 skew-logged events accrue AND you sign off.

## Run
```
python pre_engine.py        # prints version + parameter count vs ceiling
python pre_selftest.py      # 32 — exit 0 = all pass
python calcrisk_selftest.py # 46 — exit 0 = all pass
python ledger_selftest.py   # 12 — exit 0 = all pass
```
All three suites must pass (90 assertions) before anything is handed back.

## What's live vs shadow vs design
- **Live (default):** sealed core + PLUMBING (C1/C2/C3) + fast-track conservative LOGIC (C4/C5/C6/C9).
- **Shadow (`EngineConfig(watch=True)`):** canonical LOGIC C7/C8 — score every event both ways to
  accumulate holdout evidence; do **not** land until 2 non-anomaly holdouts + sign-off.
- **Stage-1 skew (LIVE, v1.4.0):** pass an optional `Skew(...)` to `evaluate()`. SKEW/RICH/POS/PAYOFF
  are logged on every `Result` (`.skew`, `.skew_components`, `.skew_status`) and are **verdict-neutral** —
  never summed into DS, never gated. Its 8 thresholds are unvalidated priors, off the scoring-param budget.
- **Live (v1.5.0, calc-risk v1.1.0):**
  - **C12 forward-sourcing** — declare `order_driven` + `vel_basis` on every `Judgment`. On an
    order-driven name a `TRAILING_REVENUE` basis is REJECTED (VEL discarded, band widened).
    `EngineConfig(strict_sourcing=True)` additionally rejects any leg with no declared basis.
  - **FUND_UNDEFINED -> NO_TRADE** — a washout BUY needs >=2 of REV/GG/VEL actually VERIFIED.
    This is the fix for the NFLX/QS washout-BUY failure mode, and it is why C12 exists: without
    sourcing discipline it also blocks the AEHR-type winner. See the replay note in
    `calc_run_2026_07_14.py`.
  - **Cliff-fragility abstention** — a stance resting on an IRM sitting on a threshold abstains.
  - **VRICH** — vol-space richness (implied vs realized). Can demote or abstain; it CANNOT
    originate a trade on its own (that is Stage 2 and unapproved).
  - **Override logging** — `pre_ledger.log_override()`. Any narrative deviation from a mechanical
    signal MUST be logged and is scored as its own decision.
- **Design only:** skew Stage 2 (veto) / Stage 3 (calc-risk), options pricing/expression sizing,
  in-engine GG/VEL/REACT bucketing, a real positioning DATA FEED (the inputs exist; nothing fetches them).

## Non-negotiable
No change weakens a hard gate, the CBR long-block, the falling-knife guard, or the worst-case/INCOMPLETE
logic. Prime directive is anti-overfitting: at n≈3, freeze thresholds; validate forward, never on a
historical replay that the un-reproducible judgment layer makes impossible.

## Wiring the caller (LLM/reasoning layer)
Supply `Judgment` (RAW values + per-input `confidence`), `Market` (numeric), and a `Truth` object holding
the SAME fields fetched from a **pre-registered** data source (the engine never fetches — C4 only compares).
Missing `Truth` → the run is flagged UNRECONCILED but still evaluates.
