# HYPOTHESES — every test this experiment runs, in one place

> A **map, not a rule**: the registry file named in each row wins on any detail. Kept current by the session
> that changes a test. Consolidated 2026-10-20 from `registry/` D001–D015. Counts as of Season A week 2.
> **"Insufficient"** (rule 7): under 30 events AND 10 event-dates no verdict is given, in either direction.

## 1. Confirmatory tests — pre-registered; a verdict counts

| # | test | the question, in plain words | sample | verdict | rule |
|---|---|---|---|---|---|
| 1 | **H-S0** | Does **buying every gated event** at the open before the print and selling at the first open after it pay, net of 0.20%? ("the earnings premium") | gated S2 events | **Gate 2** (Mar 2027) | D008 |
| 2 | **H-M** | The same premium, market-wide (every ≥ $2B reporter, any industry) | SH-M, ~1,300 a season | A + B pooled | D009 v1, Holm m = 3 with 3–4 |
| 3 | **H-X** | Does **selling the earnings straddle** (short volatility over the print) pay? | SH-X (gated events' quotes) | A + B pooled | D009 v1 |
| 4 | **H-VOL** | Is the premium bigger for stocks that were volatile beforehand? (found on history: a candidate) | SH-M | A + B pooled | D009 v1 |
| 5 | **H-MY** | Is the premium there all year, off-season prints included? | SH-M + SH-MO from 2026-10-05 | pooled | D009 v2 |
| 6 | **H-RU** | Do stocks **run up in the 20 sessions before** the print (beta-adjusted)? | SH-RU | A + B pooled | D009 v3, Holm m = 2 with 7 |
| 7 | **H-RU-AIH** | The same, AI-hardware names only (a candidate from the DRIVE chat) | SH-RU AI hardware | A + B pooled; "insufficient" is the stated expectation | D009 v3 |
| 8 | **H-XT** | Does the short straddle pay when **both legs are liquid** (spread ≤ 10%)? | SH-X ∩ tight spreads | A + B pooled | D012 |
| 9 | **H-T2C** | Does **T2's (the AI's) confidence predict the win**? (calibration) | gated PASS events with T2 | A + B pooled; **never on Season A alone** | D005 v3 |
| 10 | **H-C1** | When a stock gaps more than its options-implied move before the open, does **fading the gap** pay over the first 30 minutes? | every SH-M event with an implied move | look 1 from **Dec 7** (A, p < 0.005); final A + B (p < 0.045); **blind until then** | D015 |

**Uncomfortable, and new:** these are 10 hypotheses in **7 separate families**, each corrected only inside itself.
If every null were true, the chance of at least one false "works" across the seven is up to about 30% (1 − 0.95⁷). See idea A
below.

## 2. Live descriptive and shadow tracks — measured, decide nothing on their own

| track | what it records | why | rule |
|---|---|---|---|
| **T0 / T1 / T2** on gated events | buy-all · the frozen T1 rule v0 (R-LIT, which *failed* validation, frozen anyway) · the AI's decision | RQ3, RQ5; lift vs T0 is exploratory in Season A | D004 v4, D005 v2 |
| **T2G, T2E** | Gemini's decision; the mean of T2 and T2G | ensemble calibration (I2) | D004 v4 |
| **T2R, T2O, T2M** | a Sonnet re-run (test–retest); Opus; the mean of three | model choice, stability | D013 |
| **SH-W** | T0-wide: every allowlist event, gate or no gate | power for T0 | D009 v1 |
| **SH-MO** | the market-wide shadow off-season | feeds H-MY | D009 v2 |
| **Paper F** | short iron butterfly on Alpaca paper, every gate, real order mechanics | can H-X be *executed*? (RQ6) | D011 v1/v3 |
| **Paper L** | long straddle, a second paper account | the mirror of F | D011 v2 |
| **Paper shares** | T0 shares at the open | fills vs the official open (RQ6) | paper.py |
| **Exit audit, report views, fill re-check** | on-time counterfactual; P&L at fill/mid/halfway/far; real prints | truth about paper fills | D011 audit, views |
| **Open-fill trigger** | first 6 opens per account: filled at 0 / 1 / platform | decides whether opens get the v3 ladder | D011 trigger |

## 3. Closed studies — answered, kept as negative knowledge

| study | question | answer |
|---|---|---|
| D006 (history) | Which literature factors select winners? | **No factor cleared t > 3**; the composite R-LIT failed validation (−0.7 pts). Buy-all won 54% |
| D007 (history) | 20 new signals vs buy-all | **None beats buying everything** |
| D010 v1/v2 (options history) | Does either side of the straddle pay after costs? | **No, after costs**. Short at mid +1.13% on liquid names (post-hoc → became H-XT). Holding to expiry gives it back. The IV spread (LR12) is no selector |
| D014 v1–v3 (first hour) | Patterns in the first hour after the print | **None validated**. C1 failed validation (−0.8%, n 62) → became H-C1 on fresh data |
| Pilot | Does the pipeline work? | Yes, after the scheduler fixes. 5 events lost to cron in September |

## 4. Candidates — not registered; the backlog plus the 2026-10-20 brainstorm

Ranked by charter lever (power, then truthfulness, signal, calibration, speed) × prior × cost. Rule 6: anything
found on history is a CANDIDATE. It goes live only as a pre-registered shadow, with its own family.

| # | idea | lever | evidence / prior | cost | verdict |
|---|---|---|---|---|---|
| **A** | **One global multiplicity view.** Report a Holm (and BH) across all 10 confirmatory tests beside each family's own verdict, registered as a *secondary* | truthfulness | arithmetic: 7 families at 5% each ≈ up to 30% chance of one false positive | tiny | **registered** in D017 §6 (2026-10-29), before any outcome look |
| **B** | **D016 gate audit → D003 v5 for Season B.** Season A's gates pass few names (2 PASS of 7 so far). Counts only | power (RQ3, RQ5) | 4/4 early Season A gates failed `wide_spread`; only RTX was a near-miss | small | **do this week** (plan) |
| **C** | **Busy-day attention.** On days with many reporters, the open reaction is smaller and more is left for later | signal | Hirshleifer, Lim & Teoh 2009 ("Driven to Distraction"); data already captured (calendar captures, D006/D014 history) | low | **explore on history, then a live SH-M shadow** |
| **D** | **Industry read-across.** The first reporter's reaction predicts its peers' reactions days later | signal (RQ2) | intra-industry information transfer (Foster 1981; Thomas & Zhang 2008 find later reporters overreact) | low: SH-M has industry and dates | **explore on history** |
| **E** | **Estimate revisions before the print** (EPS-trend 7/30/60-day change at the snapshot) | signal | revisions predict surprises; the premium link is weaker | low, but **live-only**: no free history, so it must start capturing now to matter by Gate 2 | **start the capture now, test later** |
| **F** | **Attention from Wikipedia pageviews** (free, history back to 2015) before the print | signal | announcement-volume premium (Frazzini & Lamont); retail attention | moderate | explore on history |
| **G** | **Implied move rich vs the stock's own past moves** (I5) as an H-X conditioner | signal (RQ4) | the straddle premium is documented; history in D010 | moderate | explore on D010 data |
| **H** | **An auth refusal is retried, not counted** (T2 attempt cap) | truthfulness | ABT and SPCX lost T2 this way | small, but it **changes `t2_stage2.py`**: only in a new D004 version with its own clock | at the next D004 version |
| — | Not worth it now: post-earnings drift in large caps (gone since ~2006), news-sentiment NLP (costly, weak), more T2 models (shadows cover it) | | | | |

**Order of work:** A (done), B (this week), E (start the capture), then C and D as one history exploration batch
(D018; D017 became the Stage 1 review) with FDR control and t > 3, then F and G.
