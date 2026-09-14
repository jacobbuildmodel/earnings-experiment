# External source leads — UNVERIFIED

**Status: leads, not facts.** Collected 2026-09-13 from the external reviews of the retired PRE v1 model,
chiefly a Genspark research dossier. **Nothing here has been probed.** Before any of it touches a
snapshot or a factor: probe it live, record what it actually returns and what it costs, and only then
move it into `FRAMEWORK.md` §8. The Alpha Vantage docs were wrong about five endpoints on the first
probe — assume these are wrong too until shown otherwise.

Only facts about **data sources and methods** were kept. Nothing about which factors predict returns —
that stays fenced off with the rest of PRE v1 (`archive/README.md`).

## Options and implied moves — the hardest family to backfill

| lead | claimed | to verify |
|---|---|---|
| **Alphanume — Earnings Move History** | pre-print straddle-implied move **and** realised move per event; ~3,554 events since 2024; point-in-time; BMO/AMC flag; API on a paid plan | price, redistribution terms, coverage of this universe. ⚠ its realised move is close-based and our outcome is open-based — use its *implied* column only |
| ThetaData | full OPRA history with IV and Greeks; end-of-day bulk files | real plan prices, and how much history each tier includes |
| Databento | $125 of free credits (said to expire after 6 months); ~12 years of OPRA | whether the credits cover a one-off backfill of this universe |
| Polygon ("Massive") | end-of-day options on a basic tier | history depth on that tier |
| MarketData.app | 100 free credits a day; **each option symbol in a chain response costs credits** | whether a strike-filtered ATM pull fits the budget |

## Earnings timing — the field that keeps breaking

| lead | claimed | to verify |
|---|---|---|
| Finnhub earnings calendar | explicit `hour` field (bmo / amc / dmh) | ⚠ free tier said to cover only **one month** of history — usable live, not for backfill |
| Wall Street Horizon | institutional-grade confirmed dates and timing | paid; a trial said to be available via IBKR |
| SEC 8-K Item 2.02 filing timestamps | the authoritative release time | already the method — supports "two sources, one of them the company" |

## Prices, survivorship, filings, transcripts

| lead | claimed |
|---|---|
| EODHD | US price history **including delisted tickers** from 2000 — a fix for survivorship bias |
| Stooq | free bulk daily price files |
| `edgartools` — github.com/dgunning/edgartools | maintained EDGAR client: XBRL statements, 8-K parsing, no key |
| `edgar-parser` — github.com/henrysouchien/edgar-parser | parses Item 2.02 earnings-release exhibits, tables included |
| Hugging Face: `defeatbeta/yahoo-finance-data`, `Bose345/sp500_earnings_transcripts`, `glopardo/sp500-earnings-transcripts` | earnings-call text for tone factors (I4) |

## Literature pointers — read before designing the options (B) factors

- **Dubinsky & Johannes** — the earnings move implied by the options term structure, rather than a single straddle.
- **Alexiou, Goyal, Kostakis & Rompolis (2025, *Review of Finance*)** — short-dated implied-vol curves around earnings.
- **Milian (2023)** — the efficiency of weekly option prices around earnings announcements.
- **Meursault, Liang, Routledge & Scanlon (2023, *JFQA*), "PEAD.txt"** — earnings-call text as a standardised surprise.

None of these has been read for this project.
