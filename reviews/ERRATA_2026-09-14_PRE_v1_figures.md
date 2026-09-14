# Errata — PRE v1 figures checked against primary sources, 2026-09-14

The archive is byte-exact and is never edited, so its known errors are recorded here instead.
**This file is about the reliability of a retired model's record. It is not evidence about any
factor** — the fence in `archive/README.md` still applies.

Checked against SEC filings (EDGAR, with a User-Agent) and the companies' own earnings calls
(Alpha Vantage transcripts; ORCL's from the Motley Fool transcript).

## Verdict: nothing was fabricated. Three kinds of error were found.

### 1. Correct figure, wrong source label
PRE v1 labelled these FILED, but they come from the earnings **call** (company-stated), not the filing.

| figure | where it actually is |
|---|---|
| ORCL "GPU utilisation 97.9%" | Q1 FY27 call, Clay Magouyrk. Not in the release |
| CPRT "US insurance units −7.5% Q4, −8% FY" | Q4 FY26 call, CFO Leah Stearns. Not in the release |
| CPRT "record total loss frequency" | Q4 FY26 call, CEO Jay Adair: 23.3% in calendar Q2 2026, vs 22.4%. Not in the release |
| ORCL "1.74 est" | consensus (yfinance 1.74 est vs 1.92 reported) — an analyst figure, not filed |

### 2. Mislabelled number
- **CPRT "EPS missed by 14.6%"** — $0.35 against $0.41 a year earlier is **−14.6% YoY**. Against
  a $0.38 consensus the miss was **−8.5%** (yfinance).

### 3. Unsupported causal story
- **CPRT "the market looked through the EPS drop and bought total-loss frequency and ACV."** The same
  evening Copart filed a **separate 8-K agreeing to buy ACV (ACVA)** — $10.50 a share in cash, about
  $1.9B equity value (acc 0001193125-26-388064). "ACV" in the story was the acquisition, not a
  volume driver. The reaction priced both events together, and the gap reversed intraday: 1-minute
  data shows 30.76 → **31.76 at the open (+3.25%)** → **29.94 at the close (−2.7%)**.

Also found in PRE v1's handoff rows (outside this archive):
- ADBE "CEO transition announced with the print" — the succession was filed **2026-09-08**,
  two days before the print (8-K items 5.02/7.01, acc 0000796343-26-000144).
- ADBE "ARR +11.2%" — not in the release. The release gives an FY26 target of 10.2%.

## Verified exactly

| name | figures | source |
|---|---|---|
| AEO | op profit $211M vs $103M; net IEEPA refund benefit $161M; refunds $196M incl. interest; FY op-income guide $540–550M "inclusive of net tariff refund benefit"; prior guide $390–410M, which "excludes any impact from … (IEEPA) tariff refunds"; Q2 guide $45–50M | [Q2](https://www.sec.gov/Archives/edgar/data/919012/000119312526386510/aeo-ex99_1.htm) · [Q1](https://www.sec.gov/Archives/edgar/data/919012/000119312526245310/aeo-ex99_1.htm) |
| CPRT | revenue $1.2B +2.4%; net income $327.4M −17.4%; EPS $0.35 vs $0.41; FY revenue $4.7B +0.4% | [release](https://www.sec.gov/Archives/edgar/data/900075/000119312526387902/cprt-ex99_1.htm) |
| ORCL | revenue $19.3B +30%; IaaS +121% to $7.4B; EPS $1.92 non-GAAP / $1.56 GAAP; FY27 ≥ $90B and EPS $8.10; 850MW; Q1 capex $28,499M; Q1 FCF −$5,396M | [release](https://www.sec.gov/Archives/edgar/data/1341439/000119312526387905/orcl-ex99_1.htm) |
| ADBE | Q3 revenue $6.76B; EPS $6.13 non-GAAP; FY26 $26.576–26.626B (from $26.50–26.60B); Q4 $6.80–6.85B; ARR $27.50B | [Q3](https://www.sec.gov/Archives/edgar/data/796343/000079634326000147/adbeex991q326.htm) |
| CHWY | net sales $3.33B +7.3% (5.7% excluding acquisitions); gross margin 30.4%; adj. EBITDA margin 6.8% +90bp; active customers 21.705M +3.8%; Autoship 84.6%; gap −6.1% | [Q2](https://www.sec.gov/Archives/edgar/data/1766502/000162828026061011/chwyq22026exhibit991.htm) |

The AEO "~4% underlying cut" is arithmetic on verified figures ($545M − $161M vs a $400M midpoint).
It assumes the guide carries no refund benefit beyond Q2's $161M, which the release does not quantify.

## Archive lines carrying the errors (do not edit them)

- `PRE_v1_closed/PRE/STATE.md:119`
- `PRE_v1_closed/PRE/dossiers/CPRT.json:20, 25, 35`
- `PRE_v1_closed/PRE/dossiers/ORCL.json:20` (label only)
- `PRE_v1_closed/PRE/errors.jsonl:19`
- `PRE_v1_closed/reviews/audit_brief_rev2.html:516` — the "Does PRE Have Edge?" brief the external
  reviewers read; its CPRT row carries error types 2 and 3
- `PRE_v1_closed/skills_tombstones/post/SKILL.md:42`

## What this changes for the new experiment (data facts only)

- **Read every filing from the event window** before attributing a reaction to the print. A
  same-evening 8-K (M&A, CEO change) confounds it.
- **"The open" is ambiguous in yfinance.** CPRT on 2026-09-11: the daily bar says Open 32.01, while
  the 09:30 one-minute bar opened at 31.76. Exit A needs one pinned definition and one source.
- **A call-only figure is company-stated, not filed.** Store the tier with every value.
