# Thesis card — PENG · 2026-10-06 (AMC) · pilot

Written before the entry open. FRAMEWORK §4 items 1–6. Never edited after the freeze.

## 1. Identity

| field | value |
|---|---|
| ticker | PENG — Penguin Solutions, Inc. (Nasdaq; formerly SMART Global Holdings; US-domesticated from Cayman 2025-06-30) |
| cluster | `ai_infra` (D003 screen; filing test AI_HOSTING, 34 hits) |
| stage | `profitable_growth` — rev growth +47.6% y/y, op margin +10.6% for the quarter ended 2026-05-29 (SEC XBRL) |
| report date / session | 2026-10-06, AMC — company release 2026-09-15 16:05 ET gives a 16:30 ET call; session inferred from the call time (flag `session_from_call_time`), confirmed AMC by yfinance `get_earnings_dates` and the Nasdaq calendar |
| quarter reported | FQ4 and full-year fiscal 2026 (FY26 ended 2026-08-28; fiscal year = 52/53 weeks to the last Friday in August) |
| entry | 2026-10-06 open · exit A 2026-10-07 open (primary, D001 WIN_raw) · secondary: exit B 2026-10-07 close, exit C 2026-10-14 close |
| snapshot | 2026-10-05, `captured_et` 14:31:00.265425-04:00 · market cap $3.14B · spot $61.36 |

## 2. Factor snapshot

By reference: `events/pilot/PENG_2026-10-06/factors.json` (every factor with its source and as-of time),
`gate.json`, `option_chain.json`. The ones that carry weight below:

| factor | value | read |
|---|---|---|
| `A_ret_12m_LR01` | +123.5% | extreme 12-month winner → LR01 negative |
| `A_ret_1m` / `A_ret_5d_LR10` | +26.2% / +11.6% | run-up straight into the entry → LR10 negative |
| `A_max_daily_ret_21d_LR11` | +11.6% | identical to the 5-day return, so the whole move is **one day** → LR11, and raises LR21 (peer-driven, reversal) |
| `A_dist_from_52w_high` | −24.6% | 52w high ≈ $81; the stock is a bounce off a drawdown, not at new highs |
| `A_vol_60d_ann` | 90.2% | |
| `A_volume_20d_vs_250d` | 0.74 | volume **below** its longer average — attention is not elevated |
| `B_implied_move` | **19.48%** | huge; most probability mass is "big move, unknown sign" |
| `B_atm_iv_over_rv60` | 1.51 | event premium priced |
| `B_event_move_term_structure` | 21.6% | iv1 1.359 (10-16) vs iv2 0.941 (11-20) |
| `B_iv_spread_call_minus_put_atm_LR12` | **+9.01 vol pts** | calls rich → LR12 positive (parity-checked below) |
| `B_put_skew_90_LR13` | −9.84 vol pts | no put smirk, the opposite → LR13 not triggered |
| `B_put_call_volume_LR14` / `B_put_call_oi` | 0.58 / 0.45 | call-heavy → LR14 mildly positive |
| `E_last4_win_rate_A` | 0.75 | +7.8%, +9.0%, +11.6%, **−25.5%** — the loss is the same fiscal quarter (FQ4, 2025-10-07) |
| `E_past_reaction_volume_LR02` | 6.11× | high past announcement volume → LR02 positive |
| `E_last_surprise_pct_LR17` | +49.3% | basis not pinned (STATE #2) |
| `D_eps_est_current_q` | avg $0.772, range $0.75–$0.80, 7 analysts, year-ago $0.43 | the bar |
| `D_eps_revision_90d_LR19` | +7.7% (flat over the last 30 days) | estimates were raised, not walked **down** → LR19 reversed |
| `C_analyst_dispersion_LR08` | 0.065 | disagreement among analysts is **low** |
| `C_short_pct_float` | 19.68% | high, but materially mechanical (convert arb — see thesis 2) |
| `C_analyst_rec_mean` | 1.71 | sell-side is bullish |
| `J_forward_pe_LR20` / `J_price_to_sales_LR20` | 18.2 / 2.09 | **not** a glamour multiple → LR20 torpedo risk is low |
| `K_rev_growth_yoy_q` / `K_op_margin_q` | +47.6% / +10.6% | |
| `L_report_date_shift_days` | 0 | not scheduled late → LR23 neutral |
| `L_same_day_reporters_LR06` / `L_weekday_LR07` | 11 / Tuesday | not a busy day, not a Friday → no distraction discount |

**Parity check on the gate quotes** (own arithmetic, not a fetched figure): $60 strike, 2026-10-16
expiry, spot $61.36. Call mid $6.85, put mid $5.10 → C−P = $1.75. Theoretical C−P = S − K·e^(−rT) ≈
$1.36 + $0.07 = $1.43. Calls are ~$0.32 rich, 0.52% of spot. Expensive borrow (19.7% short interest)
pushes the synthetic forward *down*, i.e. makes calls *cheaper*, so the richness is genuine and
understated. This is the one real signal pointing the other way from the fundamentals.

**What the print actually is.** From the 2026-07-07 release: FY26 guided to net sales +22% ±2% and
non-GAAP EPS $2.60 ±$0.05, both stated to land **above the high end** of the prior range. Against FY25
net sales of $1,368.8M and Q1–Q3 FY26 of $1,164.8M (XBRL), FQ4 net sales are implied at **≈$505M**
(+49% y/y vs $337.9M) and FQ4 non-GAAP EPS at **≈$0.75** — *below* Q3-26's $0.84 — against consensus
$0.772. Consensus sits in the upper half of the company's own implied range. Penguin guides **annually**,
not quarterly, so 2026-10-06 is the initial **FY2027** outlook. The quarter is pre-announced; the guide
is the news.

## 3. Three theses

### Thesis 1 — the FY2027 guide lands short of a stock that has already moved *(the one this decision bets on)*

- **Expected.** Penguin prints a strong FQ4 (revenue at or above ~$505M, EPS at or near $0.75–0.80) and
  then gives an initial FY2027 outlook that is cautious on gross margin and on Advanced Computing, and
  the stock opens 2026-10-07 **below** the 2026-10-06 open.
- **Mechanism.** Three reinforcing, primary-sourced facts. (a) *Mix.* All the growth is the lowest-margin
  segment: Integrated Memory +111% y/y to $275.1M while Advanced Computing — the AI Factory Platform the
  multiple is paid for — grew 3.8% to $137.6M. Non-GAAP gross margin fell to 28.1% from 31.7% a year
  earlier (−360bp) on 48% revenue growth, and raising the FY26 revenue-growth guide by ten points bought
  only 50bp of gross margin (26.0% → 26.5%). The 10-Q states both risks itself: Integrated Memory "has
  gross margins which are lower than the Company average", and the AI-infrastructure shift away from
  hyperscalers "may negatively impact our net sales during the transition". (b) *Cash.* AR rose to
  $703.0M from $307.9M (+128%) and inventories to $498.3M from $255.2M (+95%) while revenue rose 48%;
  cash *fell* to $440.3M. AR is ~134 days of Q3 sales. The $750M 0.00% convert of 2026-07-17 funded old-note
  repurchases, a $100M revolver repayment, $49.1M of capped calls and working capital — a financing need.
  (c) *Who speaks.* The first FY2027 guide is set by an **interim** CFO (Aaron Johnson since 2026-07-09;
  permanent search unresolved at the snapshot), on a cyclical memory tailwind, with Penguin Edge winding
  down by end-FY26 as a stated comparability headwind. Interim CFOs guide low. On top: +11.6% in five
  sessions into the entry (LR10/LR11) on a +123% twelve-month winner (LR01).
- **Proved wrong by.** An FY2027 net-sales guide comfortably above about +20% growth **with** a gross-margin
  guide held at or above 26.5%; or Advanced Computing guided to reaccelerate to double digits; or FQ4
  showing AR and inventory days falling and positive operating cash flow; or a permanent CFO named with
  the print. Any of those and the quality objection collapses.

### Thesis 2 — the memory upcycle guide blows out and the 19.7% short base is squeezed *(the live bull case)*

- **Expected.** FY2027 is guided far above consensus on DRAM pricing and CXL/high-density demand, and the
  stock gaps up hard — plausibly a double-digit percentage, given the 19.5% implied move.
- **Mechanism.** Integrated Memory more than doubled y/y and memory pricing has been the sector's dominant
  force; a company at the intersection of memory and AI infrastructure can guide a full year off that with
  conviction. Valuation does not fight it: forward P/E 18.2 and P/S 2.09 on 47.6% growth means there is no
  glamour multiple to de-rate (LR20 inactive). Three consecutive beats (+12.3%, +23.1%, +49.3%) and two
  guidance raises in FY26 say management has been running ahead of its own numbers. 19.68% of float is
  short and open interest is call-heavy; the option market is paying up for calls (+9.0 vol points, ~$0.32
  rich to parity *despite* expensive borrow), which is the market's own forward-looking lean and the
  best-fitting literature signal for this window (LR12, strongest just before events).
- **Proved wrong by.** A gross-margin guide below 26.5%, or FY2027 revenue growth guided below ~15%, or
  management declining to guide the full year at all; any of those turns the richness of the calls into
  positioning that gets unwound rather than information.
- **Note on the short interest.** It should *not* be read as informed bearish positioning (LR08). The $750M
  2031 convert has 6.43M shares underlying (~12.6% of the ~51.2M shares outstanding); a material part of the
  short base is delta hedging, which is also gamma-long and therefore *dampens* realised moves.

### Thesis 3 — the implied move dominates and direction is simply not forecastable here

- **Expected.** A move of roughly ±20% whose sign is close to a coin flip, so the open-to-open outcome is
  decided by the FY2027 number rather than by anything observable at the snapshot, and any confidence far
  from the base rate is overreach.
- **Mechanism.** A 19.5% implied move with ATM IV at 1.51× realised vol says the market itself has no view
  on direction, only on magnitude. The signals available at the snapshot are flatly contradictory: options
  lean up (LR12, LR14, LR02), price history leans down (LR01, LR10, LR11), valuation is neutral-to-positive
  (LR20 inactive), and scheduling is neutral (LR06, LR07, LR23 all inert). The literature's own warning
  applies: most predictors change the *size* of the reaction, not its sign, and published edges decay — in
  a ≥$2B universe, expect any of these to be weaker than its paper. In raw-return terms a symmetric 19.5%
  log distribution also puts P(up) marginally under 50% with no drift.
- **Proved wrong by.** A reaction small relative to the implied move (say under 8%), which would mean the
  print was largely anticipated and the snapshot signals had room to matter after all.

## 4. Key observations to capture

1. **FY2027 outlook — the whole event.** Net-sales growth, GAAP and non-GAAP EPS, and whether they guide the
   full year at all. Compare on the same basis as the FY26 guide given 2026-07-07.
2. **FY2027 gross-margin guide** versus the FY26 guide of 26.5% GAAP / 28.5% non-GAAP. This is the mix test.
3. **FQ4 segment split** — Integrated Memory vs Advanced Computing vs Optimized LED, against Q3-26's
   $275.1M / $137.6M / $66.1M. Does Advanced Computing finally move off ~$135M?
4. **Sequential gross margin**, GAAP and non-GAAP, vs Q3-26's 27.8% / 28.1%.
5. **Working capital at 2026-08-28** — AR and inventories vs $703.0M and $498.3M, plus FQ4 and FY26 operating
   cash flow. Did the record earnings convert to cash?
6. **FY2027 diluted share count**, and how the $750M 2031 convert (conversion price $116.70), the capped calls
   (cap $175.05) and the repurchased 2029/2030 notes are modelled. FY26 was guided at 59M GAAP / 56M non-GAAP.
7. **A permanent CFO** — named or not; and whether the interim CFO guides a full year or hedges.
8. **DRAM contract-pricing commentary** — duration and visibility, and any hedging of the FY27 memory assumption.
9. **Penguin Edge wind-down** quantified as an FY2027 headwind.
10. **Any same-evening 8-K** (acquisition, officer change, financing) that would confound attribution of the
    2026-10-07 reaction. Nothing material was filed between 2026-07-17 and the snapshot: the only later
    filings are Form 4s (all code-A grants dated 2026-09-29, no insider selling), Form 144s and 13G/13D
    amendments.

## 5. Predicted deciding variable

**The initial FY2027 outlook, and inside it the gross-margin line.** Not FQ4 revenue or EPS — management
pre-announced on 2026-07-07 that FY26 would come in above the high end, so the quarter carries almost no
surprise. The market has to decide whether 47% revenue growth driven by low-margin Integrated Memory, funded
by a $750M convert and sitting in receivables, is a durable FY2027 base. The second-order variable is whether
Advanced Computing is guided to reaccelerate.

## 6. Decisions

| track | decision | confidence | basis |
|---|---|---|---|
| **T0** | BUY | — | buys every event that passes the S2 gate (D004 v1 §1) |
| **T1** | — | — | `null`, note "rule v0 not frozen - pilot" (D004 v1 §2). Rule v0 is frozen before Season A; pilot events are never back-filled |
| **T2** | **NO_BUY** | **0.45** | prior 0.55 (ai_infra 0.558 shrunk toward the 0.542 overall and 0.538 AMC rates) → 0.45 |

**T2 reasoning, short form.** The quarter is pre-announced, so the entire print is the first FY2027 guide, and
it is being set by an interim CFO off a memory-price peak whose growth is in the lowest-margin segment, sits in
receivables rather than cash, and leaves the AI-infrastructure segment the multiple is paid for flat at +3.8%
y/y — while consensus already sits in the upper half of the company's own implied FQ4 range and the stock has
risen 11.6% in five sessions. Against that, calls are genuinely rich to put-call parity and past announcement
volume is high, which is why this is 0.45 rather than lower. The fundamental judgements were deliberately
halved in weight: nothing in this experiment has yet shown that earnings quality predicts *direction* over a
one-open-to-next-open window, and a 19.5% implied move means most of the probability mass is "big move, sign
unknown". **BUY ⇔ confidence > 0.5, so 0.45 is NO_BUY.**

**Leak probe (recorded before any file about this event was opened).** "I don't know. PENG (Penguin Solutions,
formerly SMART Global Holdings) reports its fiscal Q4 in early October, but I have no recollection of the
2026-10-06 print or the stock's reaction to it; that date is beyond what I know. I am not looking it up."

**Disclosed data gaps.** No FQ3 call transcript was read — no Alpha Vantage key is present in this environment,
and the available web transcript pages are live pages whose update time cannot be checked against `captured_et`,
so under D004 none was used; management's qualitative FY2027 tone is unknown to this decision. The implied FQ4
EPS of ~$0.75 is approximate because quarterly EPS does not sum to annual while the diluted share count is
rising. `E_last4_prints` surprise percentages use an unpinned vendor EPS basis (STATE #2). `C_short_pct_float`
is an undated vendor snapshot and is partly mechanical convert-arb hedging.

**Uncomfortable finding, stated plainly.** The 2025-10-07 FQ4 print — the same fiscal quarter, one year earlier —
opened **−25.5%** despite an 18.5% EPS beat. One observation is not evidence (rule 6) and is not used as a
statistic here. What *is* used is the structural fact it illustrates and that the filings confirm: for Penguin
Solutions, FQ4 is the annual-guidance print, and a beat on the reported quarter has no claim on the reaction.
