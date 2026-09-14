# STATE — Earnings Experiment

**Phase 0 · Build** · updated 2026-09-14 · collection opens **Mon 2026-09-21**

## Where things are

| what | where |
|---|---|
| this project | `C:\Users\jacob\OneDrive\Desktop\Jacob\Earnings Experiment` — its own git repo |
| backup | `C:\repos\earnings-experiment.git`, remote `local` — push after every commit |
| PRE v1 | `archive/PRE_v1_closed/`, byte-exact and fenced — never read it while designing (`archive/README.md`) |
| DRIVE | PRE was removed there in commit `ea4d32d`; a DRIVE chat that hears `pre earnings model` sends Jacob here |

## Done

- Repo created; PRE v1 archived — 98 files, SHA-256 verified (`d256787`).
- `FRAMEWORK.md` v0.1 — outputs-first design (`ea772cf`).
- **Handoff (2026-09-14):** trigger phrase wired in `CLAUDE.md`; `check.py` health check; off-OneDrive
  backup; session-only evidence rescued into `analysis/exploratory/` (the pilot screen and the raw source probes).
- **Every figure and quote in `FRAMEWORK.md` re-checked against the saved lookups (2026-09-14).** Corrected:
  - pilot screen: **34** names passed, not 30. The "22 big movers" figure was dropped — it was annualised
    at-the-money vol, and for 8 of the 34 the option expiry ended before the report
  - replaced three overstated or unsourced descriptions ("shrinking", "on rate risk alone", "AI hardware
    manufacturing") and a false sector claim (Manchester United is Communication Services)
  - §8 no longer claims every source was probed live — only Alpha Vantage and yfinance were
  - removed an unverified claim that 1.74 "matches the consensus quoted in coverage"
  - Frazzini & Lamont: the premium tracks volume at **past** announcements, not pre-print volume
  - a link labelled "Thomas & Zhang 2008" pointed to a different, 2019 paper — relabelled
  - the calendar preview is date-sorted, so Sep 14 – Oct 9 is complete, not partial
- **PRE v1's reported figures checked against filings and call transcripts (2026-09-14).** Nothing was
  fabricated; there were mislabels and one unsupported causal story. See `reviews/ERRATA_2026-09-14_PRE_v1_figures.md`.

## Waiting on Jacob — blocks the first trade (Mon 2026-09-21)

1. **Primary exit** — A first open after the print · B reaction-day close · C +5 days. Default **A**.
2. **Primary outcome** — beat the sector, raw P&L alongside. Default **yes**.
3. **"bmc" in his message = BMO.** Default **yes**.
4. **Industry allowlist** — the draft in `FRAMEWORK.md` §10. Default **the draft**.

Not blocking: ThetaData ~$40/month for historical options, or collect free going forward (default: free) ·
a retail-attention source (default: leave it out of v0) · real trades, paper, or signals only (default: signals).

## Next actions — Sep 14–18

1. Freeze decisions 1–4 into `registry/` once Jacob confirms.
2. **Universe:** pull the FULL season calendar (`return_full_data`); apply the §10 allowlist; confirm every
   date and session from two sources; freeze `universe/`. First clean event: **MU, Sep 30, after close.**
3. **Pin the EPS basis before building any beat or surprise factor.** Alpha Vantage gives ORCL's quarter
   ending 2026-08-31 two consensus figures — 1.39 (earnings history) and 1.74 (estimates history). Also
   check whether "N days ago" in estimates history is anchored to the report date or to today.
   Lead (2026-09-14): the release gives GAAP EPS **$1.56** and non-GAAP **$1.92**; yfinance gives 1.74
   estimated against 1.92 reported, so **1.74 is the non-GAAP consensus**. Earnings history's 1.63 and 1.39
   match neither basis — find out what they are before using that endpoint.
   **Pin "the open" as well:** for CPRT on 2026-09-11, yfinance's daily Open was 32.01 while the 09:30
   one-minute bar opened at 31.76. Exit A needs one definition and one source.
4. Pipeline: snapshot → hash → git-commit before the entry open; grading code; ET clock guard.
5. History study on the free factor families (A, C3–C4, D, E, F, I, J).
6. External evaluator design brief → `reviews/`.
7. Probe a lead in `reviews/external_source_leads.md` only when a factor needs it.

## Watch-outs

- **Alpha Vantage free key: 25 calls a day, 1 a second.** Three probes were rate-limited for firing too
  fast. The ETF-holdings endpoint the leave-one-out benchmark needs is still untested.
- The pilot screen's implied-vol column is a proxy — never reuse it as the §10 rule.
- `FRAMEWORK.md` was drafted in a chat that held PRE v1's full history. Review it with fresh eyes; the
  external evaluator is the check on that.
