# D002 · Universe industry allowlist · v1 — FROZEN 2026-09-16

> Jacob chose "the §10 draft" on 2026-09-16. It is copied here verbatim from FRAMEWORK v0.1 §10, so a
> later edit to FRAMEWORK cannot move it. Rule 8: the universe is a rule. A change creates `v2`, which
> applies from the next season's screening date and never mid-season.

## Conditions — all must hold on the season's screening date

- US-listed common stock with a market cap of **≥ $2B**
- its **industry**, not its broad sector label, is on the allowlist below
- the **implied move** for the event is **≥ 4%**, taken from the option expiry that straddles the print
- the options are liquid: enough front-expiry open interest, and a spread tight enough to trust the implied move
- the report date **and** session are confirmed from two sources, one of them the company

## Allowlist

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

## ⚠ Still judgment — these must become numbers in D003 before the universe is screened

The allowlist is frozen, but five of its terms are not yet mechanical. Each one is a dial until it gets
a number or a list. **D003 (universe screening rule) sets them all, before any calendar name is looked at.**

1. **The industry taxonomy.** Pick one source (for example, yfinance `industry`) and map every allowed
   industry string to a cluster.
2. **"AI-hosting revenue"** and **"robotics or autonomy is the product"** need a test that can be checked
   against a filing.
3. **"Largest names only"** in healthcare needs a market-cap floor.
4. **"Liquid options"** needs a minimum open interest and a maximum bid-ask spread.
5. **The screening date**, and the implied-move formula with its source.
