# NKE — 2026-10-01 (AMC) — thesis card

> Written before the entry open, under D004 decision protocol **v1** (pilot). Frozen with the event.
> FRAMEWORK §4 items 1–6. Items 7–10 are filled in after the exit, by code.

## 1. Identity

| field | value |
|---|---|
| ticker | NKE — NIKE, Inc. (Class B, NYSE) |
| cluster | **consumer** (Footwear & Accessories; `universe/pilot/candidates.json`, screened 2026-09-17) |
| stage | **unknown** — `K_stage`. NIKE does not tag `us-gaap:OperatingIncomeLoss` in XBRL, so D004 §4's formula has no operating-income input. D004 v3 §6 confirms NIKE stays `unknown`; a proxy would be a guess, which §4 forbids. |
| market cap | $52.7bn |
| report date / session | 2026-10-01, **AMC** — release ~13:15 PT, call 14:00 PT, from NIKE's own 2026-08-28 scheduling release; second source yfinance `get_earnings_dates` |
| snapshot session | 2026-09-30, captured 14:31:00 ET (gate) / 14:31:04 ET (factors) |
| entry | open, 2026-10-01 |
| exit A (primary) | open, 2026-10-02 · exit B close 2026-10-02 (secondary) · exit C close 2026-10-09 (secondary) |
| quarter being reported | fiscal **Q1 2027**, ended August 2026 |

## 2. Factor snapshot

By reference: `events/pilot/NKE_2026-10-01/factors.json` and `gate.json` (options), both captured
2026-09-30 ~14:31 ET. The values this card leans on:

| factor | value | read |
|---|---|---|
| `A_ret_12m_LR01` | **−47.3%** | an extreme 12-month *loser*, so LR01's winner-reversal runs the other way |
| `A_dist_from_52w_high` | **−50.8%** | the stock has halved |
| `A_ret_1m` / `A_ret_5d_LR10` | −8.2% / −1.5% | mild pre-print pressure → LR10 reversal, weakly positive |
| `A_vol_60d_ann` | 28.9% | |
| `A_volume_20d_vs_250d` | 1.53 | volume already running hot into the print |
| `E_last4_prints` raw_return_A | +0.05%, **−10.34%**, **−10.32%**, +6.11% | two 10% punishments in four prints; mean −3.6% |
| `E_last4_win_rate_A` | 0.50 | below the consumer base rate of 0.555 (n=4, so weak) |
| `E_last_surprise_pct_LR17` | +466% | but that beat moved the stock +0.05% — the surprise is not the driver |
| `D_eps_est_current_q` | avg **$0.437**, low 0.38, high 0.50, 24 analysts, year-ago $0.49 (−10.8%) | |
| `D_eps_revision_90d_LR19` | **−2.6%** | consensus walked down; LR19 reads a walk-down as a beatable bar |
| `C_analyst_dispersion_LR08` | 0.275 | high disagreement (LR08 negative) |
| `C_short_pct_float` | **9.0%** | disagreement plus shorting — the Miller/Berkman setup |
| `J_forward_pe_LR20` / `J_price_to_sales_LR20` | 16.5 / 1.13 | not glamour any more |
| `B_implied_move` | **8.55%** | the options price a very large binary |
| `B_iv_spread_call_minus_put_atm_LR12` | **+0.0078** | calls marginally richer than puts → LR12 positive |
| `B_put_skew_90_LR13` | **−0.0381** | the 90%-strike put trades 3.8 vol points *below* the ATM call — the **opposite** of the bearish smirk LR13 penalises |
| `B_put_call_volume_LR14` / `B_put_call_oi` | 0.824 / 0.769 | call-heavy flow and open interest → LR14 positive |
| `B_event_move_term_structure` | iv1 1.183 (10-02) vs iv2 0.710 (10-09) | the event is cleanly isolated in the front expiry |
| `L_report_date_shift_days` | +2 | two days later than the same quarter last year → LR23 weakly negative |
| `L_same_day_reporters_LR06` | 16 | a modifier on size, not sign |
| `L_weekday_LR07` | Thursday | not the Friday inattention slot |

## 3. Three theses

### Thesis 1 — the bar is already on the floor, and NIKE keeps stepping over it (*expected: up*)

**What we expect.** NKE prints a Q1 FY2027 EPS above the $0.437 consensus and the stock does not
break down, because expectations are set for a −11% year-on-year quarter in a stock that has already
lost 47% in a year and sits 51% below its high.

**Mechanism.** LR19 (Richardson, Teoh & Wysocki) and LR20 / La Porta et al.: analysts walk the number
down to a beatable level, and the torpedo that punishes glamour names on a miss has far less to
destroy once the multiple has compressed to 16.5× forward and 1.1× sales. NIKE has beaten the vendor
consensus in each of the last four quarters. Positioning in the options market is consistent with
this: call-heavy volume and open interest, calls richer than puts, and — most unusually — downside
puts priced *below* the ATM call, i.e. no crash premium is being paid.

**What would prove it wrong.** A headline revenue miss rather than an EPS miss; or an EPS beat that
the stock ignores or sells, exactly as happened on 2026-06-30 (+466% surprise, +0.05% reaction). If
the stock falls on a beat, the bar was never the deciding variable.

### Thesis 2 — the company itself has already told us fiscal 2027 gets worse before better (*expected: down*)

**What we expect.** Management reiterates that Greater China and Converse keep dragging, and the
stock falls, because the market is repricing a slower turnaround rather than one quarter's EPS.

**Mechanism.** Company-stated, in the FY2026 10-K filed 2026-07-15: *"We expect negative impacts from
Greater China and Converse to continue throughout fiscal 2027,"* with the turnaround actions only
"complete by the end of December 2026," and Greater China facing "declining store traffic, elevated
promotional activity and higher levels of inventory across the marketplace." Q4's reported 49.2%
gross margin and $0.72 EPS were inflated by a **one-off $986m IEEPA tariff recovery** (about 900bp of
margin, $0.52 of EPS) after the Supreme Court's 2026-02-20 ruling; the underlying quarter was ~$0.20.
FY27 laps none of that. Converse revenue fell 32% in Q4 and 31% for the year. This is the mechanism
that produced the two −10.3% reactions in the last four prints.

**What would prove it wrong.** Greater China returning to growth, or a credible sequential
gross-margin bridge that shows the tariff benefit being replaced by structural margin.

### Thesis 3 — a new CFO's first call is a reset risk that this window cannot hedge (*expected: down, fat left tail*)

**What we expect.** David Denton, CFO since 2026-08-17 (announced 2026-06-23, from Pfizer, previously
Lowe's and CVS), delivers his first NIKE guidance. Incoming CFOs habitually rebase expectations. If
he does, the move is large and negative; the 8.55% implied move says the market knows a large move is
coming but not its sign.

**Mechanism.** Limits-to-arbitrage plus disagreement (LR08, Miller 1977, Berkman et al. 2009):
dispersion is 0.275 and 9.0% of the float is short, so opinion is genuinely divided and the print is
the event that settles it — historically downwards. Supporting flag: the Chief Accounting Officer and
Corporate Controller, Johanna Nielsen, resigned effective 2026-09-04 (8-K of 2026-08-10, stated as
*not* the result of any disagreement over operations, policies or practices). Two finance departures
in one quarter is worth recording even with the boilerplate denial.

**What would prove it wrong.** Denton reaffirming the framework Matthew Friend left rather than
issuing his own, or the company pre-releasing the reset (as it did on 2026-06-23) so nothing new
lands at the print.

## 4. Key observations to capture

- Q1 FY2027 revenue growth, **reported and currency-neutral**, versus the −1% / −4% Q4 exit rate.
- **Greater China** revenue and EBIT, and whether the 10-K's "negative impacts throughout fiscal
  2027" language is repeated, softened or hardened on the call.
- **Gross margin on a clean basis** — Q1 FY27 versus Q4 FY26's *underlying* ~40.2% (49.2% less the
  ~900bp IEEPA benefit), not versus the 49.2% headline. Any new tariff cost or further refund.
- Whether the **new CFO issues his own Q2/FY27 guidance** or defers, and on what basis (reported vs
  currency-neutral) — the guide-vs-prior-guide comparison must be on the same basis.
- **NIKE Direct / Digital** (−7% / −12% in Q4) versus **wholesale** (+4%): is the channel reset
  bottoming?
- **Converse** revenue (−32% in Q4) and any decision on the brand.
- **Inventory** ($7.5bn, flat, with units up) — a units-up, mix-shifted inventory is a promotion risk.
- Any **new severance or restructuring charge** (FY26 took $385m; the 10-K says more may come).
- Whether anything else lands in the event window — a same-evening 8-K would confound the reaction.

## 5. Predicted deciding variable

**The forward commentary on Greater China and the fiscal-2027 revenue and gross-margin trajectory,
delivered by the incoming CFO on the call — not the EPS surprise.** The evidence for this is in the
event's own factor snapshot: NIKE beat consensus by +466%, +41%, +24% and +81% over the last four
quarters, and the reactions were +0.05%, −10.3%, −10.3% and +6.1%. The EPS line has no explanatory
power for this name on this window; the guide does.

## 6. Decisions

| track | decision | confidence | note |
|---|---|---|---|
| **T0** | BUY | — | buys every event that passes the S2 gate |
| **T1** | null | — | rule v0 not frozen — pilot (D004 v1 §2). Not back-filled later. |
| **T2** | **BUY** | **0.52** | this card |

### From the prior to 0.52

**Prior: 0.55.** `registry/D004_base_rates_v3.json`, `by_cluster.consumer` = 0.555 (n=436, marked
sufficient), nudged down by `by_session.AMC` = 0.538. The cluster cell is the more specific of the
two, so ~0.55 before anything about NIKE itself. The buy-everything opponent, not 0.50, is the bar.

**What moved it, and by how much.**

| | direction | rough weight |
|---|---|---|
| Extreme washout, not glamour: −47% 12m, −51% from the high, 16.5× forward, 1.1× sales — LR20's torpedo has little left to destroy, and LR01's winner-reversal runs the other way | + | +0.01 |
| Option positioning mildly call-side on all three B-family signs at once (LR12 +, LR13 inverted, LR14 +) — but the literature review flags B-family priors as weak in today's retail-dominated weekly market | + | +0.01 |
| Consensus walked down 2.6% in 90 days to $0.437, four consecutive beats (LR19) | + | +0.01 |
| The 10-K's own words: Greater China and Converse drag **throughout** fiscal 2027; Q4's $0.72 was $0.52 of one-off tariff recovery | − | −0.02 |
| A new CFO's first call, with the CAO also gone; dispersion 0.275 and 9.0% short (LR08) | − | −0.02 |
| NIKE's own last four reactions on this exact window: two at −10.3%, mean −3.6% (n=4, so weak) | − | −0.02 |
| 8.55% implied move — a very wide distribution reduces any ability to call direction, which pulls the answer back toward the base rate rather than away from it | toward prior | — |

**0.55 → 0.52.** Still above 0.5, so **BUY**, but below the consumer base rate: the negatives here
are company-stated and specific, while the positives are mostly the generic "it is cheap now."
This is a name I would rather own at 0.52 than pass on — and if the T0 track beats me on it, the
right lesson is that washed-out valuation is not a direction signal.

## Disclosures — data gaps and one excluded fetch

- **The Q4 FY2026 earnings call transcript could not be retrieved.** No `ALPHAVANTAGE_API_KEY` is set
  in this job, and the accessible transcript hosts returned 404 or 403. **NIKE therefore gives its
  quarterly guidance only on the call, and the specific Q1 FY2027 revenue and gross-margin guide is
  a genuine gap in this card — it is not estimated and not guessed.** The forward view above rests on
  the filed 10-K language and on the vendor consensus in `factors.json`.
- **One live page was fetched at 2026-09-30 ~14:33 ET, two minutes after `captured_et`**
  (`stockanalysis.com/stocks/nke/`, a quote page). It is **excluded from `inputs_read`** and from the
  reasoning above. What it showed — a street consensus near $0.44 EPS — matches
  `D_eps_est_current_q.avg` = 0.43689 already in the snapshot, so no post-snapshot information
  entered the decision. Recorded here rather than left unsaid.
- **A Form 144 was filed on 2026-09-30** (accession 0001959173-26-007147), the snapshot day. EDGAR
  gives no filing time for it, so it cannot be shown to precede `captured_et`; it was **not read and
  not used**. Form 144s are routine 10b5-1 sale notices and NIKE has filed several this month.
- `K_stage` is `unknown` for the reason in §1 — a structural limitation of D004 §4 for this filer,
  not a fetch failure.
- `E_last_surprise_pct_LR17` and the `E_last4_prints` surprise figures use a **vendor-defined EPS
  basis that is not pinned** (STATE #2). They are used qualitatively here — "NIKE keeps beating" —
  never as a calibrated magnitude.
