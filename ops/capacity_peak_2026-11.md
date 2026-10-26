# Peak capacity, Nov 2–6 (and this week) — computed Mon 2026-10-26

Written 13:10 ET by the T2-check chat. The numbers come from `python ops/capacity_peak.py --spot`, which reads only
the calendar, the gate files and the paper ledgers' sizing fields (n, mid, wings, the opening natural, equity). **No
result, P&L or C1 figure was read.** Re-run it Fri Oct 30, when more dates are confirmed.

## The answer

| resource | binds? | when | what is lost |
|---|---|---|---|
| **Main paper account** (butterflies + T0 stock + DPZ) | **yes, this week** | from **Tue Oct 27** | ~58% of the butterflies wanted Oct 27–Nov 11 are refused (`capacity`); ~33% if DPZ is flattened |
| Second paper account (long straddles) | at the edge | Wed Oct 28, Tue Nov 3 | ~7% refused |
| AI allowance (Pro, weekly) | **this week, if laptop chats run long** | Fri Oct 30 17:20 ET fire | a scored T2 (MISSING, can't be redone). Measured cost below |
| S2 gates | no | — | 8 gates take 11–14 s; 55 take ~1.5 min of an 80-minute window |
| T2 timing | no | — | ~20 s per call; the shadows' 12-per-run cap spills Tue Nov 3's extras to the next fire, which still lands before 09:15 |
| C1 capture | watch | peak days | more names to settle in the 15:25–15:55 window; count only |

**Scored decisions are not at risk from the paper accounts.** `grade.py` grades T0/T1/T2 from prices, not from
paper fills. A refused paper open loses a D011 execution observation, nothing else.

## 1. The calendar (Season A; 208 confirmed + 79 pending at 12:30 ET)

Prints Nov 2–6: **157** (121 confirmed). Prints Nov 3–5: **135**. The plan's "~165" was an older estimate.

| S2 day (gate) | confirmed | + pending (est.) | gates | PASS at 26% | AI calls (×3) |
|---|---|---|---|---|---|
| Mon Oct 26 | 20 | 4 | 24 | 6.2 | 19 |
| Tue Oct 27 | 33 | 4.5 | 37.5 | 9.7 | 29 |
| Wed Oct 28 | 20 | 3 | 23 | 5.9 | 18 |
| Thu Oct 29 | 1 | 2 | 3 | 0.8 | 2 |
| Fri Oct 30 | 18 | 7.5 | 25.5 | 6.6 | 20 |
| **this week** | 92 | 21 | **113** | **29** | **88** |
| Mon Nov 2 | 24 | 11 | 35 | 9.0 | 27 |
| **Tue Nov 3** | 45 | 9.5 | **54.5** | **14.1** | 42 |
| Wed Nov 4 | 33 | 5 | 38 | 9.8 | 29 |
| Thu Nov 5 | 2 | 4 | 6 | 1.5 | 5 |
| Fri Nov 6 | 3 | 3 | 6 | 1.5 | 5 |
| **peak week** | 107 | 32.5 | **139.5** | **36** | **108** |

A pending name with no session is counted half BMO (gate D−2), half AMC (gate D−1). The pass rate is Season A's
8 / 31. Power: ~65 more PASS by Nov 6, against the plan's minimum of 12 PASS-with-T2 by Nov 20.

## 2. Paper accounts

**One structure is far bigger than the design.** D011 sizes n = floor(0.5% of equity / (100 × straddle mid)),
at least 1. 0.5% of $91k is $456, so any straddle dearer than $4.56 is one contract. **23 of 26 butterflies and
22 of 25 long straddles so far sat on that 1-lot floor.**

| so far (opening natural) | median | p90 | max |
|---|---|---|---|
| butterfly margin, % of main equity ($91,140) | 2.6% | 5.5% | 6.6% |
| long straddle cost, % of second equity ($94,733) | 2.1% | 4.3% | 5.1% |

Wing width is 2.14× the straddle mid and the credit 0.78× (medians), so the margin is ~1.36 × mid × 100. The
dear names coming up cost much more at one lot: MELI 24% of the account, SNDK 18%, MPWR 17%, TDG 16%, LITE 12%,
REGN 12%, FICO 11%, STX 9.5% (spot × the 9.7% median implied move).

**Margin needed, % of equity.** A butterfly is held from the gate (S) to the reaction-day exit (R). The low figure
assumes the day's closes fill before its opens; the high one counts everything alive in the 14:30–15:55 window.

| day | butterflies alive | main: margin | second: straddle cost | main: T0 stock notional |
|---|---|---|---|---|
| Mon Oct 26 | 29 | 63% | 47% | 14% |
| Tue Oct 27 | 60 | 124–140% | 105% | 45% |
| Wed Oct 28 | 70 | 151–197% | 147% | 81% |
| Thu Oct 29 | 53 | 75–153% | 114% | 80% |
| Fri Oct 30 | 43 | 42–115% | 86% | 35% |
| Mon Nov 2 | 53 | 98–100% | 74% | 38% |
| Tue Nov 3 | 96 | 157–197% | 147% | 80% |
| Wed Nov 4 | 107 | 152–210% | 157% | 119% |
| Thu Nov 5 | 83 | 60–159% | 119% | 123% |
| Fri Nov 6 | 42 | 13–67% | 50% | 58% |

Options buying power is about the equity (D011 §2 probe: ~$98k). The main account also carries DPZ's 100
assigned shares (~$30k) and the T0 stock buys. Those are 5.2% of equity per PASS, held open to open, at 50% RegT.

**Refused opens, simulated day by day.** Closes free their margin first. The day's opens then go in the code's
order (gate paths, i.e. alphabetical by ticker) until buying power runs out. A refused open holds nothing later.

| S2 day | butterflies wanted | main refused, DPZ held | main refused, DPZ flat | second refused |
|---|---|---|---|---|
| Tue Oct 27 | 31 | 25 | 12 | 0 |
| Wed Oct 28 | 19 | 8 | 6 | 2 |
| Mon Nov 2 | 29 | 27 | 13 | 0 |
| Tue Nov 3 | 46 | 26 | 26 | 12 |
| Wed Nov 4 | 32 | 32 | 11 | 0 |
| **Oct 27–Nov 11** | **204** | **118 (58%)** | **68 (33%)** | **14 (7%)** |

### `held_by_cap` as an outcome
- The code's own cap can no longer bind. That cap (`UNVERIFIED_OPEN_CAP`, 3 opens before the sign convention is
  verified) is what `held_by_cap` labels, and `convention_verified` is set in both ledgers.
- The cap that binds is Alpaca's buying power, labelled `open_failed: capacity`. D011 §7: never simulated, "the
  account's real capacity". This is D011's own question 3, and the answer is **no**: at the 1-lot floor the
  account can't carry a peak day.
- Count it per S2 day as an outcome, next to `platform` and fills. The hash-locked report views
  (`D011_report_views_implementation_v1`) fold it into "open_failed: other". **Owed:** split `capacity` out in the
  next report-views version. Until then the per-trade rows show it.
- **The refusals are not random.** They fall on late-alphabet tickers on busy days, and on dear names when
  buying power is near the edge. The peak-day paper sample leans toward cheap, early-alphabet names. Disclose this
  next to every D011 execution figure.
- **T0 stock hides it.** `paper.py` books any refused buy as simulated at the official open, the platform rule. A
  buying-power refusal is booked as if the account had carried it. **Owed:** label those refusals `capacity` in
  the next paper.py version.

### What can change it (Jacob's call)
1. **Flatten DPZ before Tue 14:30 ET** (waiting since Oct 19). That halves the main account's refusals, 118 → 68.
2. **Season B, a D011 version with a larger paper balance** (e.g. $1M): the 1-lot floor then binds only above a
   $50 straddle. Each structure falls to ~0.7% of equity, and the Nov 4 peak needs ~80%. A balance reset wipes
   open positions, so it is for between seasons only. It's a new rule version with its own clock.

## 3. The AI allowance (Pro, weekly all-models; resets Mon 06:00 UTC)

- **Per call** (`logs/t2`, 34 decided calls): ~21.4k input tokens, then ~1.0k output (Sonnet 5.5) or ~1.5k (Opus
  5.5). A PASS name is 3 decisions plus 3 short probes, ~66k in + 3.5k out.
- **Routine sessions per week on this account:** t2-cloud 28 and t2-models 28 (Haiku 4.5; they call Sonnet or Opus
  only when a name waits), s2-trigger 20, paper-trigger 14, housekeeping 5 (Sonnet 5.5), about **95**. Jacob's
  other routines draw on the same allowance. One is a weekly Opus 5.5 brief, last fired Sun Oct 25 14:40 UTC,
  inside the Sun 10:22–21:21 UTC window when the limit ran out.
- **Laptop chats are the largest draw.** The week-plan chat took weekly use from 12% (09:20 ET) to ~20%. This chat
  took it 20% → 21% (5-hour 49% → 56%) in 42 minutes, ~25 calls at 100–190k context.
- **Measured cost of one PASS name:** _filled in after tonight's 17:20 and 17:50 ET fires (5-hour and weekly
  readings before and after, this chat idle)._

## 4. Timing at the peak
- **Gates:** 8 gates were captured in 11–14 s (Oct 20, 21, 23). 55 take ~1.5 min of the 80-minute window.
- **T2:** calls run 17–29 s apart, so 14 PASS names take ~5 min per backend.
  - `t2_stage2` has no per-run cap.
  - `t2_models` caps at 12 per backend per run. Tue Nov 3 (14 expected, up to ~20) spills to the 01:50 UTC fire
    (20:50 EST). The 05:50 and 10:50 UTC fires follow, all before 09:15 EST.
  - The weekly cap of 80 per backend clears the peak week's ~36.
- **After DST** (from Mon Nov 2): the 21:20 UTC fire is 16:20 EST, 30 min after the S2 window closes at 15:50 EST.
  The 10:20 UTC fire, 05:20 EST, is the fallback before 09:15.
- **C1:** window 15:25–15:55 ET, retry passes until every name settles. Oct 21 had 91 names and used 29 passes, to
  the window's end. The shadow calendar lists 316 prints for Oct 29 and 292 for Nov 3 (before C1's filters). Watch
  the settled count on peak days (`shadow_c1.py status`, counts only).
