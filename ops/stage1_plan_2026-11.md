# Stage 1 review — plan for Tue 2026-11-03 (SGT)

> Asked by Jacob on Thu 2026-10-29: results he can use to judge whether the model is useful, not redundant,
> and worth funding, plus the projects carrying into next month, presented like a PhD qualifying review.
> The rules of the look are frozen in `registry/D017_stage1_review_v1.md`. This file is the plan around it.

## The constraint that shapes everything

- **The weekly AI allowance was at 85% on Thu 09:13 ET**, with 3 days 16 hours to the Mon 2026-11-02 06:00 UTC
  reset. That is earlier than Wednesday's estimate of 85% by Fri 17:20.
- Friday's T2 decisions (18 gates) may run out before the fires land. Mon 10:20 UTC is the fallback.
  A lost decision is recorded as missing, never filled.
- **So nothing heavy runs before the reset.** Today's chat freezes the rules and the plan, then stops.

## Timeline (SGT = ET + 12 until Sun Nov 1, then + 13)

| when (SGT) | what | who |
|---|---|---|
| Thu Oct 29 | D017 frozen (pass/fail words, data cut, firewall), this plan, global multiplicity view registered | done |
| Thu → Mon 14:00 | laptop idle; cloud routines run Thu and Fri gates as usual | — |
| **before Mon Nov 2 14:00** | **D003 v5 = A4: yes or no**, on counts only. Silence means A4 (D017 §5) | **Jacob** |
| Mon Nov 2 14:00 (reset) | 1. DST inventory: the first EST session; the T2 deadline is 22:15 SGT | Claude |
| Mon 15:30 | 2. write `pipeline/stage1.py`, test on synthetic data, **commit before running** | Claude |
| Mon 17:00 | 3. run once on the Fri Oct 30 cut; commit the output | Claude |
| Mon 18:00 → Tue | 4. build the deck from the committed output only; a second model reviews it for overclaiming | Claude |
| **Tue Nov 3, by 12:00** | **deck delivered**; committee session with Jacob whenever he is ready | both |

**Time extension: not needed.** The one risk is Monday. If the DST inventory finds a break, it comes first,
because it protects live data. The deck then moves to **Wed Nov 4**, and Jacob is told by Mon 20:00 SGT.

## The deck — 13 slides, qualifying-review style

1. **The question, and the one-line answer.** It is written from the data, not before.
2. **What Stage 1 can and cannot prove.** The power maths (D017 §1): a real premium shows t ≈ 0.9 at 100 events.
   This slide stops a weak t being read as failure.
3. **P1 · the record is truthful.** Freezes before the open, hash chain, check.py, VOID, missed windows.
4. **The foundation · history (D006).** 2,771 prints: +0.85% raw, +0.65% net, +0.73% over the S&P, t 3.6.
5. **P2 · the premium, live.** SH-W, gated S0 and SH-M, each with its D017 word.
6. **Not redundant.** The excess over SPY is a return the index does not give. The negative knowledge stops the
   portfolio chasing stock-picking factors that failed.
7. **P3 · does the AI or the rule beat buying everything?** Likely INSUFFICIENT; said plainly.
8. **P4 · execution.** Paper fills against the official open; the paper options record at all four views.
9. **What failed, and what it taught.** Cron losses, the DPZ exit, the token refusal, the allowance.
10. **P6 · cost and capacity.** What a decision costs, what the allowance supports, what was lost to it.
11. **The ask.** The D017 §5 row the evidence lands in, and the capacity it needs.
12. **November → Gate 1 projects.** The table below.
13. **Committee questions.** The hard questions below, each answered from the record.

## Hard questions the deck must answer

| question | where the answer comes from |
|---|---|
| Isn't this just market beta? Why not buy SPY? | P2's excess over SPY; history's +0.73% over the S&P |
| How do I know you didn't pick the rules after seeing results? | commit timestamps before each open; D017 frozen before the look |
| Why so few events? Why is nothing "proven"? | the power slide; D016 gates passing few; D003 v5 |
| Was the premium a 2023–26 bull-market artifact? | history by quarter (4 of 13 negative); live season under new conditions |
| Does the AI add anything over buying everything? | P3, labelled; H-T2C is held to Gate 1 by design |
| What has a month of funding bought? | P1 record, P5 negative knowledge, P4 execution facts |
| What does it cost to run, and what breaks if it isn't funded? | P6 |
| When will we know for sure? | Gate 1 (early Dec, Season A report), Gate 2 (Mar 2027, the verdict) |
| What would make you stop? | D017 §5; D008's kill switch |

## Projects carrying into November and December

| project | why it matters | by |
|---|---|---|
| Finish Season A | more events: the only path to power | Nov 20 |
| DST inventory, then the health marker's window-job extension | protects the live record past Nov 1 | Mon Nov 2 |
| D003 v5 (A4) gate fix | more PASS events in Season B (5 → 7 in the audit) | before the Season B screen |
| Pooled H-T2C code, tested, reviewed and hashed; `D005_confirmatory_seasonB.json` without `T2_confidence` | the AI's calibration test becomes runnable | before the Season B screen |
| **Gate 1 report** (`gate1.py`): full Season A; register Season B's confirmatory family | the real Stage 1 → Stage 2 decision | early Dec |
| C1 look 1 (the gap fade) | first confirmatory look of any live signal | from Dec 7 |
| D018 history batch: busy-day attention (C) and industry read-across (D), FDR, t > 3 | the next candidate signals | Nov |
| Capacity: the Actions AI token; the plan's allowance | the experiment outgrew the allowance this week | Jacob's call at Stage 1 |
