# Cloud network probe — October 2026

Run time: 2026-10-03 02:28 UTC / 2026-10-02 22:28 ET, from a claude.ai cloud session
(`ops/cloud_session_prompt.md`, Step 0). Python `requests`, 20 s timeout, headers from
`pipeline/common.py` (`SEC_HEADERS` for SEC, `WEB_HEADERS` otherwise). No pipeline stage ran.

| # | target | result |
|---|---|---|
| 1 | SEC EDGAR `data.sec.gov/submissions/CIK0000320193.json` | **BLOCKED** — `ProxyError: Tunnel connection failed: 403 Forbidden` |
| 2 | Nasdaq `api.nasdaq.com/api/calendar/earnings?date=2026-10-06` | **BLOCKED** — same proxy 403 |
| 3 | NYSE `www.nyse.com/markets/hours-calendars` | **BLOCKED** — same proxy 403 |
| 4 | yfinance `Ticker("SPY").history(period="5d")` | **BLOCKED** — `curl: (7) CONNECT tunnel failed, response 403` |
| 5 | DoltHub `www.dolthub.com/api/v1alpha1/post-no-preference/options/master?q=select+1` | **BLOCKED** — same proxy 403 |

The session proxy's own status page logs each one as `connect_rejected`: "gateway answered 403 to
CONNECT (policy denial)". PyPI and GitHub work (packages installed, git push works).

## Conclusion

Unchanged since 2026-09-17 (`ops/cloud_probe.md`): the cloud environment's network policy blocks every
market-data host. To unblock, in claude.ai/code open the environment menu in the session title bar →
Edit → **Network access: Full**, or Custom with these allowed domains added (keep the package-manager
defaults): `data.sec.gov`, `www.sec.gov`, `api.nasdaq.com`, `www.nyse.com`, `query1.finance.yahoo.com`,
`query2.finance.yahoo.com`, `fc.yahoo.com`, `www.dolthub.com`.

Consequence for this session: T1 and T3 (no network) and the no-network part of T2 were done. T2's
off-season print count and T4 (D010 exploration batch 2, data needed after its freeze) were not.
