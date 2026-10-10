"""Paper options, D011 v2: the LONG earnings straddle on a SECOND Alpaca paper account. Code only, no AI.

    python pipeline/paper_long.py sync [--commit] [--exits-only]
    python pipeline/paper_long.py check          # the second account's options level and equity

Rules: registry/D011_paper_options_v2.md. Every rule of v1 (pipeline/paper_options.py, frozen and NOT edited)
applies unchanged; this file only points v1's code at another structure, account and ledger:
- structure L: buy the gate's ATM call and put (v1's legs_for already builds it); same events, size, entry, exit,
  retries, sign guard and failure labels as v1's butterfly, so the two are paired event by event
- account: APCA_L_API_KEY_ID / APCA_L_API_SECRET_KEY (one account cannot hold both sides of the same contracts)
- ledger: paper/long_ledger.json
- only gates whose snapshot session is on or after START count; earlier gates are not this track's events
- held past expiry: the straddle is worth |S - K| on the expiry close, so the close books a credit of |S - K|
Without the two secrets it prints "not configured" and does nothing.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paper_options as po  # noqa: E402
from common import ROOT  # noqa: E402

LEDGER = os.path.join(ROOT, "paper", "long_ledger.json")
START = "2026-10-12"
KEY_ID, SECRET = "APCA_L_API_KEY_ID", "APCA_L_API_SECRET_KEY"


def configured():
    return bool(os.environ.get(KEY_ID) and os.environ.get(SECRET))


def headers():
    return {"APCA-API-KEY-ID": os.environ[KEY_ID], "APCA-API-SECRET-KEY": os.environ[SECRET]}


def straddle_close_at_expiry(s, k, lo, hi):
    """Net cash per unit to close a long straddle at expiry: + paid, - received. We receive |S - K|."""
    return -abs(s - k)


def load_ledger():
    if os.path.exists(LEDGER):
        import json
        return json.load(open(LEDGER, encoding="utf-8"))
    return {"rule": "D011_paper_options_v2 (long straddle, second account)", "structures": {"L": "long straddle"},
            "start": START, "trades": {}}


def configure(set_=setattr):
    """Point v1's code at structure L, the second account and its own ledger."""
    gates, commit = po.live_gates, po.commit_ledger
    set_(po, "headers", headers)
    set_(po, "LEDGER", LEDGER)
    set_(po, "STRUCTURES", "L")
    set_(po, "fly_payoff", straddle_close_at_expiry)
    set_(po, "load_ledger", load_ledger)
    set_(po, "live_gates", lambda: [x for x in gates() if (x[1].get("snapshot_session") or "") >= START])
    set_(po, "commit_ledger", lambda msg: commit(msg.replace("Paper options ledger", "Paper LONG straddle ledger")
                                                 .replace("D011)", "D011 v2)")))


def check():
    code, a = po.call("GET", "/account")
    keep = ("status", "equity", "options_approved_level", "options_trading_level", "options_buying_power")
    print(f"second paper account: HTTP {code}", {k: a.get(k) for k in keep})


if __name__ == "__main__":
    a = sys.argv[1:]
    if not configured():
        print(f"long straddle track not configured: no {KEY_ID} / {SECRET} - nothing done")
        sys.exit(0)
    configure()
    if a and a[0] == "sync":
        sys.exit(po.sync("--commit" in a, "--exits-only" in a))
    elif a and a[0] == "check":
        check()
    else:
        raise SystemExit(__doc__)
