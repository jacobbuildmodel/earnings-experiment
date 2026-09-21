# D004 · Decision protocol · v2 — FROZEN 2026-09-21 (ET) · applies from Season A

> **v1 stays LIVE for the pilot** (rule 5). v2 governs `seasonA` onwards. Machine-readable twin:
> `D004_decision_protocol_v2.json`, which code reads through `rule_for`. This file wins on any
> disagreement. **Everything not listed here is v1 unchanged.**
>
> Source: the external evaluations of 2026-09-21 (`reviews/evaluations/2026-09-21_external.md`).
> Both found that T2 could see information T1's snapshot never had.

## Change 1 — T2 decides by the close of the snapshot session

v1 let T2 decide any time before the entry open, which in practice meant until the evening run. After
16:00 ET T2 could read:
- peers' after-close prints
- the stock's own after-hours trading
- same-day news

T1's snapshot had none of that, so "T2 vs T1" was not a fair comparison.

**v2:**
- `decided_et` must be **at or before the close of the snapshot session**: 16:00 ET, or 13:00 on an
  NYSE early close.
- A decision after that is not valid, and code freezes the event with T2 **MISSING**.
- T0 and T1 are unaffected.

## Change 2 — timestamps on T2's inputs

Already enforced by `freeze.py` since 2026-09-21, for every season:
- An input published before the snapshot day may be dated with a date only.
- An input from the snapshot day **must carry its exact time**, and that time must precede the gate's
  `captured_et`.
- A live web page is used only if it has not been updated after `captured_et`. A page about the print
  itself is never used.
- What every web fetch returned (hash and opening text) is logged to `logs/actions/`, so a claimed
  time can be checked.

## Unchanged, and why

**BUY ⇔ confidence > 0.5 stays.** WIN_raw is "the price rises". For that question, buying exactly when
P(rise) > 0.5 is the decision that maximises expected correct calls, so the threshold is right.

The evaluator's concern is statistical power: with a ~55% base rate, the binary BUY test loses power as
T2's BUY share drifts. D005 v2 answers it by also testing T2's confidence number directly. The
decision rule does not change.
