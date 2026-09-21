# External evaluator brief — design review before results exist

**Prepared 2026-09-21.** The pilot's first entry is the 2026-09-22 open. No outcome of this experiment
has been graded. A flaw found now can still be fixed with a new rule version. A flaw found after
results exist can only be reported.

## What the experiment claims it will be able to say

> Before an earnings print, can a mechanical rule (T1) or an AI (T2) pick BUYs whose hit rate beats
> buying every eligible name (T0) — and does the answer differ by type of business?

Buy-side only. Every eligible event gets BUY or NO_BUY. The primary outcome is **raw direction**: the
price at the first official open after the print versus the entry open (D001).

## Read in this order (≈ 1 hour)

| # | file | what to check |
|---|---|---|
| 1 | `CLAUDE.md` | the ten rules that keep the experiment honest |
| 2 | `registry/D001_outcome_v1.md` | entry, exit, prices, WIN, VOID — frozen 2026-09-16 |
| 3 | `registry/D003_universe_screen_v1.md` | universe screen, per-event gate (implied move ≥ 4%, liquidity, two-source date confirmation) |
| 4 | `registry/D004_decision_protocol_v1.md` | what T2 may and may not read; BUY ⇔ confidence > 0.5; business-stage formula |
| 5 | `registry/D005_evaluation_v1.md` | how outcomes become verdicts: test, clustering, multiple testing, fixed wording, power |
| 6 | `pipeline/` | `due.py` (unattended gate and freeze) · `s2_gate.py` · `factors.py` · `freeze.py` (hashes, RFC 3161 timestamps, commit) · `grade.py` · `report.py` |
| 7 | `.github/workflows/` | when things run; how the AI step is fenced (sparse checkout, tool-call log) |
| 8 | `reviews/drafts/D003_v2_DRAFT.md` | changes proposed for Season A |

**Do not read `archive/`.** It holds a retired model whose record was contaminated. Its conclusions
are deliberately kept away from this design.

## How blindness is proven

1. **Order.** Decisions are written after the pre-entry snapshot and before the entry open. Code
   refuses to freeze at or after the open (`freeze.py`).
2. **Time.** Each freeze commit holds a manifest of SHA-256 hashes, plus two independent RFC 3161
   timestamp tokens (DigiCert, FreeTSA) over the manifest. `check.py` verifies that each token covers
   the manifest and pre-dates the entry open. It also fails if any later commit touches a frozen file.
3. **The AI's inputs.** In the AI step's checkout, `archive/` and `outcomes/` are not on disk. Every
   tool call is logged to `logs/actions/`, and any touch of a fenced path is flagged.

## Known limitations — disclosed, not hidden

- **Power.** About 100 events per season can only detect a lift of ~12 points of hit rate (D005 §7).
  One season's "no evidence" is expected even if a modest edge exists.
- **T0 is a real opponent.** The earnings-announcement premium and a rising market both push T0's hit
  rate above 50%.
- **Price checks.** The check source (Alpha Vantage) needs a key the automated grader may not have.
  Until it does, prices are graded `single_source`.
- **Leave-one-out benchmark** is not implemented (`bench_weight_missing`); WIN_excess is secondary.
- **EPS consensus basis** is not pinned across vendors. No EPS-surprise factor may enter a rule until
  it is (D005 §5).
- **T2's self-report.** T2 lists its own inputs. The tool-call log is the independent check.
- **Deviation.** The 2026-09-18 Friday mid-season re-pull (D003 §7) was never run; the code for it
  was added 2026-09-21.
- **Pilot universe.** It includes PAYX, which D002's intent excludes. Kept under rule 5; fix proposed
  in the D003 v2 draft.
- **Design author.** The framework was drafted in a chat that held the retired model's history
  (FRAMEWORK §9 bias note). That is why this review exists.

## The questions we most want answered

1. Is **lift over T0, on raw direction at the first open**, the right primary target for "can we pick
   BUYs"? Or should the primary be excess return, or the return-weighted version?
2. Is **clustering by entry session** sufficient? For exit A, every event entering on session X has
   the same open-to-open window. Is the **restricted wild cluster bootstrap-t** the right test at
   25–30 clusters?
3. Can T2 leak future information by any route we have not fenced?
4. Is the pre-entry **S2 gate** (implied move ≥ 4%, liquidity, confirmation) a selection that biases
   what can be learned?
5. What would make you refuse to believe a positive result from this design?

## What we will do with the answers

A defect in a frozen rule becomes a **new version** with its own clock. The old version keeps being
scored beside it (rule 5). Nothing already frozen is edited.
