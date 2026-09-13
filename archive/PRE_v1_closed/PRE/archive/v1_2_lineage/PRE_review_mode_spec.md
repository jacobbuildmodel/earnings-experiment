═══════════════════════════════════════════════════════════════════
PRE v1.2 — BUILD BLOCK: `pre_engine.py --review` (READ-ONLY ANALYSIS)
Hand this to Claude Code. Implements descriptive log analysis only.
═══════════════════════════════════════════════════════════════════

PURPOSE
A read-only reporting mode over log.jsonl. It SURFACES evidence so Jacob
can read the model's health at a glance and feed the existing kill switches.
It is NOT a learning or tuning layer.

───────────────────────────────────────────────────────────────────
READ-ONLY CONTRACT (enforce in code — non-negotiable)
───────────────────────────────────────────────────────────────────
- Opens log.jsonl read-only. NEVER writes, edits, or reorders it.
- Proposes NOTHING. Changes NO threshold, weight, or rule.
- May write ONLY a timestamped copy of its own report to review_runs/.
- Every metric prints its n. Any metric below its kill-switch n threshold
  is printed but labelled "DESCRIPTIVE ONLY — below decision threshold".
- The report footer always restates: "Rule changes remain WATCH → 2
  independent holdouts → Jacob sign-off. This report decides nothing."
- If the LLM invokes this mode, it relays the report verbatim and adds no
  scores, verdicts, or recommendations of its own.

───────────────────────────────────────────────────────────────────
LOG SCHEMA IT READS (append-only JSONL; two record_types)
───────────────────────────────────────────────────────────────────
record_type="prereg" (written at entry, frozen):
  ts, ticker, earnings_date, session, price, sector_etf,
  components: { REV:{raw,score}, GG:{raw,score}, VEL:{raw,score},
               SAT:{raw_a,raw_b,score}, REACT:{raw,score}, FLAG:{raw,score} },
  DS, direction (BUY/SHORT/NO_TRADE), conviction, avg_abs_open, IRM,
  units, shares, gates:{G0..G4,CBR}, regime:{VIX, SPX_entry_move, macro_flag},
  integrity_hash (hash of all frozen fields above)

record_type="postmortem" (written after exit; keyed to prereg by
ticker+earnings_date):
  ts, ticker, earnings_date, price_source (named independent),
  stock_open_pct, etf_open_pct, idio_open_pct, idio_sign_correct (bool),
  raw_pnl, taxonomy (A–F), postprint_CBR

Integrity rule: on load, recompute integrity_hash for every prereg; any
mismatch = the frozen record was altered → list under DISCIPLINE, exclude
from accuracy stats.

───────────────────────────────────────────────────────────────────
REPORT SECTIONS (compute deterministically; this is engine math, no LLM)
───────────────────────────────────────────────────────────────────

1. HEADLINE
   date range | n_prereg | n_traded (BUY+SHORT) | n_no_trade |
   n_outcome (postmortem present) | n_unregistered_rejected

2. IDIO SIGN ACCURACY  (THE number)
   acc = correct / n_outcome, on idio SIGN only.
   Show acc and n_outcome. KILL SWITCH: if n_outcome≥15 and acc<50%
   → flag "PAUSE (idio acc <50% @ n≥15)". If n_outcome<15 → DESCRIPTIVE ONLY.

3. PER-COMPONENT ATTRIBUTION  (standalone, no interaction fitting)
   For each of REV, GG, VEL, SAT, REACT, FLAG:
     among outcomes where component.score ≠ 0:
       n_nonzero, standalone idio-sign hit rate (does the component's own
       sign match realized idio sign?).
   KILL SWITCH: if n_nonzero≥20 AND hit<50% → flag "ABLATION CANDIDATE
   (harming cumulative idio acc @ n≥20)". Below 20 → DESCRIPTIVE ONLY.
   Do NOT compute reweightings. Report only.

4. CALIBRATION
   - idio-sign hit rate by conviction tier (MEDIUM |DS|3–4 vs HIGH |DS|5+).
   - mean |idio_open_pct| by conviction tier (expect HIGH > MEDIUM if calibrated).
   - mean IRM, and mean |idio_open_pct| split by IRM above/below its median.
   All n-labelled; interpretation suppressed on any slice with n<5.

5. TYPE-B COUNTER  (SAT regime-blindness — also the REV-gate's live holdout)
   count of taxonomy=B in the last 10 outcomes.
   KILL SWITCH: if >2/10 → flag "recalibrate SAT". Note in output that the
   v1.2 REV-gate is on trial here — sustained Type-B at 0–1/10 post-v1.2 is
   the evidence the gate worked.

6. REGIME SLICES  (descriptive, n-gated, no decisions)
   idio hit rate sliced by: VIX>28 vs ≤28 | G3 macro-overlap vs clean |
   SPX_entry_move beyond ±1.5% vs within. Each slice prints n; suppress
   interpretation where n<5.

7. NO-TRADE AUDIT WORKLIST  (operational)
   list every NO_TRADE prereg whose later |idio_open_pct|>3% that has NO
   postmortem yet → these are owed a re-run per spec. Plain worklist for Jacob.

8. DISCIPLINE / INTEGRITY
   - integrity_hash mismatches (altered frozen records)
   - postmortems whose price_source is not a named independent source
   - preregs missing any component/source/timestamp (should already be
     rejected at write time; double-check here)
   - count of records excluded from stats and why

9. PENDING-CHANGE HOLDOUT TRACKER  (counts only; Jacob promotes)
   [P2 GG sandbag-overlay] list outcomes since registration where the name
     was a ≥3-of-4 guidance-beater AND GG applied a −1 → tally how many of
     those −1s were contradicted by a positive idio move (each = 1 confirming
     holdout). Show running count toward the 2 required. Promotion still needs
     Jacob + the REACT ablation call.
   [v1.2 REV-gate] show Type-B rate before vs after the gate's activation date
     as continued validation.

───────────────────────────────────────────────────────────────────
INVOCATION
───────────────────────────────────────────────────────────────────
CLI:  python pre_engine.py --review [--since YYYY-MM-DD] [--ticker X]
STANDING PROMPT (paste):
"Run pre_engine.py --review over the full log and show me the report
verbatim. Add nothing — no scores, no recommendations. Flag any tripped
kill switch and the NO-TRADE audit worklist."

OUTPUT: plain-text report to stdout + a timestamped copy in review_runs/.
Footer (always): "Rule changes remain WATCH → 2 holdouts → Jacob sign-off.
This report decides nothing."
═══════════════════════════════════════════════════════════════════
END BUILD BLOCK — review mode
═══════════════════════════════════════════════════════════════════