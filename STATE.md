# STATE — Earnings Experiment

**Phase 0 · Build** · updated 2026-09-17 · collection opens **Mon 2026-09-21**

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

## Frozen 2026-09-16 — `registry/` (hash-checked by `check.py`; never edit, only add versions)

- **D001 outcome v1:**
  - Exit A is the first official open after the print. The official open is the daily-bar Open, not the
    09:30 one-minute bar: for CPRT on 2026-09-11, yfinance and Alpha Vantage both give 32.01 (probe 13).
  - **WIN = raw_return > 0** (Jacob's choice). WIN_net (20 bp) and WIN_excess are secondary.
  - **The bar is T0's hit rate, not 50%.**
  - It also fixes: price sources and their tolerance, fetch-once storage, splits and dividends, VOID rules.
- **D002 allowlist v1:** the §10 draft, verbatim. **Five terms are still judgment** (taxonomy source,
  "AI-hosting", "robotics is the product", healthcare "largest", options liquidity, plus the screening date
  and the implied-move formula). D003 must turn them into numbers before any calendar name is screened.
- `FRAMEWORK.md` is now v0.2 (§2, §3, §5, §12 match the registry; **the registry wins on conflict**).
- The WIN_excess benchmark (ETF map, beta window, leave-one-out threshold) is frozen WITH the universe.

## Literature review — DONE 2026-09-17 → `reviews/literature_review.md`

- 48 papers, each tagged by verification tier:
  - **V1**: abstract read on a primary page. Only V1 figures are quoted.
  - **V2**: bibliography confirmed only.
- **27 candidate factors, LR01–LR27**, each with the sign that favours BUY, how well its window matches
  ours, what data it needs, and its FRAMEWORK family.
- Uncomfortable points:
  - the announcement premium means **T0 is a real opponent**
  - published edges decay: about 35% after publication in McLean & Pontiff's 2012 draft, and for large
    stocks the post-earnings drift has been gone since 2006 (Martineau)
  - most papers use 3-day windows, not our open-to-open
  - many attention effects change the size of the move, not its direction
- Caught: a wrong remembered title (Jin, Livnat & Zhang); an "11%" figure absent from the paper's own
  abstract; McLean & Pontiff figures available only from the 2012 draft.
- Actions it created: probe FINRA daily short-sale volume · **capture option chains before every entry
  from Season A (or the pilot), even unused** · pin the EPS basis · choose a live sentiment proxy and
  freeze it with the universe · read each paper's method section before its factor is registered.

Not blocking: ThetaData ~$40/month for historical options, or collect free going forward (default: free) ·
a retail-attention source (default: leave it out of v0) · real trades, paper, or signals only (default: signals).

## Next actions — Sep 16–18

1. **D003 universe screening rule:** give the five open D002 terms numbers, fix the screening date,
   the implied-move formula and the WIN_excess benchmark. Freeze D003 BEFORE pulling the season calendar.
   Then pull the FULL season calendar (`return_full_data`), apply the rule, confirm every date and
   session from two sources, and freeze `universe/`. First clean event: **MU, Sep 30, after close.**
2. **Pin the EPS basis before building any beat or surprise factor.** Alpha Vantage gives ORCL's quarter
   ending 2026-08-31 two consensus figures — 1.39 (earnings history) and 1.74 (estimates history). Also
   check whether "N days ago" in estimates history is anchored to the report date or to today.
   Lead (2026-09-14): the release gives GAAP EPS **$1.56** and non-GAAP **$1.92**; yfinance gives 1.74
   estimated against 1.92 reported, so **1.74 is the non-GAAP consensus**. Earnings history's 1.63 and 1.39
   match neither basis — find out what they are before using that endpoint.
   **Lead (2026-09-17):** Nasdaq's earnings calendar gives ORCL the same pair — forecast $1.39, reported
   $1.63 (probed on 2026-09-10) — so AV earnings history shares Nasdaq's consensus basis, not non-GAAP.
3. Pipeline (include option-chain capture — literature review §6): snapshot → hash → git-commit before the entry open; grading code that reads
   `registry/D001_outcome_v1.json`; ET clock guard.
4. History study on the free factor families (A, C3–C4, D, E, F, I, J) plus the free LR candidates.
5. External evaluator design brief → `reviews/`.
6. Probe a lead in `reviews/external_source_leads.md` only when a factor needs it (first: FINRA short-sale volume for LR09).

## Watch-outs

- **Alpha Vantage free key: 25 calls a day, 1 a second.** Three probes were rate-limited for firing too
  fast. The ETF-holdings endpoint the leave-one-out benchmark needs is still untested.
- The pilot screen's implied-vol column is a proxy — never reuse it as the §10 rule.
- `FRAMEWORK.md` was drafted in a chat that held PRE v1's full history. Review it with fresh eyes; the
  external evaluator is the check on that.
