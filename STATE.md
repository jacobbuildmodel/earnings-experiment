# STATE — Earnings Experiment

**Phase 0 · Build** · updated 2026-09-13

## Done
- Folder created as its own git repo.
- The previous model (PRE v1) archived byte-exact in `archive/PRE_v1_closed/` — 98 files, SHA-256
  verified against the originals, first commit `d256787` — and removed from the DRIVE repo.
- `FRAMEWORK.md` v0.1 drafted: outputs-first design; three decision tracks (buy-all · rule · AI);
  clusters × business stage; 84-factor library with evidence; data sources probed live; the rules;
  the universe rule; timeline.

## Waiting on Jacob — blocks the first trade (Mon 2026-09-21)
1. **Primary exit:** A first open after the print · B reaction-day close · C +5 days. Default **A**.
2. **Primary outcome** = beat the sector, raw P&L alongside. Default **yes**.
3. **"bmc" = BMO?** Default **yes**.
4. **Industry allowlist** (FRAMEWORK §10). A plain sector screen let in two homebuilders, an RV maker
   and Manchester United. Default: the draft in §10.

## Next actions — Sep 14–18
1. Freeze decisions 1–4 into `registry/` once confirmed.
2. Universe: pull the FULL season calendar (the one pulled so far is a 1,064-of-3,548-row preview);
   apply the §10 allowlist; freeze `universe/`.
3. Validate Alpha Vantage estimate history before building any D-family history: its EPS basis (it
   disagrees with its own earnings history on ORCL — 1.39 vs 1.74) and whether "N days ago" is anchored
   to the report date.
3. Pipeline: snapshot → hash → git-commit before the open; grading code; ET clock guard.
4. Factor extraction for the free families (A, C3–C4, D4–D5, E, F, I, J).
5. External evaluator design brief → `reviews/`.
