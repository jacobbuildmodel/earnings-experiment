# Literature review — what moves prices around earnings

> **2026-09-16/17 · written for the Earnings Experiment · Jacob's request of 2026-09-16.**
> Every idea here is a **CANDIDATE** (rule 6). A published result is someone else's in-sample
> discovery, on other stocks, in other years, over a different window. Nothing here is evidence that a
> factor works in *our* universe. Written without reading `archive/` (rule 10).

## How the papers were checked

The web-search tool returns AI summaries, and those have fabricated figures before (CLAUDE.md). So
every paper carries a verification tier:

| tier | meaning | what we may quote from it |
|---|---|---|
| **V1** | abstract read on a primary page: publisher, RePEc/EconPapers, NBER, CEPR, or the authors' own PDF or post | figures, as written in that abstract |
| **V2** | existence and bibliography confirmed on several publisher and index listings; abstract seen only through the search summary | the qualitative claim only, **never a figure** |

**Caught while checking:**
- *Jin, Livnat & Zhang (2012)* is titled "Option Prices Leading Equity Prices…". It is not "Option
  Prices Leak Information", which was the title recalled from memory.
- *Barber et al. (2013)*: a search summary gave the global premium as "over 11 percent annually". That
  figure is **not** in the paper's own abstract (V1 check), so it is not used.
- *McLean & Pontiff*: the only primary text read is the **2012 working paper**: 82 characteristics,
  about 10% out-of-sample decay (not significant), and **about 35% post-publication decay**. The
  published 2016 version (97 variables) reports different figures, which were seen only in a search
  summary and are not quoted.
- *Savor & Wilson*: the annualised premium figure seen in a search summary was not verified. The 2011
  draft (V1) confirms that early announcers earn more and late announcers less.

Only abstracts were read — no full texts. Before any candidate becomes a registered hypothesis, the
paper's method section is read, so our factor matches its definition.

---

## 1. Five things the literature says that change how we read our own results

**1 · Buying into earnings has paid on average — so T0 is a real opponent.**
Stock prices tend to rise around scheduled announcements. Frazzini & Lamont link this premium to
volume surges and to small-investor buying [V2]. Savor & Wilson find it persistent, larger for early
announcers and smaller for late ones, and argue it is compensation for risk [V1, draft]. Barber et al.
find it across countries, strongest where uncertainty rises most [V1]. So T0, "buy everything", may
well have a hit rate above 50% on its own. That is exactly why D001 makes T0, not 50%, the bar.

**2 · Published edges shrink.**
Post-publication decay was about 35% in McLean & Pontiff's 2012 draft [V1]. Martineau: "for large
stocks, PEAD have been non-existent since 2006" [V1]. Our universe is ≥ $2B, which means large stocks.
**Expect any effect here to be weaker than its paper reports, and some to be zero.** A result from
1990s data is a place to look, not a prior to lean on.

**3 · Mispricing concentrates on earnings days, which supports the whole design.**
Across 97 anomalies, returns are "six times higher on earnings announcement days", and the authors
read this as biased expectations being corrected when news arrives (Engelberg, McLean & Pontiff) [V1].
If ordinary anomaly signals (value, momentum, quality…) pay out mostly on print days, then a composite
of those signals is a principled T1 input.

**4 · Our window is odd, and most papers do not measure it.**
Most studies use 2- or 3-day abnormal returns around the announcement, or months of drift. D001
measures raw direction from one open before the print to the first open after it: one intraday
session plus one overnight gap. Lou, Polk & Skouras show that strategy profits split sharply between
the overnight and intraday components, often with opposite signs [V2]. **So a factor that works on a
3-day window may not work on ours.** Every candidate below carries a "window fit" note.

**5 · Most predictors change the size of the reaction, not its sign.**
Distraction, Friday timing and attention make the immediate reaction smaller and the drift larger
(DellaVigna & Pollet: 15% lower immediate response [V1]; Hirshleifer, Lim & Teoh [V2]). That matters
for magnitude, which we record but do not test first. For a direction test, these are **modifiers**:
they belong in interactions, not as stand-alone BUY signals.

---

## 2. Theory — why prices would be predictable at all

| idea | papers | what it predicts around a print |
|---|---|---|
| **Conservatism + representativeness** | Barberis, Shleifer & Vishny 1998 [V2] | underreaction to a single piece of news; overreaction to a *run* of similar news |
| **Overconfidence + self-attribution** | Daniel, Hirshleifer & Subrahmanyam 1998 [V2] | short-run momentum and earnings drift; long-run reversal |
| **Slow information diffusion** | Hong & Stein 1999 [V2] | short-run underreaction, which momentum traders later push into overreaction |
| **Divergence of opinion + short-sale limits** | Miller 1977 [V2, bibliography only]; tested by Berkman et al. 2009 [V2] | disputed stocks are overpriced before the print, and the print settles the dispute — **downwards** |
| **Limits to arbitrage** | Shleifer & Vishny 1997 [V2]; Mendenhall 2004 [V2] | mispricing survives where arbitrage is risky or costly; drift is larger where arbitrage risk is higher |
| **Limited attention** | DellaVigna & Pollet 2009 [V1]; Hirshleifer, Lim & Teoh 2009 [V2]; Barber & Odean 2008 [V2] | slower reaction when attention is scarce; retail *buying* concentrates in attention-grabbing stocks |
| **Disposition effect** | Frazzini 2006 [V2] | news travels slowly when it has the same sign as holders' unrealised gains or losses |
| **Contrast effects** | Hartzmark & Shue 2018 [V2] | today's print looks worse if yesterday's prints were good, and better if they were bad |
| **Market makers price inventory risk** | So & Wang 2014 [V1] | pre-print price pressure is compensated. Short-term reversals are "six-fold" larger at announcements |

---

## 3. Candidate factors

**Sign** = the direction that favours BUY. **Window fit**: ✅ the paper's window is close to ours ·
⚠ a different window, so the effect may not carry over · ❓ unclear. **Data**:
- **free** — free now, including history
- **fwd** — free only if we capture it live, going forward
- **paid** — needs a paid source
- **none** — no known source

**Family** maps to FRAMEWORK §7.

### Attention and retail flow

| id | candidate | sign for BUY | evidence | window fit | data | family |
|---|---|---|---|---|---|---|
| LR01 | **Extreme 12-month winner** going into the print | **−** | top prior-12m-return stocks: +1.58% in the 5 days *before*, **−1.86%** in the 5 days *after* (Aboody, Lehavy & Trueman 2010) [V1] | ⚠ our entry is 1 session before the print, so most of the run-up is already gone and the post-print fall is what we hold | free | A |
| LR02 | **High volume at past announcements** | + | the announcement premium is largest where past announcement volume was highest (Frazzini & Lamont) [V2] | ⚠ monthly / announcement-window | free | A · E |
| LR03 | **Early reporter** in the season | + | early announcers earn more, late ones less (Savor & Wilson) [V1 draft] | ⚠ | free | L |
| LR04 | **Retail net buying before the print** | + | "intense aggregate individual investor buying (selling) predicts large positive (negative) abnormal returns on and after" the announcement (Kaniel et al. 2012) [V1]; retail net buying beats net selling by about 10 bp over the next week (Boehmer et al. 2021) [V1] | ✅ / ⚠ | **paid** (TAQ-based) → out of v0, as STATE already defaults | C |
| LR05 | **Search-volume spike** (Google Trends) | + short-run, then reversal | a rise in search volume predicts higher prices over the next 2 weeks, then reversal (Da, Engelberg & Gao 2011) [V2] | ❓ | free, but the unofficial API is flaky | C |
| LR06 | **Many other firms report the same day** | modifier (weaker reaction) | Hirshleifer, Lim & Teoh [V2]; the distraction effect is stronger for positive surprises | ✅ | free (the calendar) | L |
| LR07 | **Friday print** | modifier (−15% immediate response) | DellaVigna & Pollet [V1] | ✅ | free | L |

### Positioning, disagreement and short sellers

| id | candidate | sign | evidence | fit | data | family |
|---|---|---|---|---|---|---|
| LR08 | **High divergence of opinion** (analyst dispersion, turnover, volatility), stronger when hard to short | **−** | high-disagreement stocks earn significantly lower announcement returns, most negative where shorting is hardest (Berkman et al. 2009) [V2] | ✅ announcement window | dispersion: partial (AV estimate high/low); turnover and volatility: free; borrow cost: paid | C · N |
| LR09 | **Abnormal short selling in the 5 days before** | **−** | pre-announcement abnormal shorting is linked to post-announcement returns — informed shorts (Christophe, Ferri & Angel 2004, Nasdaq) [V2] | ✅ | FINRA daily short-sale volume files: free (**to be probed**) | C · N |
| LR10 | **Short-term pre-print price pressure** (last 1–5 days' return) | **−** (reversal) | reversals are six-fold larger at announcements (So & Wang 2014) [V1] | ✅ the closest match to our entry | free | A |
| LR11 | **Lottery-like stock** (a big maximum daily return last month) | **−** | high-MAX stocks underperform by >1% a month (Bali, Cakici & Whitelaw 2011) [V1] | ⚠ monthly | free | A |

### Options — what is already priced

| id | candidate | sign | evidence | fit | data | family |
|---|---|---|---|---|---|---|
| LR12 | **Calls rich against puts** (implied-vol spread at matched strikes) | + | expensive-call stocks beat expensive-put stocks by 50 bp a week, with decay over the sample (Cremers & Weinbaum 2010) [V1]; >1.5% over a 2-day announcement window (Atilgan 2014) [V1]; the signal is strongest *just before* events (Jin, Livnat & Zhang 2012) [V1] | ✅ | **fwd** (yfinance chains captured before entry) | B |
| LR13 | **Steep put skew** | **−** | steepest-smirk stocks underperform by 10.9% a year, and they have the worst next-quarter earnings shocks (Xing, Zhang & Zhao 2010) [V1] | ⚠ months | fwd | B |
| LR14 | **Low put/call volume ratio** | + | low-ratio stocks beat high-ratio stocks by >40 bp the next day (Pan & Poteshman 2006) [V1]. ⚠ Their ratio uses *buyer-initiated opening* volume, which we cannot see; plain volume is a weaker proxy | ✅ next-day | fwd (plain volume only); the AV historical put/call endpoint works (probe 11) | B |
| LR15 | **High option-to-stock volume ratio** | **−** | lowest-decile O/S beats highest by 0.34% a week, and O/S predicts earnings news (Johnson & So 2012) [V1] | ⚠ weekly | fwd | B |
| LR16 | **Implied move vs realised history** | not a sign — a universe and risk note | pre-announcement straddles earned 3.34%, so investors *underestimate* announcement uncertainty (Gao, Xing & Zhang 2018) [V1]; the implied announcement uncertainty is informative about later volatility (Dubinsky et al. 2019) [V2] | — | fwd | B |

⚠ **Modern options market.** Retail now exceeds 60% of US options volume, and retail prefers cheap
weekly options with a 12.6% average spread (Bryzgalova, Pavlova & Sikorskaya 2023) [V1]. Option
signals estimated on pre-2020 data may mean something different now. Treat B-family priors as weak.

### Expectations and earnings history

| id | candidate | sign | evidence | fit | data | family |
|---|---|---|---|---|---|---|
| LR17 | **Last quarter's surprise** (sign and size) | + for quarters t+1…t+3; **−** for t+4 | the next announcements' 3-day reactions are predictable from quarter t, matching the autocorrelation of earnings (Bernard & Thomas 1990) [V2] | ✅ 3-day | free, **once the EPS basis is pinned** (STATE #3) | E |
| LR18 | **High-seasonality quarter** (this fiscal quarter is historically the biggest) | + | higher returns when high-seasonality earnings are due; analysts too pessimistic (Chang, Hartzmark, Solomon & Soltes 2017) [V2] | ⚠ | free (quarterly history) | E |
| LR19 | **Consensus walked down** before the print | + (beatable bar) | analysts walk forecasts down to beatable levels, most when the firm or insiders will sell after the print (Richardson, Teoh & Wysocki 2004) [V2]; meeting or beating earns a return premium even when it was managed (Bartov, Givoly & Hayn 2002) [V2] | ⚠ quarter-level | AV estimate revisions: free, basis TBD | D · I |
| LR20 | **Growth or glamour valuation** | **−** on mean return (asymmetric) | growth stocks fall disproportionately on negative surprises (Skinner & Sloan 2002) [V2]; value stocks' surprises are systematically more positive (La Porta et al. 1997) [V2] | ✅ announcement | free | J · K |
| LR21 | **Peer-driven pre-print move** (the stock moved on peers' prints) | **−** (reversal) | the market overreacts to early reporters' news for late reporters, and corrects at the late reporter's own print (Thomas & Zhang 2008) [V2] | ✅ | free | F |
| LR22 | **Yesterday's prints were good** (market-wide or large-cap surprises) | **−** | contrast effect (Hartzmark & Shue 2018) [V2] | ✅ day-level | free, once surprise basis pinned | F · M |

### Scheduling — what the company's calendar gives away

| id | candidate | sign | evidence | fit | data | family |
|---|---|---|---|---|---|---|
| LR23 | **Scheduled later than expected** (vs the same quarter last year) | **−** | late schedulers announce worse news; equity prices miss this until the print, while options price the volatility-timing information efficiently (Johnson & So 2018) [V2] | ✅ the signal is known weeks ahead | free (proxy: last year's date) | L |
| LR24 | **Friday, after-hours, or busy-day slot; short notice** | **−** | surprises are much lower for Friday, after-hours and busy-day reporters, and shorter notice goes with worse news (deHaan, Shevlin & Thornock 2015) [V1, via the authors' own post] | ✅ | free, except notice lead-time (announcement dates of the *schedule* are hard to get → partial) | L |

> ⚠ LR24 and D001 interact: most of our names report after the close, so "after-hours" barely varies
> in our universe. Friday and busy-day slots still vary.

### Sentiment and news tone

| id | candidate | sign | evidence | fit | data | family |
|---|---|---|---|---|---|---|
| LR25 | **Market sentiment regime × cluster** | high sentiment: good news rewarded more, bad news punished less; the effect is strongest in young, volatile, unprofitable and extreme-growth stocks | Mian & Sankaraguruswamy 2012 [V2]; Baker & Wurgler 2006 [V2] | ✅ | the Baker-Wurgler index is published with a lag → use a live proxy (to be chosen and frozen) | M |
| LR26 | **Negative tone of pre-print news** | **−** | a higher share of negative words forecasts lower earnings, and prices briefly underreact (Tetlock, Saar-Tsechansky & Macskassy 2008) [V2] | ⚠ | AV NEWS_SENTIMENT: free, rate-limited (probe 08) | C · H |
| LR27 | **Composite anomaly score** (value, momentum, profitability…) | + for the long side | anomalies pay six times more on announcement days (Engelberg, McLean & Pontiff 2018) [V1] | ✅ | free | A · J |

---

## 4. What this means for Jacob's question — "does it differ by type of business?"

The literature gives a **reason to expect** cluster differences:
- Sentiment effects (LR25) and the growth "torpedo" (LR20) are strongest in young, volatile,
  unprofitable, extreme-growth stocks. That is the AI-infrastructure and software clusters, not
  healthcare or consumer.
- Disagreement (LR08) should matter most where valuations are hardest to pin down.

**A pre-registrable, literature-backed hypothesis:** *in high-valuation, high-volatility clusters,
disagreement and sentiment factors separate BUY from NO_BUY better than in other clusters.* It stays a
candidate until the history study (Phase 2) and Season A have tested it on data it was not drawn from.

## 5. Counting the tests (rule 7)

27 candidates × 8 clusters is 216 cells before any interaction. At 5%, about 11 cells would "work" by
chance alone. The history study must:
- apply false-discovery control and t > 3
- report every cell tested, not just the survivors
- pool across clusters first

Candidates that need **fwd** data (LR12–LR16) cannot be history-tested at all on the free route. They
are collected from Season A onward and are exploratory until Season B.

## 6. Actions this review creates

1. **Probe** FINRA daily short-sale volume (LR09) — free, and it has history.
2. **Before the first entry, start capturing option chains** (LR12–LR16), even though no rule uses
   them yet. Data not captured before the print can never be recovered free.
3. **Pin the EPS basis** (STATE #3). LR17, LR19 and LR22 all depend on it.
4. **Choose a live sentiment proxy** for LR25 and freeze it with the universe.
5. For each candidate that enters the history study, read the paper's method section and record
   the exact definition used.

## Not cited — recalled but not verified in this pass

Ball & Brown 1968 (seen only as a citation inside Bernard & Thomas 1989 [V2]) · Kahneman & Tversky
1979 · Grinblatt & Han 2005 · Kumar 2009 · Lee, Mucklow & Ready 1993 · Diavatopoulos et al. 2012 ·
Matsumoto 2002 · Kasznik & McNichols 2002. None of them is used above.

---

## References

| # | paper | tier | link |
|---|---|---|---|
| 1 | Aboody, Lehavy & Trueman (2010), Limited attention and the earnings announcement returns of past stock market winners, *Review of Accounting Studies* 15(2) 317–344 | V1 | [RePEc](https://ideas.repec.org/a/spr/reaccs/v15y2010i2d10.1007_s11142-009-9104-9.html) |
| 2 | Atilgan (2014), Volatility spreads and earnings announcement returns, *J. Banking & Finance* 38, 205–215 | V1 | [RePEc](https://ideas.repec.org/a/eee/jbfina/v38y2014icp205-215.html) |
| 3 | Baker & Wurgler (2006), Investor sentiment and the cross-section of stock returns, *J. Finance* 61(4) 1645–1680 | V2 | [RePEc](https://ideas.repec.org/a/bla/jfinan/v61y2006i4p1645-1680.html) |
| 4 | Bali, Cakici & Whitelaw (2011), Maxing out: stocks as lotteries…, *J. Financial Economics* 99(2) 427–446 | V1 | [NBER w14804](https://www.nber.org/papers/w14804) |
| 5 | Barber & Odean (2008), All that glitters…, *Review of Financial Studies* 21(2) 785–818 | V2 | [EconPapers](https://econpapers.repec.org/RePEc:oup:rfinst:v:21:y:2008:i:2:p:785-818) |
| 6 | Barber, De George, Lehavy & Trueman (2013), The earnings announcement premium around the globe, *JFE* 108(1) 118–138 | V1 | [RePEc](https://ideas.repec.org/a/eee/jfinec/v108y2013i1p118-138.html) |
| 7 | Barberis, Shleifer & Vishny (1998), A model of investor sentiment, *JFE* 49(3) 307–343 | V2 | [EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:49:y:1998:i:3:p:307-343) |
| 8 | Bartov, Givoly & Hayn (2002), The rewards to meeting or beating earnings expectations, *J. Accounting & Economics* 33(2) 173–204 | V2 | [RePEc](https://ideas.repec.org/a/eee/jaecon/v33y2002i2p173-204.html) |
| 9 | Berkman, Dimitrov, Jain, Koch & Tice (2009), Sell on the news…, *JFE* 92(3) 376–399 | V2 | [EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:92:y:2009:i:3:p:376-399) |
| 10 | Bernard & Thomas (1989), Post-earnings-announcement drift: delayed price response or risk premium?, *J. Accounting Research* 27, 1–36 | V2 | [RePEc](https://ideas.repec.org/a/bla/joares/v27y1989ip1-36.html) |
| 11 | Bernard & Thomas (1990), Evidence that stock prices do not fully reflect the implications of current earnings for future earnings, *JAE* 13(4) 305–340 | V2 | [Deep Blue](https://deepblue.lib.umich.edu/handle/2027.42/28288) |
| 12 | Boehmer, Jones, Zhang & Zhang (2021), Tracking retail investor activity, *J. Finance* 76(5) 2249–2305 | V1 | [RePEc](https://ideas.repec.org/a/bla/jfinan/v76y2021i5p2249-2305.html) |
| 13 | Bryzgalova, Pavlova & Sikorskaya (2023), Retail trading in options and the rise of the big three wholesalers, *J. Finance* 78(6) 3465–3514 | V1 | [CEPR DP17688](https://cepr.org/publications/dp17688) |
| 14 | Chang, Hartzmark, Solomon & Soltes (2017), Being surprised by the unsurprising: earnings seasonality and stock returns, *RFS* 30(1) 281–323 | V2 | [EconPapers](https://econpapers.repec.org/RePEc:oup:rfinst:v:30:y:2017:i:1:p:281-323.) |
| 15 | Christophe, Ferri & Angel (2004), Short-selling prior to earnings announcements, *J. Finance* 59(4) 1845–1876 | V2 | [Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2004.00681.x) |
| 16 | Cremers & Weinbaum (2010), Deviations from put-call parity and stock return predictability, *JFQA* 45(2) 335–367 | V1 | [RePEc](https://ideas.repec.org/a/cup/jfinqa/v45y2010i02p335-367_00.html) |
| 17 | Da, Engelberg & Gao (2011), In search of attention, *J. Finance* 66(5) 1461–1499 | V2 | [Wiley](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.2011.01679.x) |
| 18 | Daniel, Hirshleifer & Subrahmanyam (1998), Investor psychology and security market under- and overreactions, *J. Finance* 53(6) 1839–1885 | V2 | [Wiley](https://onlinelibrary.wiley.com/doi/10.1111/0022-1082.00077) |
| 19 | deHaan, Shevlin & Thornock (2015), Market (in)attention and the strategic scheduling and timing of earnings announcements, *JAE* 60(1) 36–55 | V1 (authors' post) | [Harvard Law forum](https://corpgov.law.harvard.edu/2015/04/21/market-inattention-and-the-strategic-scheduling-and-timing-of-earnings-announcements/) |
| 20 | DellaVigna & Pollet (2009), Investor inattention and Friday earnings announcements, *J. Finance* 64(2) 709–749 | V1 | [RePEc](https://ideas.repec.org/a/bla/jfinan/v64y2009i2p709-749.html) |
| 21 | Dubinsky, Johannes, Kaeck & Seeger (2019), Option pricing of earnings announcement risks, *RFS* 32(2) 646–687 | V2 | [OUP](https://academic.oup.com/rfs/article-abstract/32/2/646/5001193) |
| 22 | Engelberg, McLean & Pontiff (2018), Anomalies and news, *J. Finance* 73(5) 1971–2001 | V1 | [RePEc](https://ideas.repec.org/a/bla/jfinan/v73y2018i5p1971-2001.html) |
| 23 | Frazzini (2006), The disposition effect and underreaction to news, *J. Finance* 61(4) 2017–2046 | V2 | [EconPapers](https://econpapers.repec.org/RePEc:bla:jfinan:v:61:y:2006:i:4:p:2017-2046) |
| 24 | Frazzini & Lamont (2007), The earnings announcement premium and trading volume, NBER WP 13090 | V2 | [NBER](https://www.nber.org/papers/w13090) |
| 25 | Gao, Xing & Zhang (2018), Anticipating uncertainty: straddles around earnings announcements, *JFQA* 53(6) 2587–2617 | V1 | [RePEc](https://ideas.repec.org/a/cup/jfinqa/v53y2018i06p2587-2617_00.html) |
| 26 | Hartzmark & Shue (2018), A tough act to follow: contrast effects in financial markets, *J. Finance* 73(4) 1567–1613 | V2 | [NBER w23883](https://www.nber.org/papers/w23883) |
| 27 | Hirshleifer, Lim & Teoh (2009), Driven to distraction…, *J. Finance* 64(5) 2289–2325 | V2 | [RePEc](https://ideas.repec.org/a/bla/jfinan/v64y2009i5p2289-2325.html) |
| 28 | Hong & Stein (1999), A unified theory of underreaction, momentum trading, and overreaction…, *J. Finance* 54(6) 2143–2184 | V2 | [RePEc](https://ideas.repec.org/a/bla/jfinan/v54y1999i6p2143-2184.html) |
| 29 | Jin, Livnat & Zhang (2012), Option prices leading equity prices: do option traders have an information advantage?, *J. Accounting Research* 50(2) 401–432 | V1 | [RePEc](https://ideas.repec.org/a/bla/joares/v50y2012i2p401-432.html) |
| 30 | Johnson & So (2012), The option to stock volume ratio and future returns, *JFE* 106(2) 262–286 | V1 | [EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:106:y:2012:i:2:p:262-286) |
| 31 | Johnson & So (2018), Time will tell: information in the timing of scheduled earnings news, *JFQA* 53(6) 2431–2464 | V2 | [RePEc](https://ideas.repec.org/a/cup/jfinqa/v53y2018i06p2431-2464_00.html) |
| 32 | Kaniel, Liu, Saar & Titman (2012), Individual investor trading and return patterns around earnings announcements, *J. Finance* 67(2) 639–680 | V1 (CEPR version) | [CEPR DP8259](https://cepr.org/publications/dp8259) |
| 33 | La Porta, Lakonishok, Shleifer & Vishny (1997), Good news for value stocks, *J. Finance* 52, 859–874 | V2 | [NBER w5311](https://www.nber.org/papers/w5311) |
| 34 | Lou, Polk & Skouras (2019), A tug of war: overnight versus intraday expected returns, *JFE* 134(1) 192–213 | V2 | [RePEc](https://ideas.repec.org/a/eee/jfinec/v134y2019i1p192-213.html) |
| 35 | Martineau (2022), Rest in peace post-earnings announcement drift, *Critical Finance Review* 11(3–4) 613–646 | V1 | [EconPapers](https://econpapers.repec.org/article/nowjnlcfr/104.00000122.htm) |
| 36 | McLean & Pontiff (2016), Does academic research destroy stock return predictability?, *J. Finance* 71(1) 5–32 — figures quoted from the 2012 working paper only | V1 (2012 draft) | [HEC draft PDF](https://www.hec.ca/finance/Fichier/McLean.pdf) |
| 37 | Mendenhall (2004), Arbitrage risk and post-earnings-announcement drift, *J. Business* 77(4) 875–894 | V2 | [RePEc](https://ideas.repec.org/a/ucp/jnlbus/v77y2004i4p875-894.html) |
| 38 | Mian & Sankaraguruswamy (2012), Investor sentiment and stock market response to earnings news, *Accounting Review* 87(4) 1357–1384 | V2 | [AAA](https://publications.aaahq.org/accounting-review/article-abstract/87/4/1357/3404/Investor-Sentiment-and-Stock-Market-Response-to) |
| 39 | Miller (1977), Risk, uncertainty, and divergence of opinion, *J. Finance* 32(4) 1151–1168 | V2 (bibliography) | [RePEc](https://ideas.repec.org/a/bla/jfinan/v32y1977i4p1151-68.html) |
| 40 | Pan & Poteshman (2006), The information in option volume for future stock prices, *RFS* 19(3) 871–908 | V1 | [EconPapers](https://econpapers.repec.org/RePEc:oup:rfinst:v:19:y:2006:i:3:p:871-908) |
| 41 | Richardson, Teoh & Wysocki (2004), The walk-down to beatable analyst forecasts…, *Contemporary Accounting Research* 21, 885–924 | V2 | [Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1506/KHNW-PJYL-ADUB-0RP6) |
| 42 | Savor & Wilson (2016), Earnings announcements and systematic risk, *J. Finance* 71(1) 83–138 | V1 (2011 draft) | [Wharton draft PDF](https://faculty.wharton.upenn.edu/wp-content/uploads/2012/04/Draft20111215p_edited.pdf) |
| 43 | Shleifer & Vishny (1997), The limits of arbitrage, *J. Finance* 52(1) 35–55 | V2 | [RePEc](https://ideas.repec.org/a/bla/jfinan/v52y1997i1p35-55.html) |
| 44 | Skinner & Sloan (2002), Earnings surprises, growth expectations, and stock returns…, *Review of Accounting Studies* 7, 289–312 | V2 | [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=172060) |
| 45 | So & Wang (2014), News-driven return reversals: liquidity provision ahead of earnings announcements, *JFE* 114(1) 20–35 | V1 | [RePEc](https://ideas.repec.org/a/eee/jfinec/v114y2014i1p20-35.html) |
| 46 | Tetlock, Saar-Tsechansky & Macskassy (2008), More than words…, *J. Finance* 63(3) 1437–1467 | V2 | [RePEc](https://ideas.repec.org/a/bla/jfinan/v63y2008i3p1437-1467.html) |
| 47 | Thomas & Zhang (2008), Overreaction to intra-industry information transfers?, *J. Accounting Research* 46(4) 909–940 | V2 | [RePEc](https://ideas.repec.org/a/bla/joares/v46y2008i4p909-940.html) |
| 48 | Xing, Zhang & Zhao (2010), What does the individual option volatility smirk tell us about future equity returns?, *JFQA* 45, 641–662 | V1 | [Cambridge](https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/what-does-the-individual-option-volatility-smirk-tell-us-about-future-equity-returns/ECFD16BA9ACBDC8D577D1BD866FBEA72) |
