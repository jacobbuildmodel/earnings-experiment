# D016 · Season A gate audit · v1 — counts only · FROZEN 2026-10-21 (ET), before 14:30 ET

**Why.** Power is the binding constraint (CHARTER, lever 1). Season A's S2 gate (D003 v4 §6) passed 5 of its first
15 events. 9 failed `wide_spread`, 1 `thin_oi`. `gate.json` keeps only the FIRST failing check, so nobody knows how
many names fail several checks, or which alternative gate the stored chains would have passed. This audit counts
that, so Jacob can decide a **D003 v5 for Season B** without seeing any outcome (HYPOTHESES idea B).

**What it never changes.** The Season A gate stays D003 v4 for the whole season (rule 5). D016 grades nothing and
re-labels no event. Any change it supports is D003 v5, from the Season B screen, and Jacob's call.

## 1. Inputs — two files per event, nothing else

- `events/seasonA/*/gate.json` and the same folder's `option_chain.json`. Live gates only: `dry` false and
  `in_s2_window` true.
- **Never read:** `outcomes/`, `paper/`, `shadow/`, any decision, thesis, dossier, manifest or factor file. The code
  opens files through one function that refuses any other name. `tests/test_gate_audit.py` records every file the
  audit opens on a tree that also holds outcome and paper files, and fails if it opens anything else.
- A gate that failed before the chain (`unconfirmed`, `outside_window`, `printed_before_entry`, `no_expiry`,
  `chain_error`) is counted on one line and has no chain reading.

## 2. Part A — the full D003 v4 cascade on every event

Every check is evaluated on every event, not only the first that fails:

| check | fails when |
|---|---|
| `no_quote` | either leg at the gate strike has bid ≤ 0 or ask ≤ bid |
| `low_implied_move` | `(mid call + mid put) / spot < 0.04` |
| `wide_spread` | either leg's `(ask − bid) / mid > 0.10` |
| `thin_oi` | call + put open interest within ±2% of spot (always including the nearest strike) `< 500` |

- Spot, the gate expiry and the gate strike come from `gate.json`. The legs and the open interest are recomputed
  from `option_chain.json`.
- **Reproduction check:** the recomputed first failure (in the order above) must equal `gate.json`'s status and
  reason. A mismatch is reported by ticker and never "fixed".
- Reported: events failing each check; events where it is the **only** failing check; every combination seen.

## 3. Part B — pass rate by bucket

- **Share price** (spot): `< $100`, `$100–<$300`, `≥ $300`.
- **Expiry gap:** gate expiry ≤ 5 sessions after the reaction day vs > 5 (D003's `diluted_implied_move` flag; in
  practice a monthly expiry, because the name lists no weekly).
- Each bucket: events, PASS, and failures per check.

## 4. Part C — alternatives the stored chains support

Each keeps every other D003 v4 check exactly as it is.

| id | change | what it measures |
|---|---|---|
| A0 | none (D003 v4 as run) | the baseline and the reproduction |
| A1 | the **better of the two strikes nearest spot** (by distance, tie → lower; listed for calls and puts). PASS if either strike passes every check; it keeps the passing strike with the lower worst-leg spread. The open-interest band also includes the chosen strike | a gate lost to one bad strike |
| A2 | a **dollar floor**: a leg passes the spread test if `(ask − bid) / mid ≤ 0.10` **or** `ask − bid ≤ $0.10` | cheap options held back by the tick size |
| A3 | the **straddle spread**: `(spread call + spread put) / (mid call + mid put) ≤ 0.10`, in place of the per-leg test | the cost of the structure that is traded, not its worst leg |
| A4 | A1 and A3 together | both |

All four keep the 10% friction ceiling: they measure it at a better strike, net of the tick, or on the straddle.
A3's bound on the straddle mid (±5%) is the same bound v4's per-leg test gives the implied move.

**Sensitivity, reported and never recommended by §5:** the per-leg cap at 0.125, 0.15 and 0.20, and A3's cap at
0.125 and 0.15. These raise the friction ceiling. Jacob sees what each would buy; choosing one would be his call
with its own written reason.

**For each alternative:** PASS count, the events it adds over A0 (by ticker), and the friction of what it admits.
That is the median and maximum straddle spread, and the maximum single-leg spread, over its PASS events.

**Needs a forward capture, not this audit:** a later quote inside the S2 window, and a next-expiry gate. The stored
chain holds one snapshot of one expiry. Either would be a separate pre-registered capture file.

## 5. Decision rule — counts to a D003 v5 proposal (fixed before any count was computed)

1. `N` = audited events with a chain reading. `P(x)` = PASS count under alternative x. `gain(x) = P(x) − P(A0)`.
2. If no alternative among A1–A4 has `gain ≥ 2` → **recommend keeping D003 v4 for Season B.** A change mixes two
   gate versions in pooled H-T2C, and fewer than 2 names over the audit could be one name's accident.
3. Otherwise → recommend the alternative with the largest `P`. Ties go to the lower median straddle spread among
   its PASS events, then the simpler rule, in the order A2, A1, A3, A4.
4. The recommendation is a proposal written in the report. D003 v5, if Jacob takes it, is a new frozen file that
   applies from the Season B screen and is reviewed independently before its freeze.

## 6. When it runs

- **The decision run:** the first run at or after **Fri 2026-10-23 16:00 ET**, over every live Season A gate on disk
  at that moment: `python pipeline/gate_audit.py seasonA --decision`. It writes
  `analysis/d016/gate_audit_seasonA_decision.{json,md}` once (write-once) and is committed.
- **Interim runs** before that are allowed and labelled `interim` in the file name and the header. They decide
  nothing.
- **A season-end run** (descriptive) repeats it on all Season A gates, for the Season B file's power estimate.

## 7. Disclosed

- **The design was informed by the first gate failures.** The Mon 2026-10-19 plan named the four that existed then:
  DPZ, NOC, RTX and VICR all failed `wide_spread`, and RTX was a near miss. The chat that froze this file also saw
  the 15 `gate.json` readings (spreads, open interest, implied moves). It computed no alternative's count before
  this freeze.
- **No Season A return, paper P&L, grade, C1 or shadow figure** selects or justifies anything here (rule 6; D005 v3's
  interim clause). NOC, RTX and VICR traded on paper; this file is frozen before their first P&L is read.
- **Pooled H-T2C will mix two gate versions** if v5 is adopted. The Season B file must say so and report each
  version's events separately.
- **Counts this small are descriptive.** At 15–30 events, a 2-name gain is a proposal for Jacob's judgement, not a
  finding. Season B's own gate counts are the test of it.
- **yfinance quotes** at the 14:31 ET snapshot are the only spread source. A wider quote at that instant fails a
  name that was tradable a minute later; §4's forward capture would measure that.

## 8. Implementation

`pipeline/gate_audit.py` and `tests/test_gate_audit.py`, hashed in `registry/D016_implementation_v1.sha256`
(frozen with this file). check.py FAILS if either differs. A fix is a dated addendum, never an edit.
