# PRE Stage 1: the committee's decision

<div class="verdict">
<div class="lab">Decision · confidence about 85% after PRE's answers</div>
<div class="big">B · REFRAME: end PRE as a trade picker; keep a code-only premium monitor with fixed kill dates</div>
<p>No money goes to it now. Stop the selection research, the paper options and the extra AI shadow tracks. Keep only the automated measurement of the one open question: does buying broadly before earnings pay after costs Jacob would actually pay? It stops at Gate 1 (early Dec) or Gate 2 (Mar 2027) unless the bars below are met.</p>
</div>

> Independent committee review of the Earnings Experiment ("PRE"), written from its repository (GitHub `main` as of
> 2026-11-03 ~08:00 ET), its Stage 1 deck, its PRE v1 archive and three DRIVE lab results. PRE wrote none of this.
> Figures marked *committee recompute* were recomputed here from PRE's raw files (scripts kept with the hand-over
> notes); every other figure cites PRE's own file. Per-name outcomes and any T2-confidence-vs-outcome view are
> deliberately left out: they would break PRE's D017 §4 firewall and its registered H-T2C test.

## 1. Executive decision

**PRE does not deserve continued funding in its current form.** Its central idea, picking earnings trades with
an informational edge, has now failed in two separate records:

- **PRE v1** (Jul–Sep 2026) was the research-driven, conviction-graded forecaster this mandate describes: 27 blind,
  pre-registered calls, 14 right (51.9%, p = 1.00 against 50%). It closed on 2026-09-13 because its scoring stack was
  edited four times inside its own measurement window.
- **The Earnings Experiment (v2, since 2026-09-13)**, which the slides describe, tested selection on 2,771 historical
  prints. No literature factor cleared t > 3; the composite rule failed validation (−0.7 pts); none of 20 new signals
  beat buying everything; the call–put IV spread selected nothing; no first-hour pattern validated. Options lost on
  both sides after bid/ask in history and in paper trading.

What is left is not a picker. It is a **passive premium**: history says buying every eligible stock at the open
before its print and selling at the next open earned +0.85% raw (+0.65% net of 0.20%). Three things make that number
weak:

1. **The sample was chosen with hindsight.** The history universe is the companies worth ≥ $2B on 2026-09-28
   (`analysis/history/universe.json`). Firms that shrank or delisted after bad prints are missing. That is selection on
   the outcome, not just "today's listed companies".
2. **The live record contradicts it on every interval method, and the deck understated that.** Stage 1 ran before
   the Fri 10-30 exits had been graded, and `stage1.py` dropped them without a word. That left out the 10-29 entry
   session, the season's worst, although D017's cut includes it. PRE confirmed this and re-ran it (r2, `4fa6d03`). On the correct cut:
   - SH-W is **−1.50% net** (n 104, 9 sessions), and every 95% upper bound (normal, t, session bootstrap,
     wild-cluster) is below history's +0.65%;
   - gated S0 is −5.34% net (n 21);
   - market-wide, survivor-free SH-M is −0.18% raw (n 696, 14 sessions).

   Only the session count (9, the rule needs 10) stops D017 from printing CONTRADICTS HISTORY.
3. **An independent study points the same way.** DRIVE's lab (T22, reviewed) found that a print inside a multi-week hold
   adds variance in both tails, not mean return, on 2019–2026 data.

At Jacob's size the trade cannot pay even if history is right. moomoo SG charges US$0.99 per order and has no
market-on-open orders. PRE's open-to-open trade cannot be placed as specified, and a ~$600 position pays ~0.32% in
platform fees. On top of that, PRE's own paper fills lose ~0.9% a round trip, almost all of it selling into the
post-print open, against the 0.20% the study assumes.

**The reframe keeps what is cheap and informative:** the code-only market-wide measurement that already runs in
GitHub Actions, re-defined on a trade Jacob can place (close before the print → close of the reaction day). Its kill
criteria are fixed in §12 before any further data is read.

| outcome | committee's probability it is the right call |
|---|---|
| **B · REFRAME** (recommended) | ~85% after PRE's answers (~80% before) |
| A · TERMINATE outright | ~12% |
| C · continue as is, smaller | ~3% |
| D, E, F (shadow, live pilot, integrate) | ~0%: no edge to shadow, pilot or integrate |

## 2. Current model assessment

### What PRE actually is

| | PRE v1 (closed 2026-09-13) | Earnings Experiment, Season A (the deck) |
|---|---|---|
| question | will this stock move the way our research says? | does buying before the print pay, and can a rule (T1) or an AI (T2) beat buying everything (T0)? |
| method | dossiers, a scoring stack, conviction tiers, direction calls | a frozen universe (D003), an options-liquidity gate (implied move ≥ 4%, spreads, open interest), T0/T1/T2 decisions frozen and timestamped before the open, code grading at the next open (D001) |
| record | 27 calls, 51.9%; separation −1.86 pp (t −0.50) | history 2,771 prints; live: 16 gated graded, 84 SH-W, 596 SH-M (cut 10-30) |
| status | archived byte-exact | INTERIM; Gate 1 early Dec, Gate 2 Mar 2027 |

The deck describes the second column. **Jacob's mandate describes the first.** The research-driven high-conviction
model he is asking about is the one that already failed and closed.

### Strongest components

- **Truthfulness machinery is excellent.** Every decision is hashed, committed and RFC-3161 timestamped before its
  entry open (454 tokens, 0 late), VOID 0 of 16, code grades, rules are versioned not edited, and failures are
  journalled. The 2026-09-21 external review called the blindness machinery "unusually strong". The committee agrees:
  PRE's numbers can be believed.
- **Negative knowledge is real and banked.** D006, D007, D010 and D014 answered four questions with frozen procedures
  and reported "no" when the answer was no.
- **Self-criticism.** The deck shows its own near-miss and the small-cluster caveat. Few research teams would.

### Weakest components and major concerns

| # | concern | why it matters | evidence |
|---|---|---|---|
| 1 | **Hindsight universe in the only positive evidence** | inflates the premium by an unknown amount, possibly most of it | `universe.json`: "2026-09-28 market data", size floor |
| 2 | **The premium is a right-tail effect** | the top 5% of events carry 141% of the total return; without them the mean is −0.37% | *committee recompute*, `legs_exploratory.json` |
| 3 | **Regime-dependent** | by year: 2023 −0.57%, 2024 +1.02%, 2025 +0.43%, 2026 +1.54% (a strong, AI-led market) | *committee recompute* |
| 4 | **Gate 2 has ~25–40% power** | H-S0 on ~250 gated events gives a real premium an expected t of ≈ 1.05 on the net mean (1.4 on the raw); Gate 2 is closer to a coin flip than a test | D017 §1 arithmetic: 0.066 × √250 net, 0.087 × √250 raw |
| 5 | **Not executable as specified for Jacob** | open-to-open needs market-on-open orders; moomoo SG has none | broker facts; D001 |
| 6 | **The cost assumption is ~4.5× too low** | signed paper slippage: buys −13 bp (slightly favourable), **sells at the post-print open +105 bp (20 of 23 adverse)**; round trip **+92 bp vs the 20 bp assumed**. Stage 1 reported only the absolute 27.5 bp median | *committee recompute*, paper ledger (Alpaca simulator fills) |
| 7 | **Scope creep** | 10 confirmatory hypotheses in 7 families, 6 AI tracks, 2 paper options accounts, ~1,687 commits in 7 weeks; the allowance hit 85% by Thursday of week 26 Oct | HYPOTHESES; git log; JOURNAL 10-29 |
| 8 | **No termination rule** | D017 §5 and D008 only withhold money. Nothing ever stops the research, which is how it keeps growing | D017; D008 |
| 9 | **Layer 1 is absent** | no EPS or revenue surprise forecast is recorded, so "wrong about the numbers" can't be told from "wrong about the reaction" | D004 v4 |
| 11 | **Stage 1 dropped ungraded events silently** | the run (Mon 11-02 07:28 ET) read the newest grade, `c2dc357` (Fri 10-30 21:52 ET), made before Friday's exit opens were fetched, and `stage1.py` did not report the gap. PRE confirmed and fixed it (`4383102`, `a6f7cc6`, r2). It omitted 20 SH-W, ~100 SH-M and 5 gated events inside D017's own cut; the corrected read is materially worse (§5). Verified: `graded.json` holds 129 graded 10-29 prints at `c2dc357` and 227 at `4d9affc` | *committee recompute*; git |
| 12 | **Health counter defect, still in the output** | the report prints "T2 missing 0 of 26"; ABT and SPCX have no `t2.json`, so it is 2 of 26 (7.7%). It also says "T2 none recorded" for cost, but `t2.json` records ~$0.097 a decision | stage1 P1, P6; the deck already flags the first |
| 10 | **Mismatch with what the funder needs** | the mandate asks for about one attractive trade a month; a 1-day, 10%-SD coin with a small tilt only pays in bulk (§5, §6) | mandate §8; CHARTER §5 |

**Hindsight and selection bias in the deck:** none found in the live record. Every freeze precedes its open, and
D017 was frozen before any Season A outcome was read. The bias is in the historical premium the deck uses as its bar.

## 3. Academic and industry research findings

**Bottom line: the literature puts PRE's trade, a long one-day hold into the print, at about zero or less after a
0.20% cost today.** At its historical best, the academic premium inside that window was about 0.1–0.2% gross per
event. PRE's history (+0.85% raw) is 4–8 times the largest comparable published figure, in a period two recent
studies say has no premium.

### The premium inside PRE's window (day t−1 plus the overnight gap)

| paper | status | sample | finding in PRE's window | applies to PRE? |
|---|---|---|---|---|
| Johnson & So, "Asymmetric Trading Costs Prior to Earnings Announcements" | JAR 56(1), 2018 | 1993–2012, 215,754 announcements, AMC dates corrected | t−1 **+0.18%** (t 7.7); reaction day +0.04% (n.s.); no window significant in 2007–2012 | **yes**, the closest match; the effect fades in the recent subperiod |
| Lamont & Frazzini | NBER WP 2007 | 1973–2004, above-median caps | +0.089% on day −1 and on day 0; only 0.21% of a ~0.76% monthly premium falls in the 3 days | yes; tiny per event |
| Cohen et al. | 2007 | expected-date windows | ~0.05%, smaller after 1988 | yes |
| Barber, De George, Lehavy & Trueman | JFE 108(1), 2013 | global | an announcement-month premium exists across countries | partly: monthly, not one day |
| Savor & Wilson | JF 2016 | US | announcers earn ~9.9% a year more (portfolio premium, systematic risk) | partly: a long-run portfolio premium, not a one-day trade net of costs |
| Heitz, Narayanamoorthy & Zekhnini | SSRN, rev. 2025 | pre/post 2004 | weekly premium 32.6 bp before 2004, **23.9 bp lower after** (the 2004 8-K rule) | yes: decay |
| Heater et al. | Contemporary Accounting Research 2025 | 1993–2021 | 3-day announcement return **+0.30% in the 1990s → −0.30% in the 2010s**, negative for 17 years | **yes: reversal** |
| Gutierrez & Pfiffer | WP 2024 | 1995–2022 | ~+0.40% in the announcement week, **only in the first three weeks of each season**; late reporters earn nothing | yes: a conditioner PRE could check at no cost |

### Predicting the surprise, the reaction and the instrument

- **Surprise ≠ return.** The market now expects a beat of 1–2 cents over consensus. The realised surprise explains only
  ~3–4% of announcement-day return variance (Wu et al. 2025). Predicting EPS well buys little.
- **Selection signals exist but are small, mostly long-short and mostly pre-2012.** They decay ~58% after publication
  (McLean & Pontiff 2016). The best fit to PRE's window is So & Wang (JFE 2014): pre-announcement losers beat winners
  by 145 bp over t−1 to t+1, falling to ~0.45% in an unrefereed 2007–2016 replication. PRE's own H1 (12-month losers,
  t 2.56) points the same way and also failed the bar.
- **LLMs:** no peer-reviewed paper shows a prompted general LLM beating buy-all before a print.
  - Kim, Muhn & Nikolaev was **withdrawn by its authors (2025-02-20)**.
  - Lopez-Lira & Tang (JFE 2026) reads headlines after the news; it does not forecast prints.
  - Gao, Jiang & Yan (WP) show memorisation collapses after a model's training cutoff, which supports PRE's
    forward-only T2 design.
  - The best post-cutoff hint is one fine-tuned-model working paper (Frey & Pukthuanthong 2026): ~1 pp long-short,
    before costs.
- **Sample size:** detecting a 0.3–0.5 pp selection improvement at two standard errors needs roughly 800–2,200
  independent events.

### Options around earnings

| paper | status | finding | implication for PRE |
|---|---|---|---|
| Gao, Xing & Zhang, "Anticipating Uncertainty: Straddles around Earnings Announcements" | **JFQA 53(6), 2018** (not Management Science) | the gain is the **pre-event** volatility ramp (+1.9% to +2.6% EW, mid quotes, no costs); value-weighted, straddles held **through** the print earn nothing; the day after is −1.37%; IV 0.532 → 0.491 | holding through the print, as PRE does, is the wrong side of this result |
| Dubinsky, Johannes, Kaeck & Seeger | RFS 32(2), 2019 | options price a distinct announcement jump | the implied move is information about size, not direction |
| Alexiou, Goyal, Kostakis & Rompolis, "Pricing Event Risk: Evidence from Concave Implied Volatility Curves" | **Review of Finance 29(4), 2025** (abstract read) | a concave IV curve flags a larger event move | a sizing input at most |
| de Silva, So & Smith, "Losing Is Optional" | **Review of Finance 2025** | retail option buyers lose 5–9% around announcements, 10–14% on high-volatility names | the long straddle (PX-L) is the losing retail trade |
| Hosseinkhani & Hosseinkhani, "Directional Options Demand Around Earnings Announcements" | **Borsa Istanbul Review 2026** (abstract only; effect sizes not read) | directional options demand around announcements | unverified magnitude; do not rely on it |
| Milian | weekly options, 2014–2017 | through-print straddles +0.48% (n.s.), **median −17.7%**; implied move 5.72% vs historical 5.07%; half-spread 7.4% of premium | spreads swamp the edge, as PRE's paper record shows |
| Muravyev & Pearson | RFS 2020 | timed executions pay < 40% of conventional effective-spread estimates | the only way spread costs shrink is patient execution, not a market order at the open |

### Market structure and post-print trading

- **Post-earnings drift has been gone outside microcaps since ~2006** (Martineau, Critical Finance Review 11(3–4),
  2022).
- The slow after-hours quote drift is not profitable (Grégoire & Martineau).
- Only an unrefereed paper finds overnight and intraday moves after surprises running in opposite directions, the
  premise behind C1.
- Chen & Zimmermann's open-source anomaly library (331 signals) carries no announcement-premium signal.

### What it means for PRE

- Every peer-reviewed number in PRE's window is an order of magnitude below its history estimate, and the recent
  ones are zero or negative.
- PRE's history premium is far more likely to be hindsight universe, survivorship and a strong 2024–26 tape than a
  live edge.
- Selection and options both match the literature's negative findings.

**Not verified:** the full texts of Ball & Kothari, the bodies of Barber et al. and Savor & Wilson (2011 drafts
only), So & Wang's sample period (third-party source), and the papers in the 2025 dispute over post-earnings drift.
No paper isolates 2020–2026 or covers 0DTE single-stock options around earnings.

## 4. Predictive edge assessment

### The three layers, separately

| layer | question | PRE's evidence | verdict |
|---|---|---|---|
| 1 · fundamentals | can it predict the EPS or revenue surprise? | not recorded in v2; v1 did not score it | **untested** |
| 2 · market reaction | can it predict the direction of the reaction? | v1: 51.9% (n 27, p 1.00). v2 T2: 9 BUYs, −1.64% vs −2.83% for all (INSUFFICIENT). v2 T1 (failed validation): 11 BUYs, +0.42% vs −2.91% (INSUFFICIENT) | **no skill shown**; the only record of size says none |
| 3 · instrument return | does the chosen instrument pay? | equity buy-all: live −1.50% net (correct cut); options: both sides negative after spreads | **negative so far** |

### Factor ledger: what to keep and what to remove

| factor (source) | mechanism | measured result | keep? |
|---|---|---|---|
| H1 12-month winner (D006) | losers mean-revert into prints | +2.95 pts, t 2.56, q 0.06 (TRAIN) | remove: candidate only, 1 of 10 at the edge of chance |
| H2–H10 (D006) | pressure, MAX, volatility, volume, SUE, seasonality, value, late scheduling, profitability | no factor t > 3; H10 and H3 had the wrong sign | remove |
| R-LIT composite (T1 rule v0) | average of the 10 | −0.2 pts TRAIN, −0.7 pts VALIDATION | remove (keep the frozen live record) |
| 20 new signals (D007) | short pressure, peers, regime, attention, busy days … | none beats buy-all | remove |
| call–put IV spread (D010 Z1–Z3) | option demand leads stock | not significant | remove |
| first-hour patterns (D014) | post-print overreaction | none validated; C1 −0.8% on validation | keep C1's registered look only (code-only) |
| implied-move gate (D003) | screens for liquid, high-variance names | a liquidity and variance screen, not a signal; passes 8 of 31 | keep as a filter |
| cluster (business type) | different reaction regimes | semis lost (47.9% hit) in history; descriptive | label only |
| busy-day attention (Hirshleifer et al. 2009) | distracted market under-reacts | +1.02% vs +0.45% in history, descriptive | do not open D018 |
| T2 AI judgment | an LLM reads a code-built dossier | INSUFFICIENT; 64–80% agreement across models | stop after Season A (see §12) |
| print-in-hold as a **risk** label (DRIVE T22) | event variance | both tails +~3 pp, mean ~0 | **keep, in DRIVE** (already there) |

**Interactions and ablation.** The data cannot support an ablation: no single factor has shown value, so removing one
cannot make the model measurably worse. Requiring several conditions together cut the gated sample to 26% of
candidates (D016) without any evidence of better accuracy. The factors also overlap: H1, H4 and H3 all load on past
volatility, and the gate itself is a volatility screen (external review 2026-09-21, finding 13).

**Established vs hypothesis.**
- Established (on PRE's own data, history only): a positive mean overnight reaction in a survivor sample, 2023–26.
- Hypotheses: all 10 confirmatory tests.
- Not supported: every selection layer, both option sides, and conviction.

## 5. Trading economics

### The candidate strategies, after costs

| strategy | n | mean (raw) | after costs | win rate | source |
|---|---|---|---|---|---|
| Buy every print, open → next open (history, survivors) | 2,771 | +0.85% | +0.65% at 0.20% | 54.0% | D006 |
| — of which the session before the print | 2,771 | +0.05% (t 0.54) | — | — | *committee recompute* |
| — of which the overnight print gap | 2,771 | +0.79% (t 3.93) | — | — | *committee recompute* |
| Buy every print, live SH-W (Stage 1 set; correct cut below) | 84 / 8 sessions | −0.56% | −0.76% | 48.8% | stage1 P2 |
| Market-wide, live SH-M, no survivorship (Stage 1 set) | 596 / 13 sessions | −0.08% | −0.28% | 48.7% | stage1 P2 |
| Gated S0, live (Stage 1 set) | 16 / 6 sessions | −2.11% | −2.31% | 43.8% | stage1 P2 |
| **Close before print → close of reaction day** (moomoo-executable), history on options-liquid names | 1,249 (1,086 in 2025–26) | +1.57% (t 5.5) | about +1.3% at 0.20% | 54.2% | *committee recompute*, `analysis/d010/events_valid.csv` |
| Long straddle, end-of-day, bid/ask | 1,249 | — | −4.03% per $1 of spot | 18.0% | D010 X2 |
| Short straddle, bid/ask | 1,249 | +0.40% at mid | −3.22% per $1 of spot | 32.7% | D010 X1 |
| Paper long straddle (PX-L) | 76 / 8 dates | +0.82% at mid | −1.33% at the fill | — | stage1 P4 |
| Paper short iron fly (PX-F) | 62 / 8 dates | −1.34% at mid | −4.76% at the fill | — | stage1 P4 |

### The live reads on the correct data cut

The committee rebuilt every live figure from PRE's raw files, independently of PRE's code. The per-event returns
match PRE's stored returns exactly, and PRE's Stage 1 numbers reproduce exactly on the set it used. That set is
missing the 10-29 entry session (concern 11).

| read | Stage 1 as published | **correct cut (exit-A open ≤ Fri 10-30)** |
|---|---|---|
| SH-W | n 84, 8 sessions, raw −0.56%, net −0.76%, win 48.8% | **n 104, 9 sessions, raw −1.30%, net −1.50%**, win 49.0% |
| S0 gated | n 16, 6 sessions, net −2.31% | **n 21, 7 sessions, net −5.34%**, win 33% |
| SH-M | n 596, 13 sessions, raw −0.08% | n 696, 14 sessions, **raw −0.18%**, net −0.38% |
| T1 BUYs vs all | +0.42% vs −2.91% (11 BUYs) | −1.86% vs −5.89% (13 BUYs); T1 already failed validation on history |
| T2 BUYs vs all | −1.64% vs −2.83% (9 BUYs) | −3.95% vs −5.99% (11 BUYs); BUY minus NO_BUY +4.8 pts, Welch p 0.35 |

SH-W net mean, 95% intervals:

| method | Stage 1 set | correct cut |
|---|---|---|
| normal, ±1.96 SE (D017) | [−2.00%, +0.48%] | [−3.28%, +0.27%] |
| t, clusters − 1 df | [−2.25%, +0.73%] | [−3.59%, +0.59%] |
| session bootstrap | [−2.56%, +0.29%] | [−3.56%, −0.02%] |
| wild-cluster | [−3.69%, +0.75%] | [−4.33%, +0.46%] |

On the correct cut, the small-sample t interval the deck used to soften its near-miss also sits below +0.65%. The
wild-cluster p-value for a true mean of +0.65% is 0.039.

- **Moomoo-executable legs, gated events (n 21):** close before the print → close of the reaction day **−6.44%** (19%
  win); exit B −6.62%. The shadow files carry no daily closes, so this read cannot be made on SH-W or SH-M yet.
- **T2's confidence:** not shown. D017 §4 and the registered H-T2C test hold it to Gate 1. The committee computed it
  and keeps it out of this repository so the test stays clean.
- **Integrity spot-check:** LRCX, MXL, QSR, TXN and WDC (random) were frozen 12–16 h before entry. DigiCert
  timestamps match their commit times to the second, and the hash chain to `t2.json` is intact. All 21 gated entry and
  exit prices equal the official open, with 0 Alpha Vantage disagreements.

### The payoff shape (history, one print held)

- **Expected value per trade:** 0.540 × 7.48% − 0.460 × 6.91% − 0.20% = **+0.66%**. That is the +0.65% net, so the
  arithmetic checks.
- **Break-even win rate:** 49.4% after 0.20% cost. Live SH-W wins 48.8%.
- **Profit factor:** 1.27 gross.
- **Per-event SD:** 9.8%, so the per-event Sharpe is 0.066 net.
- **Tails:** 1 print in 10 loses ≥ 10%; p1 −24.2%; worst −48.3%; CVaR 5% −20.6%.

A small tilt on a big coin, as PRE's own plan says.

### Costs at Jacob's size (moomoo SG: $0 commission, US$0.99 per order)

| position size | platform fees, round trip | plus measured signed paper slippage (+0.92%) | left of history's +0.85% raw |
|---|---|---|---|
| $300 | 0.66% | 1.58% | **−0.73%** |
| $625 (0.5% risk ÷ 8% implied move on $10K) | 0.32% | 1.24% | **−0.39%** |
| $1,000 | 0.20% | 1.12% | **−0.27%** |
| $6,250 (same rule on $100K) | 0.03% | 0.95% | **−0.10%** |

**At the measured execution cost, history's whole premium is gone at every account size.** The slippage is
Alpaca's simulator (market orders 09:30–09:34 ET), not a real broker, and the sell side carries almost all of it:
selling into the post-print open is expensive. An MOC exit at the reaction-day close avoids that auction. On the 21
gated events it returned −6.44%, too few to judge.

### What it is worth a year

- **The broad harvest**, ~150 gated-size events a year, equal-risk sizing (annual SD ~7.5% of equity):
  - at history's raw premium with the 0.20% PRE assumes: about +$600 a year on $10K and +$6,100 on $100K;
  - with Jacob-scale fees and the measured paper slippage: about **−$370** on $10K and **−$940** on $100K;
  - at the live SH-M mean (−0.18% raw) and the same costs: about −$1,330 and −$10,600.
- **The one-trade-a-month format Jacob proposed (mandate §8)**, simulated from the history distribution (20,000 runs,
  *committee recompute*): the median year is **+0.7% at a 10% position**, and **42% of years end down**, even
  if history's premium is real.

| premise | position | median year | 5th-percentile year | P(year ends down) | P(drawdown ≥ 20%) |
|---|---|---|---|---|---|
| history +0.65% net | 10% | +0.7% | −4.6% | 42% | 0.0% |
| history +0.65% net | 25% | +1.6% | −11.6% | 42% | 0.6% |
| history +0.65% net | 50% | +2.4% | −22.7% | 44% | 16.4% |
| zero premium | 25% | −0.5% | −13.3% | 52% | 0.8% |
| Stage 1 live mean (−0.76% net) | 25% | −2.5% | −15.1% | 62% | 1.5% |
| Stage 1 live mean (−0.76% net) | 50% | −5.7% | −28.7% | 64% | 29.1% |

**Statistical vs economic significance.** History's t of 3.6 is statistically significant. Economically, the
premium is a fraction of one percent against a 10% coin, it needs breadth to matter, and breadth in a small account is eaten by
per-order fees. **Options:** they lose on both sides after real spreads. The straddle spread alone costs about 2.2% of
spot per round trip (PX-L: +0.82% at mid → −1.43% at the natural). A strategy that is positive only at mid
(PX-L) is classified **mid-only: not tradable**. Debit spreads were never tested by PRE, and nothing here suggests
they would escape the spread cost; they add a second leg's spread.

## 6. Opportunity frequency

| level | per month | per quarter | per year | source and confidence |
|---|---|---|---|---|
| prints in the allowlist universe (history, ≥ $2B) | 50–200 in 8 months; < 25 in Mar, Jun, Sep, Dec | ~230 | ~920 | history months, high |
| market-wide ≥ $2B (SH-M) | ~1,300 a season | ~1,300 | ~5,000 | D009, high |
| pass the options gate | 32 of 148 gated (21.6%) on 10 sessions so far | ~57 projected for Season A (plan: ~150) | ~230 | *committee recompute*; D016 (8 of 31) |
| genuinely independent | ~1 in 10 (84 events fell on 8 sessions) | — | — | stage1 P2, medium |
| **high-conviction with demonstrated edge** | **0** | **0** | **0** | v1 + D006/D007/T2, high |

**Verdict on the monthly hurdle:** in quantity it is met easily, 8 months a year. In quality it is not met at all:
there is no subset with evidence of an edge. Lowering the bar to manufacture one a month would breach principle 12.
Broadening the universe raises event counts but not edge. The only scalable version is the passive harvest, which is
a different product from what the mandate asks for.

## 7. Portfolio risk assessment

### Position sizing principles

1. **Size by risk, never by conviction.** Notional = risk budget ÷ the option-implied move (PRE's D008 rule). A
   conviction label earns influence on size only after its calibration is proven (Brier skill > 0 on ≥ 200 graded
   events). No label here has that.
2. **Kelly says zero.** With history's numbers, full Kelly is μ/σ² = 0.0065 / 0.0096 ≈ 68% of equity per print, absurd
   given the uncertainty. With the live estimate (μ ≤ 0) it is **0**. A strategy whose live interval includes zero gets
   no Kelly allocation.
3. **Cap simultaneous exposure.** Peak days carry 24–46 gates (STATE, week of 2 Nov). Cap gross notional opened on
   one session at 25% of equity, and treat names in one industry on one date as one bet.
4. **Equities gap; stops do not protect.** An overnight print gap ignores a stop. Size for the gap: at 10% of equity,
   the p1 print (−24%) costs 2.4% of the portfolio.

### Capital-loss scenarios (portfolio loss, $ at $10K / $100K, return needed to recover)

| position | bad print (−10%, about 1 in 10) | severe (−20%, about 1 in 43) | worst seen (−48%) | long option (−100% premium) |
|---|---|---|---|---|
| 5% | −0.5% · $50 / $500 · +0.5% | −1.0% · $100 / $1,000 · +1.0% | −2.4% · $240 / $2,400 · +2.5% | −5% · $500 / $5,000 · +5.3% |
| 10% | −1.0% · $100 / $1,000 · +1.0% | −2.0% · $200 / $2,000 · +2.0% | −4.8% · $480 / $4,800 · +5.0% | −10% · $1,000 / $10,000 · +11.1% |
| 25% | −2.5% · $250 / $2,500 · +2.6% | −5.0% · $500 / $5,000 · +5.3% | −12% · $1,200 / $12,000 · +13.6% | −25% · $2,500 / $25,000 · +33.3% |
| 50% | −5% · $500 / $5,000 · +5.3% | −10% · $1,000 / $10,000 · +11.1% | −24% · $2,400 / $24,000 · +31.6% | −50% · $5,000 / $50,000 · +100% |

- **The mandate's example:** $50K in one position falling to $30K is a 40% position loss and a 20% portfolio loss on
  $100K, which needs +25% to recover.
- **Recovery time:** at a 10% position with history's premium, expected gain per trade is +0.065% of the portfolio,
  so making back a 4.8% hit takes ~74 trades: six years at one a month. Even the full harvest at $100K (~+5% a year)
  needs about two years to repair a 10% drawdown.
- **Losing streaks:** in a 12-trade year, P(5 losses in a row) is 11% if history holds and 20% at the live mean. Three
  −10% prints in a row at 25% size cost 7.3% of the portfolio.

### Scaling after profits

- Hold **absolute** risk per trade constant until the live record reaches 100 graded trades and passes its gate.
- Then re-set the risk budget once, at a scheduled review, as a fixed fraction of equity on that date. Never scale
  on one good month.
- A 10% gain after 12 trades is not evidence. At 25% size, the 5th-percentile year of a zero-edge strategy is −13.3%,
  so a +10% year sits inside the same noise.

### Holding or exiting after the print

| situation | rule for a premium harvest |
|---|---|
| beat, price falls | exit at the planned exit. The trade bet on the reaction, and the reaction is in |
| miss, price rises | exit at the planned exit; never re-label a lucky gain as thesis |
| guidance contradicts the thesis | exit (the harvest has no thesis to keep) |
| revenue strong, margins weak | exit at the planned exit |
| catalyst did not happen | exit at the planned exit |
| sharp adverse gap | exit at the planned exit (MOC), never average down |
| thesis "intact" after an adverse move | not this strategy's call. **A post-print hold is a new position.** It belongs to the main portfolio model's own post-earnings process, judged from scratch |

## 8. Operational and architectural recommendation

| option | verdict | reason |
|---|---|---|
| A · integrate into the portfolio model | **reject** | no edge to integrate; 1-day event trades do not fit a longer-horizon book; high-conviction labels would add risk, not return |
| B · independent model with daily scanning | **reject** | the scanning already runs in code; a daily AI layer costs allowance for no demonstrated value |
| C · hybrid (scanner → screen → research → review → risk → DRIVE) | **reject in full** | it is the right pipeline only once a signal exists. With none, every stage after the scanner is cost |
| **D · measurement service (recommended)** | **adopt** | PRE becomes code only: the calendar, date confirmation, chain capture, SH-M/SH-W grading and the gate reports, all already in GitHub Actions. It exports two things to DRIVE, one way, as files: the per-print risk label (implied move, both tails) and the premium verdict at each gate. No AI decisions, no laptop chats between gates |

The one-way valve (CHARTER §5) and the portfolio-blindness rules stay as they are. The portfolio side's own lab
already reached "a print adds variance, not return". D's export only confirms or updates it.

## 9. Resource efficiency

| item | measured | source |
|---|---|---|
| laptop chats, Sep 21–Oct 21 | 9 chats, 1,378 calls, ~428M cache-read tokens, ~2M output | `ops/token_efficiency_2026-10.md` |
| API-equivalent cost of those chats | **~$125–200 a month** (cache reads ~$86 and output ~$39 at Opus list prices; cache writes add up to ~$80) | *committee estimate* from the same file |
| weekly plan allowance | 85% by Thu 29 Oct; the project "outgrew the plan's allowance" | JOURNAL 10-29 |
| a T2 decision | $0.10–$0.20 equivalent (T2R $0.098, T2O $0.204); T2 and T2G unrecorded | stage1 P6 |
| commits | ~1,687 in 7 weeks | git log |
| graded gated events produced | 16 by the 10-30 cut | stage1 P1 |
| **cost per graded gated event** | roughly **$12–20 of laptop compute each**, before cloud routines | *committee estimate* |

- **Expected contribution:** negative at both $10K and $100K once measured execution costs are included, even at
  history's premium (§5).
- **The comparison that decides it:** one month of PRE's laptop chats (~$125–200 equivalent) buys a question whose
  best case, after measured costs, earns nothing at Jacob's size. The allowance PRE uses is shared with the DRIVE chats that run his money.
- **Cheaper ways to keep the useful part:** automated screening, batch grading and event-driven triggers already exist
  in PRE's code (`due.py`, `shadow.py`, `grade.py`). The reframe keeps exactly those and removes the AI and laptop layers.

## 10. Alternative opportunities

| alternative | mechanism | evidence | frequency | cost | how to test | verdict |
|---|---|---|---|---|---|---|
| **Earnings-risk label in the portfolio model** | a print inside a hold widens both tails | DRIVE T22 review: Y_BIG +3.05 pp, Y_LOW +3.00 pp, mean ~0 | every holding | ~0 (exists) | already measured | **do (already on the portfolio side)**: use it for sizing, not selection |
| **Market-wide premium monitor, MOC-executable** (the reframe) | announcement-risk premium and attention buying | academic EAP (§3); history +0.79% overnight | ~1,300 events a season | code only | §12 | **do, bounded** |
| Positive pre-announcement drift (DRIVE lab T24) | under-reaction to company pre-announcements | PASS but fragile: vs a survivor baseline p 0.115; 2023-on reverses | rare (~110 POS in the sample) | lab | replication and review (owed in DRIVE) | DRIVE lab's call, not PRE's |
| Sell earnings volatility, defined risk | implied move above realised (realised/implied 0.64 on means) | loses after spreads (D010 X1 −3.22%); paper −4.76% | high | options data | only if spreads ≤ 5% of premium on liquid names (H-XT) | **no**: policy excludes it now; reconsider in the Options project only |
| Post-earnings drift | slow digestion of surprises | decayed in large caps (PRE's note, "gone since ~2006") | high | low | — | no |
| Industry read-across (D018 D) | early reporters inform peers | intra-industry transfer (Foster 1981; Thomas & Zhang 2008) | medium | history batch | — | no new batch now. If it is ever revived, it goes to DRIVE's lab as one pre-registered test |
| Estimate-revision capture (idea E) | revisions predict surprises | strong for surprises, weaker for returns | high | free capture | capture now, test only at Gate 2 | optional, code-only |

**Best use of the freed capacity:** the main portfolio model and its lab's pending replications, and the Options
project's defined-risk work when it is ready. PRE's experience confirms the general
point: in liquid US large caps, event-driven edges that survive realistic costs are rare and small.

## 11. PRE Q&A

The full question set is `PRE_QA.md` beside this report. PRE was not contacted directly. The committee answered what
PRE's own files answer:

| question | answer from the record |
|---|---|
| strongest repeatable advantage | none demonstrated; "the edge is in method, not yet in signal" (CHARTER §4) |
| factors with incremental power | none (D006, D007, D010, D014) |
| high-conviction vs baseline | no evidence; v1 51.9% (n 27); its biggest win was a LOW-conviction call |
| surprise vs reaction vs instrument | Layer 1 not recorded; Layer 2 insufficient; Layer 3 negative |
| profit after realistic costs | equity: costs above the 0.20% assumption; options: negative after spreads |
| independent high-conviction trades a year | zero with evidence |
| worst loss distribution | p1 −24%, worst −48% per print; short options can lose more than their margin |
| what would end the project | **no rule exists**; this report sets one |

**Open questions, sent to PRE in priority order:**
- P1: the size of the hindsight-universe bias;
- P2: why the premium should hold live;
- P3: the moomoo-executable live mean, and the signed slippage;
- P4: dates by which each sample reaches power;
- P5: what to remove;
- P6: cost per graded event;
- P7: why Layer 1 is missing;
- P8–P10: failures and rejections (after Gate 1).

**Assessment of answers (round 1 of 1):** `COMMITTEE_ASSESSMENT.md`. PRE answered every question with citations.

- **Confirmed:** the corrected cut (r2) and the +91 bp signed slippage.
- **Conceded:** history's +0.65% is an upper bound with no mechanism behind it.
- **New, from PRE:** D008's Gate 2 cannot be met in Mar 2027, because gated events reach 250 only by mid-2027.

The recommendation stands, at ~85% confidence.

## 12. Final funding decision

**REFRAME.** Effective now, in this order:

0. **Correct the record:** add a Stage 1 addendum, a new commit beside the first output (D017 §2), computed on the
   full cut (exit-A open ≤ Fri 10-30). Fix the health counter (T2 missing 2 of 26) and the P6 cost line.
1. **Stop:**
   - the selection research: no D018, no new hypothesis batches, no D003 v5 work beyond what the Season A record
     needs;
   - the paper options accounts F and L (D011);
   - the shadow AI tracks T2G, T2R, T2O, T2M and T2E;
   - main T2 after Season A closes (20 Nov). H-T2C is reported as "stopped for resources, no verdict".
2. **Keep, code only:**
   - the calendar, date confirmation and chain capture;
   - SH-M and SH-W grading;
   - the registered C1 look (from 7 Dec);
   - the Gate 1 report. Chain capture keeps building the point-in-time options dataset at no AI cost.
3. **Register before Season B (a new version, its own clock):** a secondary statistic on SH-M and SH-W, **close before
   the print → close of the reaction day**. It is net of US$0.99 per order at a stated $1,000 notional and of a
   measured MOC spread. It is the trade Jacob can actually place.
4. **Budget:**
   - one laptop chat per gate, ≤ 300k tokens each;
   - zero laptop chats between gates, except to repair a broken code step;
   - cloud routines for code steps only;
   - a cap of 10% of the weekly plan allowance, measured from the usage card each Monday.

### Kill and continuation criteria, fixed now

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

### The strongest case against this decision

- **For terminating outright:**
  - the live premium leans negative;
  - the history is hindsight-flattered;
  - DRIVE's lab already shows prints add variance, not return;
  - Jacob cannot place the trade as specified.

  *Why not:* the monitor costs almost nothing once the AI and laptop layers are cut. It already exists in code, and it
  answers a question with a dated end. If Gate 1 fails, it ends in December.
- **For continuing as is:**
  - the apparatus is unusually rigorous;
  - stopping T2 forfeits a rare post-cutoff LLM record;
  - one month of data proves nothing.

  *Why not:* nothing here is terminated for lack of evidence. The selection layers were tested on ~2,700 events and
  failed. The AI record has research value but no path to Jacob's money within a year. Its cost lands on the chats
  that manage that money.

## Decision table

| Dimension | Assessment |
|---|---|
| Genuine predictive edge | **None demonstrated.** v1: 51.9% on 27 blind calls. v2: no selection factor; the base premium is unconfirmed live and leans negative |
| Incremental factor value | **None:** 0 of 10 literature factors, 0 of 20 new signals, the IV spread and the first-hour patterns all failed |
| After-cost profitability | **Not shown.** History +0.65% net on a hindsight sample; live −1.50% net (correct cut); measured paper execution ~0.9% a round trip, which more than consumes history's premium |
| Options suitability | **Unsuitable:** both sides lose after spreads in history and on paper; excluded by Jacob's policy |
| Opportunity frequency | **Events plentiful** (8 months of 12); **high-conviction opportunities with evidence: zero** |
| Long-term sustainability | **Weak:** a regime-dependent, right-tail premium; selection edges not found |
| Portfolio compatibility | **Low as a trade source** (1-day event trades); **useful as a risk label**, which the portfolio side already has |
| Capital efficiency | **Poor:** ~10% SD per print for ≤ 0.65% mean; one trade a month at 10% size returns a median +0.7% a year |
| Token efficiency | **Poor:** ~$125–200 a month of laptop compute and 85% of a weekly allowance, for a question whose best case after measured costs earns nothing at Jacob's size |
| Overall initiative value | **Low as a trading model; modest as a cheap code-only measurement** |
| Recommended action | **B · REFRAME:** code-only premium monitor with a moomoo-executable statistic; stop selection research, options paper and the AI shadows; kill at Gate 1 or Gate 2 on the bars above |

**Overall rating: 2.5 / 10.** It is a superbly honest instrument pointed at an edge that is not there in a form Jacob
can use. The rating is subordinate to the recommendation above.

## Appendix · GitHub and implementation review

Nine public repositories were read as code (shallow clones, never run), on 2026-11-03: the three the mandate named and
six found independently. **None gives credible evidence of an after-cost edge from pre-earnings long equity or from
earnings options.**

| repo | what it does | timing control | costs | result | evidence quality |
|---|---|---|---|---|---|
| ZieglerBrokerage/earnings-straddle-research | QuantConnect straddle pilot | calendar-day arithmetic: a Monday BMO enters after the release (`earnings_events.py:21,28`) | — | no results; each event counted 5 times (`main.py:208`) | none |
| erictao947/earnings-vol-study | implied vs realised vol study | ±1-day tolerance lets the AMC off-by-one through (`phase1_events.py:67`); unknown timing defaulted to AMC | full spread | −0.24% per event on the 164 of 639 tradeable events; its summary still shows a retracted 2.23× ratio | weak |
| leeyawnnn/earnings_surprise_analyzer | PEAD event study | SEC 8-K 2.02 acceptance time; hard `assert_no_lookahead` (`events.py:95-113`) | break-even computed | drift real, but breaks even at 11–20 bp round trip | **good method**, no edge |
| quanttqueensu/earnings_iv_crush | 12-year short-straddle backtest | 2 of 3 calendars must agree; unknown session skipped; 8-K cross-check | ~11.6% of premium per round trip, measured | short straddle loses after costs in all 12 years (7,765 events); calendars and iron flies net negative | **strongest**; negative |
| Darson2004/kelly-event-vol | pre-print vol buying, OPRA quotes | pre-registration, hashed files | real quotes | +6.39% per trade (n 193, t 2.65), but exits before the print, data already seen, +0.24% at T-7 entry, median trade −4.9%, holdout unopened | fragile |
| ProgramComputer/earnings-trade-automation | Alpaca paper calendar spreads | — | paper fills near the ask | committed ledger: 92 closed trades, 15 winners, average −32% of debit | negative |
| Acelogic/Earnings-Volatility-Calculator | screener | thresholds from a video | — | no backtest | none |
| JasonLi-TMT/Earnings-Release-Premium | ML classifier | random-split CV on time series | — | 0.88 "accuracy", no returns | invalid |
| TauricResearch/TradingAgents | multi-agent LLM trader | point-in-time data guards, but no guard against the model's own memory | none | no cost-aware backtest | not evidence |

**What PRE could adopt (cheap):**
- a no-look-ahead assertion in CI over every ledger row;
- "unknown session = skip", never a default;
- an after-the-fact 8-K timestamp audit of every BMO/AMC label;
- a **matched-random selector** with T1/T2's pick count, so selection is tested against chance as well as T0;
- a reported break-even cost instead of one 0.20% figure;
- a deflated Sharpe ratio with a running trial count;
- options P&L headlined at halfway or natural, never at mid.

**PRE already avoids** most public weaknesses: calendar-day arithmetic, single-source dates, mid-price headlines, random
cross-validation and stale summaries. Two caveats from the review: the SEC submissions JSON's acceptance-time offset is
handled differently by two repos, so test it on a known sample; and DoltHub option chains are not a contract-level
history (D010 already found a split-scale defect there).

## Appendix · sources and recomputation

- PRE files: `registry/D001`, `D003`, `D006`, `D008`, `D010`, `D016`, `D017`; `analysis/history/*`; `analysis/d010/*`;
  `outcomes/reports/stage1_2026-10-30.md`; `HYPOTHESES.md`; `RESEARCH_PLAN.md`; `CHARTER.md`; `JOURNAL.md`;
  `ops/token_efficiency_2026-10.md`; `archive/PRE_v1_closed/doctrine_pre.md`; `reviews/ERRATA_2026-09-14_PRE_v1_figures.md`.
- DRIVE lab (read-only): `lab/results/T8.md`, `T22.md`, `T22_review.md`, `T24.md`.
- Broker fees: [moomoo SG fees and pricing](https://www.moomoo.com/sg/learn/moomoo-singapore-fees-and-pricing), "Feb 2026
  Update": US stocks $0 commission (T&Cs), US$0.99 platform fee per order.
- Committee recompute scripts (`moc.py`, `sim.py`, seed 20261103) are kept with the committee's hand-over notes, outside
  this repository. They read only the files above.
