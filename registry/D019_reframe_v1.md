# D019 · REFRAME: PRE becomes a code-only premium monitor · v1 — FROZEN 2026-11-04 (ET)

> **Source:** the independent Stage 1 committee, `reviews/2026-11-03_stage1_committee/REPORT.md` §12 (`2b95c1c`),
> and `COMMITTEE_ASSESSMENT.md`, "Changes to the plan from this round" (`4489a33`).
> **Approval:** Jacob, "Approve the stops", in the committee chat, relayed Tue 2026-11-03 ~11:40 ET.
> **Frozen before any change it governs.** The halt, the routine stops and the new scripts each come in a later
> commit. No frozen or hash-listed file is edited: every stop goes through data, settings or routines (rule 5).
> Every earlier version keeps its record and is graded untouched where its decisions were frozen.

## 1. Stopped

| what | registered as | how it stops (no hash-listed file edited) | from |
|---|---|---|---|
| paper options, short iron fly **F** | D011 v1 + v3 | the D011 §5 `halt` field in `paper/options_ledger.json` blocks every new open; exits keep running | the halt commit after this file (before the 14:30 ET gates, Wed 2026-11-04) |
| paper options, long straddle **L** | D011 v2 | the same `halt` in `paper/long_ledger.json` (`paper_long.py` runs v1's `step`, which reads it) | the same commit |
| shadow **T2R** and **T2O** | D013 | the cloud routine `earnings-t2-models` is disabled | when the routine is off |
| shadow **T2M** (mean of T2, T2R, T2O) | D013 | stops with T2R and T2O: it has no inputs | with them |
| shadow **T2G** (Gemini) | D004 v4 | the repository secret `GEMINI_API_KEY` is removed (a GitHub setting, Jacob's). `t2_stage2.py` then skips the backend ("no GEMINI_API_KEY") and `t2-queue.yml`'s waiting check stops counting it | when the secret is gone |
| shadow **T2E** (mean of T2 and T2G) | D004 v4 | stops with T2G | with it |
| **main T2** | D004 v4 | runs to Season A's close: every Season A event (report dates to **Fri 2026-11-20**) keeps its T2. After the last one is frozen, the cloud routine `earnings-t2-cloud` is disabled; the repository variable `T2_ACTIONS_CLAUDE` stays off | after 2026-11-20 |
| **H-T2C** | D005 v3 (A + B pooled) | never tested. It is reported as **"stopped for resources, no verdict"**. Season B registers no T2 test | now |
| selection research | — | no D018, no new hypothesis batch, no D003 v5 work beyond what the Season A record needs | now |

- **Open F and L positions** close under D011's own exit rules (v1, v3; the reaction session from 14:30 ET, a missed
  exit on a later run before expiry). Nothing new opens. Their results are graded and reported like every earlier
  trade.
- **D003 v5 (A4)** is not built. `registry/D003_v5_choice_v1.md` stays as the record of the choice. Season B's S2
  gate runs D003 v4 unchanged, unless a later version says otherwise.
- **A shadow decision frozen after this commit**, because a switch above was not yet off, belongs to no registered
  statistic. Its files stay (nothing is deleted).

## 2. Kept, code only

- the calendar capture, date confirmation (with its housekeeping routine), chain capture;
- the S2 gates, the freezes, grading (`grade.py`, D005);
- SH-W and SH-M grading (`shadow.py`, D009);
- paper shares, T0 (`paper.py`, D008 §1's S0);
- C1's registered look, from 2026-12-07 (D015), written once by code;
- the Gate 1 report (`gate1.py`) and the health check.

The chain capture keeps building the point-in-time options dataset at no AI cost.

## 3. Added, code only

Each is a new script beside the hash-listed files. Neither edits one.

- **(a) The MOC secondary on SH-M and SH-W:** buy at the close before the print, sell at the close of the reaction
  day. It is net of US$0.99 per order at a stated $1,000 notional. Its full definition is frozen in its own
  registry file **before any of its numbers is computed**. It is scored on **Season B only**, because Season A was
  read before it was registered (REPORT §12.3 and the "Required sample" bullets below).
- **(b) The Layer-1 capture:** after each print, the reported EPS and the surprise from yfinance's timestamped
  `get_earnings_dates()`, and the revenue actual from SEC EDGAR, each stored with its source tier. It diagnoses the
  reaction layer at Gate 1 and tests nothing.

## 4. The premium's primary read is SH-M

This settles the conflict PRE found (`PRE_QA_answers.md` P4): D008 §3 #1 tests H-S0 on at least 250 gated events,
while RESEARCH_PLAN §6 says "T0 or T0-wide". Gated events reach 250 only in May–Aug 2027, after Gate 2.

- From this file, the premium's **primary read at Gate 1 and Gate 2 is SH-M** (D009 §3, market-wide), on the bars in
  §5. SH-W and gated S0 (H-S0) are reported beside it as secondaries.
- D008 is not edited. Its criteria are still computed and reported at Gate 2. **§5 decides continuation and
  termination.** Real money needs every §5 row through the live pilot. D008 §4's kill switch applies to the live
  pilot, as §5 says.
- D017 §3's primary read (SH-W) was for Stage 1 only.

## 5. Kill and continuation criteria — REPORT §12, verbatim

<!-- VERBATIM-START REPORT.md §12 "Kill and continuation criteria, fixed now" -->
| milestone | date | continue only if | otherwise |
|---|---|---|---|
| Gate 1 | early Dec 2026 (all of Season A, ~1,300 SH-M events, ≥ 25 sessions) | SH-M **raw** mean's upper 95% bound (cluster-robust, t with clusters − 1 df) is ≥ **+0.50%**, and P1 still PASS | **TERMINATE (A)**. A premium below +0.5% raw cannot cover Jacob's ~0.5% round trip |
| Gate 2 | Mar 2027 (Seasons A + B pooled, ≥ 2,000 SH-M events, ≥ 50 sessions) | SH-M raw mean > 0 at one-sided p < 0.05 **and** point estimate ≥ +0.50%, **and** the MOC-executable statistic ≥ +0.50% on Season B | **TERMINATE (A)** |
| Paper pilot (only after Gate 2 passes) | Season C | ≥ 50 MOC round trips at real moomoo-style sizing; mean after fees ≥ +0.30%; max drawdown ≤ 10% of the sleeve | back to terminate |
| Live pilot (E) | Season D at the earliest | the above, plus a sleeve Jacob sets (suggested ≤ 10% of the account it trades in), per-event risk ≤ 0.5% of the sleeve, kill switch per D008 §4 | — |

- **Required sample:** detecting history's +0.65% net at 80% power (one-sided 5%, SD 9.8%) needs ~1,400 independent
  events. With the observed clustering (~10 events a session), plan on ~2,000 SH-M events: Seasons A + B. The gated
  S0 (~50 a season) would need over a decade, so it can never be the primary test.
- **Repeated looks** at Season A's events are not new evidence. Only Season B's events count at Gate 2 for the
  MOC-executable statistic, because it is registered after Season A was read.
- **The criteria do not move.** A change creates a new version with its own clock (PRE's rule 5). An unmet bar ends
  the project; it does not re-open the question.

**The opportunity cost of not reframing:** at the current pace, roughly $125–200 a month of laptop compute and most of a
weekly allowance shared with the money-running chats would go into a question whose best-case answer is worth a few
hundred dollars a year at Jacob's size.
<!-- VERBATIM-END -->

## 6. The budget

- one laptop chat per gate, ≤ 300k tokens each;
- zero laptop chats between gates, except to repair a broken code step;
- cloud routines for code steps only;
- a cap of **10% of the weekly plan allowance**, measured from the usage card each Monday.

This implementation (Wed 2026-11-04) is the last chat before Gate 1 that is not a repair. Its own hand-offs, if
the context guard needs any, count with it.

## 7. Owed, from the same round

- `gate1.py` health: count a graded gated PASS event that has no T2 decision as "T2 missing" (it read 0 of 26; ABT
  and SPCX have none).
- `stage1.py` P6: read T2's cost from `t2.json` (`t2.cost_usd_equiv`), not `decision.json`.

Neither file is hash-listed. Each fix is its own commit, beside the outputs it would have changed; no committed
output is replaced (D017 §2).
