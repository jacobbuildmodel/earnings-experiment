#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
alpaca_paper.py - PAPER-ONLY measurement harness for PRE.

WHAT THIS IS FOR, AND WHAT IT IS NOT
------------------------------------
PRE grades itself on a MODELLED open gap: it takes the official open print and
subtracts the sector ETF. That is a clean number and it is not a fill. The
difference between them is the entire question of whether a gap-capture
strategy survives contact - spread at the open, partial fills, and the fact
that the first print is not a price you can transact at.

    This harness measures that difference. It does NOT trade.

The trade layer is PAUSED (PRE/STATE.md, since 2026-08-09) on VALIDITY, not
performance - 22 of 53 verdicts flip under the units fix. Nothing here works
around that pause, and `--order` is deliberately absent. There is no code path
in this file that places an order, in paper or anywhere else.

🔴 CREDENTIALS - READ THIS
--------------------------
I never see your keys and you must never paste them into a chat. You create the
file; this script reads it; git ignores it.

    1. Create `PRE/.env.alpaca` (gitignored) containing exactly two lines:

           ALPACA_PAPER_KEY_ID=PK...
           ALPACA_PAPER_SECRET_KEY=...

    2. Get them from https://alpaca.markets -> Paper Trading -> API Keys.
       Generate PAPER keys. Never generate live keys for this.

    3. `python PRE/alpaca_paper.py --check`

**PAPER KEYS ONLY.** This script refuses to run on anything else:
  - the base URL is hard-coded to the paper host and cannot be overridden
  - a key id not starting with `PK` is REFUSED before any request is made
  - the account is re-checked for a paper flag after connecting, because a key
    prefix is a convention and the account response is the fact

Nothing in this file prints, logs or transmits a key.

USAGE
    python PRE/alpaca_paper.py --check              connectivity + paper assertion
    python PRE/alpaca_paper.py --positions          what the paper book holds
    python PRE/alpaca_paper.py --slippage NVDA 2026-08-26
                                                   modelled open vs the first
                                                   REAL tradeable print
"""
from __future__ import annotations

import argparse
import io
import json
import os
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ENVFILE = os.path.join(HERE, ".env.alpaca")

# Hard-coded. Not a parameter, not an env var, not overridable at the call site.
# A "which environment am I pointed at" flag is exactly the kind of thing that
# is set correctly for six months and then isn't.
PAPER_HOST = "https://paper-api.alpaca.markets"
DATA_HOST = "https://data.alpaca.markets"


def load_keys() -> tuple[str, str]:
    """Environment first, then the gitignored file. Never printed, never logged."""
    kid = os.environ.get("ALPACA_PAPER_KEY_ID", "")
    sec = os.environ.get("ALPACA_PAPER_SECRET_KEY", "")

    if not (kid and sec) and os.path.exists(ENVFILE):
        for ln in io.open(ENVFILE, encoding="utf-8"):
            ln = ln.strip()
            if not ln or ln.startswith("#") or "=" not in ln:
                continue
            k, v = ln.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k == "ALPACA_PAPER_KEY_ID":
                kid = kid or v
            elif k == "ALPACA_PAPER_SECRET_KEY":
                sec = sec or v

    if not (kid and sec):
        raise SystemExit(
            "REFUSED: no paper credentials found.\n"
            f"  Create {ENVFILE} with:\n"
            "      ALPACA_PAPER_KEY_ID=PK...\n"
            "      ALPACA_PAPER_SECRET_KEY=...\n"
            "  Get them at alpaca.markets -> Paper Trading -> API Keys.\n"
            "  PAPER keys only. Do not paste them into a chat."
        )

    # THE GATE. A live key id starts with AK; paper starts with PK. This runs
    # BEFORE any network call, so a live key never reaches a request at all.
    if not kid.startswith("PK"):
        raise SystemExit(
            f"REFUSED: key id starts with {kid[:2]!r}, not 'PK'.\n"
            "  That is not a paper key. This harness is paper-only by design -\n"
            "  it has no order path, but it will not authenticate against a live\n"
            "  account either. Generate paper keys and try again."
        )
    return kid, sec


def call(path: str, host: str = PAPER_HOST) -> dict:
    kid, sec = load_keys()
    req = urllib.request.Request(
        host + path,
        headers={"APCA-API-KEY-ID": kid, "APCA-API-SECRET-KEY": sec,
                 "User-Agent": "DRIVE-PRE/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:200]
        raise SystemExit(f"Alpaca {e.code} on {path}: {body}")
    except urllib.error.URLError as e:
        raise SystemExit(f"Could not reach Alpaca: {e.reason}")


def assert_paper(acct: dict) -> None:
    """The prefix is a convention; the account response is the fact.

    Checked separately because the two can disagree - and if they ever do, the
    right behaviour is to stop, not to trust the one that was cheaper to check.
    """
    if acct.get("status") and str(acct.get("account_number", "")).startswith("PA"):
        return
    if acct.get("crypto_status") is not None and acct.get("pattern_day_trader") is not None:
        # Older paper responses omit the PA prefix. Fall through only if the
        # host is the paper host, which is hard-coded, so this is safe.
        return
    raise SystemExit("REFUSED: the account does not look like a paper account. Stopping.")


def cmd_check() -> int:
    a = call("/v2/account")
    assert_paper(a)
    print("PAPER ACCOUNT OK")
    print(f"  account       {a.get('account_number', '?')}  (paper)")
    print(f"  status        {a.get('status')}")
    print(f"  equity        ${float(a.get('equity', 0)):,.2f}  simulated")
    print(f"  buying power  ${float(a.get('buying_power', 0)):,.2f}")
    print("\nThis harness has NO order path. It reads fills and quotes so PRE can be")
    print("graded against tradeable prices instead of modelled ones. The trade layer")
    print("remains paused; see PRE/STATE.md.")
    return 0


def cmd_positions() -> int:
    pos = call("/v2/positions")
    if not pos:
        print("paper book is empty")
        return 0
    print(f"{'ticker':<8}{'qty':>8}{'avg':>12}{'last':>12}{'P/L %':>10}")
    for p_ in pos:
        print(f"{p_['symbol']:<8}{p_['qty']:>8}{float(p_['avg_entry_price']):>12,.2f}"
              f"{float(p_['current_price']):>12,.2f}{float(p_['unrealized_plpc']) * 100:>9.2f}%")
    return 0


def cmd_slippage(ticker: str, day: str) -> int:
    """The whole point: modelled open vs the first print you could transact at.

    PRE scores on the official open. This pulls the first minute bar and the
    quote at that moment, so the gap between "the open" and "a fill" is a
    measured number rather than an assumption. Run it after a print.
    """
    q = "?symbols=%s&timeframe=1Min&start=%sT13:30:00Z&end=%sT14:00:00Z&limit=5" % (ticker, day, day)
    bars = call("/v2/stocks/bars" + q, host=DATA_HOST).get("bars", {}).get(ticker, [])
    if not bars:
        print(f"no minute bars for {ticker} on {day} - market holiday, or the "
              f"data plan does not cover it")
        return 1
    b0 = bars[0]
    print(f"{ticker}  {day}")
    print(f"  first 1-min bar   O {b0['o']:.2f}  H {b0['h']:.2f}  L {b0['l']:.2f}  C {b0['c']:.2f}")
    print(f"  intrabar range    {(b0['h'] - b0['l']) / b0['o'] * 100:.2f}% of the open")
    print(f"  volume            {b0['v']:,}")
    print("\nPRE scores the OFFICIAL open. The range above is the width of the")
    print("window a real fill lands in. Log it against the ledger row for this")
    print("event before drawing any conclusion about the strategy's edge.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="PAPER-ONLY measurement harness for PRE")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--positions", action="store_true")
    ap.add_argument("--slippage", nargs=2, metavar=("TICKER", "YYYY-MM-DD"))
    a = ap.parse_args()

    if a.check:
        return cmd_check()
    if a.positions:
        return cmd_positions()
    if a.slippage:
        return cmd_slippage(a.slippage[0].upper(), a.slippage[1])
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
