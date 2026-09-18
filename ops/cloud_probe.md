# Cloud readiness probe

Run time: 2026-09-18 01:28:09 UTC / 2026-09-17 21:28:09 ET

One-off infrastructure probe, re-run to confirm the earlier result still holds. No pipeline stage
was run and no registry/universe/events/archive file was touched.

| # | Step | Result |
|---|------|--------|
| 1a | `python --version` | OK — Python 3.11.15 |
| 1b | `git remote -v` | OK — `origin` -> `https://github.com/jacobbuildmodel/earnings-experiment` (fetch+push). No `github`/`local` remotes configured in this environment. |
| 1c | `git branch --show-current` | OK — `claude/peaceful-franklin-58zxnd` |
| 1d | `git log --oneline -1` | OK — `ae28d2d Cloud readiness probe` (this branch is already even with `origin/main`) |
| 2 | `pip install -r requirements.txt` | OK — installed/confirmed yfinance 1.4.1, pandas 3.0.2, numpy 2.4.4, requests 2.34.2 and dependencies. Pre-existing `requests` 2.33.1 was upgraded to 2.34.2 to satisfy the pin. |
| 3 | `python check.py` | PASS — 0 warnings (7 core files present, archive/registry/events hashes match, working tree clean, US Eastern clock read OK, yfinance importable) |
| 4a | SEC EDGAR `data.sec.gov/submissions/CIK0000320193.json` (SEC_HEADERS) | FAIL — `ProxyError: Tunnel connection failed: 403 Forbidden` |
| 4b | Nasdaq `api.nasdaq.com/api/calendar/earnings?date=2026-09-23` (WEB_HEADERS) | FAIL — `ProxyError: Tunnel connection failed: 403 Forbidden` |
| 4c | NYSE `www.nyse.com/markets/hours-calendars` (WEB_HEADERS) | FAIL — `ProxyError: Tunnel connection failed: 403 Forbidden` |
| 4d | yfinance `SPY.history(period='5d')` | FAIL — `curl: (7) CONNECT tunnel failed, response 403` |
| 4d | yfinance `AAPL.options[:3]` | FAIL — same proxy 403 |
| 4d | yfinance `option_chain(...).calls` row count | SKIPPED — no expiry returned by the prior failed call |

## Conclusion

Second run, same day, confirms the first: `git`/GitHub connectivity and Python/pip installs work
from this environment, but all four outbound market-data probes (SEC EDGAR, Nasdaq, NYSE,
yfinance/Yahoo) are still blocked at the outbound proxy layer with an identical `403 Forbidden`
before any request reaches the target host. This is not a flake — it reproduced exactly on a
second, independent invocation. **Scheduled cloud runs still cannot fetch market data from this
environment as configured.** The domains used by `pipeline/common.py` (SEC EDGAR, Nasdaq, NYSE,
Yahoo Finance / yfinance) need to be added to the environment's network egress allowlist before
per-event runs relying on `s1_screen.py`, `factors.py`, `s2_gate.py`, or `freeze.py` can run
unattended here. Git push to GitHub is unaffected by this proxy policy (see below).
