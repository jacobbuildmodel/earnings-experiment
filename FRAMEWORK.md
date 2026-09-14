# Earnings Experiment — Framework v0.1

> **Status: DRAFT for owner review · 2026-09-13 · figures re-verified 2026-09-14 · NOT FROZEN.**
> Collection opens **Mon 2026-09-21**. Everything marked 🔒 must be frozen before then.

## How to read this

Built the way a 3-statement model is built: **outputs first** — what the experiment must show, and
the formulas behind it — **then inputs**: where each number comes from, and whether that source is
good enough. §1–5 are outputs. §6–8 are inputs. §9–12 are the rules that stop it lying, the
timeline, and what I need from you.

---

## 1. The one question

> **Before an earnings print, can we identify which stocks to BUY so the position profits from the
> result — and is the answer different for different kinds of business?**

- **Buy-side only.** Every event ends in exactly one decision: **BUY** or **NO_BUY**. No shorts.
- **We do not test the size of the move first.** The headline is binary — did the trade make money.
  Size is recorded for later, but it is not what we are testing now.
- **Implied volatility is a factor, not the target.**

---

## 2. OUTPUT 1 — the trade mechanics 🔒

### Entry — the open of the last session before the print is priced

| print timing | report lands | **entry** | first price that knows the result |
|---|---|---|---|
| **BMO** (before market open) on day D | before D's open | **open of D−1** | open of D |
| **AMC** (after market close) on day D | after D's close | **open of D** | open of D+1 |

*Your message said "bmc" — read as BMO. Confirm (§12).*

Every trade therefore holds **one full trading session plus the overnight gap**. That session
matters: stocks tend to drift up into earnings (factor A1), and this entry deliberately captures it.

### Exit — ⚠ YOUR DECISION, and it can never change afterwards

The exit defines what "profit from the earnings result" means. **It must be chosen before the first
trade and never changed.** Choosing whichever exit looks best *after* seeing results is the easiest
way there is to manufacture an edge that doesn't exist.

| option | exit at | what it measures | status |
|---|---|---|---|
| **A** | **first open after the print** | the result, and nothing after it | ✅ **PRIMARY (default)** |
| B | close of the reaction day | the result + the first full day of digestion, incl. the call | secondary |
| C | close 5 trading days later | the result + post-earnings drift | secondary |

**All three are recorded on every event. Only the primary decides whether anything works.** B and C
exist to answer your question about whether an *immediate* sell makes sense — as a separate,
labelled finding, never mixed into the main test.

### The outcome — computed by code, never judged 🔒

```
raw_return    = exit_price / entry_price − 1
bench_return  = the same window for the sector benchmark
excess_return = raw_return − beta × bench_return

WIN_excess    = excess_return > 0     ← PRIMARY  (did it beat its own sector?)
WIN_raw       = raw_return    > 0     ← P&L view (did the account go up?)
```

**Why excess is primary:** in a rising market almost every buy "wins" on raw return. Excess return
separates *the earnings result* from *the market that day*. Raw is still reported, because raw is
what reaches the account.

**Leave-one-out benchmark.** When a stock is a large weight in its own ETF, its move contaminates the
benchmark (ORCL moves IGV on its own print night). Where the weight `w` is material:
`bench = (ETF_return − w × stock_return) / (1 − w)`.

---

## 3. OUTPUT 2 — three decisions on every event, graded against each other 🔒

Each event is decided three ways, **independently and before entry**, and all three are graded on
the same outcome.

| track | who decides | how | what it tests |
|---|---|---|---|
| **T0 · Baseline** | nobody | BUY every eligible name | the null. If this alone makes money, that is a finding. |
| **T1 · Rule** | code | a frozen, versioned formula over the factors | does a *mechanical* signal exist? |
| **T2 · AI** | AI | reads the factor sheet + thesis card → BUY/NO_BUY, confidence, reasons | does *judgment* add anything over the rule? |

🔴 **Every eligible name is graded — including every NO_BUY.** The names we pass on are the control
group. Without them there is no way to tell a good filter from a lucky market.

| comparison | answers |
|---|---|
| T0 mean excess > 0 | does buying into earnings work *at all* in this universe? |
| T1 BUY set − T1 NO_BUY set | does the rule separate winners from losers? |
| T2 lift − T1 lift | does AI judgment add something a formula can't? |

---

## 4. OUTPUT 3 — the per-event record ("thesis card") 🔒

**Written before entry, committed to git with a timestamp, never edited afterwards:**

1. **Identity** — ticker, cluster, stage, report date, session, entry time
2. **Factor snapshot** — every factor in §7 that can be computed, each with its source and as-of time
3. **Three theses** — each as: *what we expect · the mechanism · what would prove it wrong*
4. **Key observations to capture** — what to look for in the print and the call (e.g. guide vs prior
   guide *on the same basis*; sequential gross margin; is AI revenue disclosed?)
5. **Predicted deciding variable** — the single thing we think will move the stock
6. **Decisions** — T0, T1 (with rule version), T2 (with confidence and reasoning)

**Filled in after exit:**

7. **Outcome** — computed by code (§2)
8. **Actual deciding variable** — what really moved it, with the source
9. **Thesis scorecard** — which held, which broke
10. **New ideas** → the *hypothesis queue*. **Never straight into a live rule** (§9, rule 5).

---

## 5. OUTPUT 4 — the findings table (per cluster, per factor)

| field | meaning |
|---|---|
| n events · n event-dates | how much evidence, counted honestly |
| base rate | P(WIN_excess) and mean excess return for buy-all (T0) |
| effect | WIN rate in the top third of the factor minus the bottom third; mean excess difference |
| confidence interval | where the true effect plausibly lies |
| q-value | significance **after** correcting for how many factors were tested |
| stability | does it hold in both halves of the sample? |
| status | CANDIDATE → REGISTERED → CONFIRMED / REJECTED |

Plus one verdict line: **does T1 beat T0, and does T2 beat T1, on data the rule was not built from?**

---

## 6. INPUT — the clusters (your idea, made testable)

You're right that putting a hypergrowth AI name and a cash-rich consumer name into one model is a
mistake, and there is direct evidence for it: growth stocks react far more violently to a
disappointing print than other stocks do
([Skinner & Sloan 2002](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=172060)). The same factor
can mean opposite things in different kinds of business.

### Axis 1 — sector cluster

| # | cluster | illustrative names (not the universe) |
|---|---|---|
| 1 | AI infrastructure & compute | NBIS, IREN, CRWV |
| 2 | Semiconductors & equipment | NVDA, AMD, MU, AVGO |
| 3 | Software & internet | ORCL, ADBE, PLTR, cybersecurity |
| 4 | Tech hardware & networking | servers, optics, components |
| 5 | Drones, robotics, space & defense-tech | — |
| 6 | Consumer (high implied vol) | CHWY, AEO-type movers |
| 7 | Healthcare growth (top names only) | biotech / medtech clearing the IV bar |
| 8 | Crypto-proxy | MSTR |

⚠ **MSTR is a special case.** Its print barely matters next to Bitcoin's price that day. It stays
because you asked for it — in its own cluster, benchmarked to BTC, so it cannot distort the others.

### Axis 2 — business stage, assigned by formula, never by judgment 🔒

| stage | rule (from filed financials) |
|---|---|
| **Unprofitable growth** | revenue growth ≥ 20% and GAAP operating margin < 0 |
| **Profitable growth** | revenue growth ≥ 20% and GAAP operating margin ≥ 0 |
| **Mature / slower** | revenue growth < 20% |

If a person or an AI picks the stage label, that choice becomes a hidden dial that can be turned
until the results look good. A formula can't be turned.

### The honest problem with clusters — and the fix

8 sectors × 3 stages = 24 buckets. With roughly 100 names reporting four times a year, that is
**about 16 events per bucket per year** — too few to learn anything from one bucket alone.

The fix is **partial pooling**: each cluster gets its own answer, but a cluster with little data
*borrows* from the overall pattern until it has enough of its own. Large clusters speak for
themselves; small ones are pulled toward the average instead of chasing noise. It is the standard
statistical answer to exactly the intuition you had.

---

## 7. INPUT — the factor library

**84 candidates across 14 families.** One rule governs every one of them:
**it must be knowable before the entry open.** A factor that uses anything published after entry is
look-ahead, and it voids the event.

Column key — **free history**: ✅ reconstructable for past quarters at no cost ·
⚠ live snapshot is free but history is not, or needs extra work · ❌ no reliable source.

### A · Price & volume — what the tape already did

| id | factor | why it could matter | evidence | free history |
|---|---|---|---|---|
| A1 | run-up 5 / 20 / 60d, raw and vs sector | stocks drift up into prints; retail over-extrapolates past gains | [pre-earnings over-extrapolation](https://mendoza.nd.edu/wp-content/uploads/2019/01/2016_spring_finance_seminar_series_peter_kelly_paper_updated_3_22_2016.pdf) | ✅ |
| A2 | distance from 52-week high | | | ✅ |
| A3 | realised volatility 20d | | | ✅ |
| A4 | volume surge (5d ÷ 60d average), and volume at the last few prints vs normal | stocks with high trading volume at *past* announcements earn the largest earnings premium — attributed to attention-driven small-investor buying | [Frazzini & Lamont 2007](https://www.nber.org/system/files/working_papers/w13090/w13090.pdf) | ✅ |
| A5 | gap history: average absolute gap and up-gap rate, last 8 prints | | | ✅ |
| A6 | trend: price vs 50d and 200d average | | | ✅ |
| A7 | relative strength vs sector ETF | | | ✅ |

### B · Implied volatility & options — what's already priced in *(your explicit ask)*

| id | factor | why it could matter | evidence | free history |
|---|---|---|---|---|
| B1 | implied move for the event | the options market's own forecast of size | | ⚠ free live; paid history |
| B2 | IV rank vs its own 1-year range | | | ⚠ |
| B3 | implied move ÷ this stock's historical earnings move | are options rich or cheap vs its own record? | | ⚠ |
| B4 | term structure: front-expiry IV − next-expiry IV | how big the event premium is | | ⚠ |
| B5 | put/call ratio, full chain and front expiry | positioning | | ✅ Alpha Vantage |
| B6 | skew: OTM put IV − ATM call IV | informed traders buy puts before bad news; the steepest smirks underperform by ~10.9% a year and precede the worst earnings shocks | [Xing, Zhang & Zhao 2010](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1107464) | ⚠ |
| B7 | unusual options volume before the print | | | ⚠ live only |

### C · Sentiment & positioning — institutions *and* retail

| id | factor | why it could matter | evidence | free history |
|---|---|---|---|---|
| C1 | short interest % of float, days to cover, change | short sellers trade ahead of bad news (later evidence mixed) | [Christophe, Ferri & Angel 2004](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2004.00681.x) | ⚠ snapshot |
| C2 | institutional ownership % and quarter-on-quarter change | | | ✅ EDGAR 13F (lagged) |
| C3 | analyst upgrades / downgrades, last 30 / 90d | | | ✅ yfinance (665 rows on ORCL) |
| C4 | price-target changes; price vs mean target | | | ✅ |
| C5 | retail attention: search and social volume vs baseline | retail search climbs about two weeks before a print; heavy pre-print search means a smaller reaction on the day | [Investor information demand around earnings](https://www.researchgate.net/publication/228259600_Investor_Information_Demand_Evidence_from_Google_Searches_Around_Earnings_Announcements) | ⚠ needs a source |
| C6 | retail herding intensity | the most-bought retail names averaged **−4.7%** abnormal return over the next 20 days — retail crowding is a *contrarian* signal | [Barber, Huang, Odean & Schwarz 2022](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.13183) | ⚠ needs a source |
| C7 | news sentiment, 7d, relevance-weighted | | | ✅ Alpha Vantage |
| C8 | sentiment momentum, 7d vs 30d | | | ✅ |

**Your idea that institutions trade on what retail expects** is testable directly, as an
*interaction*: retail attention × short interest (a crowded short running into retail buying), and
retail attention × implied move.

### D · Expectations — the bar the print is measured against

| id | factor | why it could matter | evidence | free history |
|---|---|---|---|---|
| D1 | EPS and revenue estimate revisions, 7 / 30 / 90d | | | ✅ Alpha Vantage — basis & timing to validate (§8) |
| D2 | estimate dispersion | more uncertainty, a bigger surprise either way | | ✅ Alpha Vantage (high / low) |
| D3 | walk-down: estimates cut into the print while the stock holds | analysts walk estimates down to beatable levels, most where the firm is raising capital or insiders plan to sell | [Richardson, Teoh & Wysocki 2004](https://onlinelibrary.wiley.com/doi/abs/10.1506/KHNW-PJYL-ADUB-0RP6) | ✅ Alpha Vantage (90d → 7d path) |
| D4 | beat rate, last 8 quarters | surprises tend to repeat | | ✅ — ⚠ EPS basis (§8) |
| D5 | average surprise size, last 4 | | | ✅ — ⚠ EPS basis (§8) |
| D6 | whisper number vs consensus | | | ❌ |

### E · Previous earnings *(your category)*

| id | factor | why it could matter | free history |
|---|---|---|---|
| E1 | excess reaction to the last print | | ✅ |
| E2 | last guide vs its own prior guide, **on the same basis** | a raise on a changed basis is not a raise — restate both sides first | ⚠ manual |
| E3 | consecutive-beat streak | | ✅ |
| E4 | drift since the last print vs sector | | ✅ |
| E5 | "beat but fell" count, last 4 prints | sell-the-news tendency | ✅ |
| E6 | history of meeting its own guidance | credibility | ⚠ manual |

### F · Peers *(your category)*

| id | factor | why it could matter | evidence | free history |
|---|---|---|---|---|
| F1 | average excess reaction of peers already reported this season | investors price late reporters off early ones; both under- and over-reaction are documented, so the *sign* has to be measured | [*Intra-industry information transfers*, Review of Accounting Studies 2019](https://link.springer.com/article/10.1007/s11142-019-9487-1) | ✅ |
| F2 | peers' guidance direction this season | | | ⚠ manual |
| F3 | early vs late reporter within its sector | late reporters show predictable pre-print drift | | ✅ |
| F4 | supply-chain read-through: key supplier or customer already reported | | | ⚠ mapping needed |
| F5 | sector ETF momentum into the event | | | ✅ |
| F6 | a mega-cap printing the same night | a large index weight moves everyone's benchmark | | ✅ |

### G · Structural change — lasting *(your category)*

G1 new product or platform cycle · G2 M&A · G3 business-model shift (e.g. bitcoin mining → AI
hosting) · G4 dated contract or capacity win; jump in RPO / backlog · G5 regulation (export
controls, drug pricing) · G6 pending index change · G7 capital raise, convertible, buyback.
*Mostly event-tagged from 8-K filings — ✅ dates, ⚠ tagging.*

### H · Temporary news *(your category)*

H1 pre-announcement in the last 30d · H2 non-earnings news shock in the last 14d · H3 macro event
inside the hold window (FOMC, CPI, jobs) · H4 sector headline shock · H5 recent investor day.
*✅ dates, ⚠ tagging.*

### I · Management *(your category)*

| id | factor | why it could matter | evidence | free history |
|---|---|---|---|---|
| I1 | CEO or CFO change, last 12 months | | | ✅ 8-K |
| I2 | net insider buying / selling, last 90d — open-market buys especially | | | ✅ |
| I3 | guidance style: sandbag score (guides low, then beats) | | | ⚠ |
| I4 | tone on the last call, especially Q&A | call tone predicts returns and drift; Q&A tone carries extra signal, strongest in firms without dividends | [Price, Doran, Peterson & Bliss 2012](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1625863) | ⚠ transcript source untested |
| I5 | equity-issuance incentive | walk-down to beatable targets is strongest here | [Richardson, Teoh & Wysocki 2004](https://onlinelibrary.wiley.com/doi/abs/10.1506/KHNW-PJYL-ADUB-0RP6) | ✅ |

### J · Direction of the company *(your category)*

J1 revenue growth and acceleration · J2 gross and operating margin, sequential and year-on-year ·
J3 forward book: RPO, backlog, deferred revenue · J4 capex intensity and direction · J5 exposure to
the live theme (AI, robotics, drones) · J6 earnings quality, `OCF / NI` · J7 cash runway for
unprofitable names. *✅ filed XBRL.*

### K · Business structure — "understand the business"

K1 recurring vs transactional revenue · K2 customer concentration · K3 operating leverage ·
K4 cyclicality · K5 stage (§6) · K6 size and liquidity.

### L · Event mechanics

L1 BMO vs AMC · L2 weekday · L3 date confirmed or estimated · L4 days since the last print ·
L5 reporting lag after quarter-end.

### M · Market regime

M1 VIX level and 5d change · M2 SPY / QQQ 20d trend · M3 sector vs SPY, 20d · M4 BTC 20d
(crypto-proxy cluster only).

### N · How institutions and quants are positioned

N1 crowding in hedge-fund holdings (13F) · N2 gap between options-implied and analyst expectations ·
N3 up-volume vs down-volume into the print · N4 momentum-factor crowding · N5 dealer gamma
(⚠ paid, probably out of reach).

> **Nothing here is pre-judged.** Several of these factors were used — and some were declared broken —
> by the retired PRE v1 model. That verdict does **not** carry over: PRE v1's record was contaminated
> (§9), so its opinion of any factor is not evidence. **Every factor enters at zero.**

---

## 8. INPUT — the data sources, tested rather than assumed

The Alpha Vantage and yfinance rows were **probed live on 2026-09-13**, not taken from their documentation — and that already
mattered. A summary of the Alpha Vantage docs called news sentiment, insider trades and the earnings
calendar *premium*; **all three returned data on the free key.** So did historical put/call, and so did
estimate history. Only historical options came back genuinely blocked; the ETF-holdings endpoint the
leave-one-out benchmark needs is still untested (it was rate-limited). Every raw response is saved in
`analysis/exploratory/2026-09-13_source_probes/`.

| source | cost | what it gives | history | verdict |
|---|---|---|---|---|
| **yfinance** | free | prices and volume; earnings dates **with timestamps**; surprise history; analyst actions (665 rows on ORCL); insider trades; current option chains, short interest and estimates | prices, earnings, analyst actions ✅ · options, short interest, estimates **snapshot only** | the backbone |
| **SEC EDGAR / XBRL** | free, needs a User-Agent | filed financials; 8-K releases and guidance text; Form 4; 13F | ✅ | authoritative for fundamentals and guidance |
| **Alpha Vantage** — your key is **free** | **25 calls/day, 1/second** | ✅ earnings history with BMO/AMC back to 1996 · ✅ news sentiment (per-ticker score + relevance) · ✅ insider trades · ✅ **historical put/call by expiry** · ✅ **estimate history per quarter back to 2017** (7/30/60/90-day averages, up/down revisions, high/low) · ✅ earnings calendar | ✅ | good, but **25 calls a day cannot cover ~100 names × several endpoints** |
| Alpha Vantage | premium | ❌ historical options and implied volatility — **confirmed blocked** | — | not usable on the free key |
| **FMP** | a key already exists in the DRIVE repo | estimates, transcripts, 13F, insiders | partial | rate-limited on the free tier |
| **ThetaData** | from **$40/month** ("Options Value"); no free tier shown | historical options: IV, Greeks, open interest | ✅ | the realistic paid route to B-family history |
| Google Trends / Reddit | unofficial / free key | retail attention | partial | ⚠ flaky; needed only for C5–C6 |

### Two findings that shape the whole design

1. **Live capture is nearly free; history is where the money goes.** Snapshot option chains, short
   interest and estimates *at decision time* with yfinance, and the forward record builds itself at
   no cost. Only a *backfill* of past quarters needs paid options history.
2. **Report timing must never rest on one source.** 962 of 1,064 rows on the Alpha Vantage calendar
   carry no BMO/AMC flag at all, and yfinance's `.calendar` is a day late for after-close reporters.
   **Rule: confirm date and session from two sources, one of them the company.**
3. **The same vendor disagrees with itself.** For ORCL's quarter ending 2026-08-31, Alpha Vantage's
   earnings history gives a consensus of **1.39** (reported 1.63 — a 17% beat), while its estimates
   history gives **1.74**. The likeliest
   cause is two different EPS bases (GAAP vs adjusted). A beat-rate factor built on the wrong one would
   measure a surprise **nobody traded**. **Rule: one EPS basis — the adjusted consensus the market
   reports — validated per source before any history is built**, along with whether "7 / 30 / 90 days
   ago" is anchored to the report date or to today (if it's today, it cannot build history at all).

---

## 9. The rules that stop this experiment lying 🔒

The retired PRE v1 model was not killed by its hit rate. It was killed because **its scoring was
changed four times while it was being measured**, each change prompted by a loss — so its record
belonged to no single model. Every rule below exists to stop that happening again.

1. **Freeze before entry.** The factor snapshot, the theses and all three decisions are hashed and
   git-committed **before the entry open**. Anything created after the open is *void*, not late.
2. **One primary outcome, chosen now.** The exit and the WIN definition cannot change after the
   first trade.
3. **Grade every eligible name** — BUY and NO_BUY alike.
4. **Code grades. AI never does.** The AI decides in T2; it never computes or judges an outcome.
5. **No edits to a live rule.** An idea that would change the rule creates **a new rule version**
   with its own clean clock, and the old version keeps being scored, untouched, until its window
   ends. *This one rule is the direct fix for what killed PRE v1.*
6. **Discovery and proof never share data.** A pattern found in a dataset is a *candidate*. It
   becomes a finding only when it holds on data it was not found in.
7. **Count the tests.** 84 factors × 8 clusters guarantees chance "patterns".
   *Exploration:* a factor is promoted only if it survives false-discovery-rate control **and**
   clears **t > 3** — across hundreds of tested factors, most that merely pass t > 2 are noise
   ([Harvey, Liu & Zhu 2016](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2249314)).
   *Confirmation:* only the few pre-registered hypotheses are tested, at 5%, corrected for how many
   were registered.
8. **No claim below a minimum sample.** Under 30 events **and** 10 separate event-dates, a result is
   reported as **"insufficient"** — never "works", never "no effect".
9. **The universe is a rule, not a feeling** (§10). "Trendy" is measured — implied vol, attention,
   short interest, theme exposure — never chosen because a name moved recently, which would be
   selecting on the answer.
10. **Portfolio-blind.** Decisions never read what you own. Owning a name is a reason to *want* an
    answer, and wanting an answer is the bias this design exists to guard against.
11. **Carry over facts about sources, never conclusions about factors.** From PRE v1 we keep:
    yfinance `.calendar` is a day off for AMC; SEC requires a User-Agent; the clock runs on US
    Eastern; verify every figure at source. We keep **nothing** about which factors predict.

> ⚠ **A bias note on this document itself.** It was drafted inside a conversation that holds PRE v1's
> entire history — which is exactly the kind of contamination rule 11 guards against. Mitigations:
> no factor is pre-judged (§7); experiment sessions are opened in *this* folder, which loads only this
> project's rules; the archive is fenced (`archive/README.md`); and an **external reviewer checks the
> design before the first trade** (§12).

---

## 10. The universe rule 🔒

**In**, if every condition holds on the season's screening date:
- US-listed common stock, market cap **≥ $2B**
- its **industry** is on the cluster allowlist below — **never its broad sector label**
- **implied move for the event ≥ 4%**, taken from the option expiry that straddles the print — your
  "moves too little to be worth measuring", made mechanical
- liquid options: enough front-expiry open interest and a tight enough spread to trust the implied move
- report date **and** session confirmed from two sources

### ⚠ Why industries, not sectors — tested on the first four weeks

I ran a sector-and-size screen over everyone reporting Sep 14 – Oct 9. **34 names passed — including two
homebuilders, an RV maker, a ski-resort operator, an auto-parts chain, a used-car dealer, a payroll
processor, a lighting company, a plasma-drug maker with flat revenue, and Manchester United.** Every one
carries a broad sector label the screen allowed. A sector label cannot express *AI infrastructure* or
*slow-growth*, so it admits exactly the names you said you don't care about — and implied volatility
doesn't rescue it: both homebuilders show 52–54% implied vol on options that span their own print.

The same screen did surface what the experiment is for: **MU** (Sep 30, after close), **APLD** and
**PENG** (AI infrastructure), **AEHR** (semiconductor test equipment), **JBL** (electronics
manufacturing) and **BB**. Evidence and caveats: `analysis/exploratory/2026-09-13_pilot_screen/`.

### Draft allowlist — ⚠ your decision (§12), set once before the season

Setting this once, before any data, is what stops it becoming a dial that gets turned later.

| cluster | industries IN |
|---|---|
| AI infrastructure & compute | data-center and IT-services operators with AI-hosting revenue · bitcoin miners hosting AI compute |
| Semiconductors & equipment | semiconductors · semiconductor equipment & materials |
| Software & internet | application and infrastructure software · internet content & information · security |
| Tech hardware & networking | computer hardware · communication equipment · electronic components · electronics manufacturing |
| Drones, robotics, space & defense-tech | aerospace & defense · machinery where robotics or autonomy is the product |
| Consumer | internet and specialty retail · apparel & footwear · restaurants — **gated by implied move alone**, because mature consumer names still gap hard on prints |
| Healthcare growth | biotechnology · medical devices — largest names only |
| Crypto-proxy | named individually (MSTR) |

**Out:** energy · materials, mining, agriculture · utilities · REITs · banks and insurers · consumer
staples · **residential construction · RVs · auto dealers and parts · resorts and leisure** ·
slow-growth industrials that aren't drones, robotics or defense-tech · mature tech services (payroll,
IT outsourcing) · healthcare outside the largest growth names.

**Screened once per season, on a fixed date.** A name added mid-season enters with a flag — never
silently.

---

## 11. Timeline — and what is honest about it

| phase | dates | what happens | produces |
|---|---|---|---|
| **0 · Build** | Sep 14–18 | freeze exit and outcome; universe rule; factor definitions; snapshot → hash → commit pipeline; grading code; **external design review** | a frozen spec |
| **1 · Pilot** | Sep 21 – Oct 9 | the full pipeline live on the few eligible names reporting | bugs, not findings — rows kept, flagged `pilot` |
| **2 · History study** | Sep 21 – Oct 9, in parallel | rebuild the free factor families (A, C3–C4, D4–D5, E, F, I, J) for the past 8–12 quarters | **candidates only** → rule v0, frozen before Oct 12 |
| **3 · Season A** | Oct 12 – Nov 20 | Q3 season live: T0, T1 (rule v0), T2 — and options data captured free as it happens | **first out-of-sample read on rule v0** + exploratory data for v1 |
| **4 · Register** | late Nov | freeze confirmatory hypotheses and rule v1 | hypotheses v1, hashed |
| **5 · Season B** | Jan – Feb 2027 | confirmatory. Rule v1 frozen. **No edits.** | the first test at full strength |
| **6 · Verdict** | early Mar 2027 | pre-registered tests only | the answer — pooled first |

**The honest parts.**

- **The first weeks are thin — measured, not guessed.** Of 188 US reporters between Sep 14 and Oct 9
  (a date-sorted calendar preview that runs to Oct 28, so this window is complete), **34** pass a
  sector-and-size screen. Under the draft allowlist (§10) the core AI, semiconductor, software and
  hardware clusters get only a handful: **BB** (Sep 24), **JBL** and **MU** (Sep 30), then **AEHR**,
  **PENG** and **APLD** (Oct 5–8). A few more would enter through the defense and healthcare rows
  (e.g. AIR, ABVX), and through consumer names whose implied move clears 4% — which that screen could
  not measure. Real volume arrives from Oct 19; **MU on Sep 30** is the first event that fits cleanly.
  Weeks one to three are for shaking out the pipeline.
- **End of November** gives a first out-of-sample read on rule v0 — built on free factors only, and
  with ~80–100 events it can only detect a *large* effect.
- **Around March 2027** is the first test including options factors and AI judgment at full strength —
  for the pooled question, *does selection beat buying everything?*
- **Per-cluster answers take several seasons** unless an effect is big. That is the price of
  splitting by business type, and it is worth paying: a pooled answer can hide a strong effect that
  lives in a single cluster.

---

## 12. What I need from you

| # | decision | default if you don't choose | blocks |
|---|---|---|---|
| 1 | **Primary exit** — A first open after the print · B reaction-day close · C +5 days | **A** | the first trade |
| 2 | Primary outcome = beat the sector (excess), with raw P&L reported alongside | **yes** | the first trade |
| 3 | "bmc" in your message means BMO | **yes** | the first trade |
| 4 | Historical options data for the backfill — ThetaData ~$40/month, or skip and let Season A capture it free | **skip for now** | Phase 2 only |
| 5 | Retail-attention source — a free Reddit API key, or leave C5–C6 out of v0 | **leave out of v0** | nothing |
| 6 | Real trades, paper trades, or signals only? Outcomes are graded from market prices either way | **signals only** | nothing |
| 7 | **Industry allowlist** (§10) — which industries count, cluster by cluster | **the draft in §10** | the universe freeze |

**External evaluator: yes — before the first trade, not after.** Last time, the one reviewer who found
the fatal flaw found it in a finished record, when it could no longer be fixed. A design review now
can catch a flaw while it is still free. I'll prepare the brief this week (`reviews/`).

---

## References — located 2026-09-13 · every figure and quote re-checked against the saved lookups 2026-09-14

- Frazzini & Lamont (2007), *The earnings announcement premium and trading volume* —
  [NBER w13090](https://www.nber.org/system/files/working_papers/w13090/w13090.pdf) · global evidence:
  [*The earnings announcement premium around the globe*, JFE 2013](https://www.sciencedirect.com/science/article/abs/pii/S0304405X12002188)
- Skinner & Sloan (2002), *Earnings surprises, growth expectations, and stock returns* —
  [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=172060)
- Xing, Zhang & Zhao (2010), *What does individual option volatility smirk tell us about future equity
  returns?* — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1107464)
- Barber, Huang, Odean & Schwarz (2022), *Attention-induced trading and returns: evidence from
  Robinhood users* — [Journal of Finance](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.13183)
- Christophe, Ferri & Angel (2004), *Short-selling prior to earnings announcements* —
  [Journal of Finance](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2004.00681.x)
- Richardson, Teoh & Wysocki (2004), *The walk-down to beatable analyst forecasts* —
  [Contemporary Accounting Research](https://onlinelibrary.wiley.com/doi/abs/10.1506/KHNW-PJYL-ADUB-0RP6)
- *Intra-industry information transfers: evidence from changes in implied volatility around earnings
  announcements* — Review of Accounting Studies (2019),
  [Springer](https://link.springer.com/article/10.1007/s11142-019-9487-1)
- Price, Doran, Peterson & Bliss (2012), *Earnings conference calls and stock returns: the incremental
  informativeness of textual tone* — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1625863)
- *Investor information demand: evidence from Google searches around earnings announcements* —
  [ResearchGate](https://www.researchgate.net/publication/228259600_Investor_Information_Demand_Evidence_from_Google_Searches_Around_Earnings_Announcements)
- *Pre-earnings announcement over-extrapolation* —
  [working paper](https://mendoza.nd.edu/wp-content/uploads/2019/01/2016_spring_finance_seminar_series_peter_kelly_paper_updated_3_22_2016.pdf)
- Harvey, Liu & Zhu (2016), *…and the cross-section of expected returns* —
  [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2249314)
