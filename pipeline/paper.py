"""Paper trading on Alpaca (RESEARCH_PLAN RQ6): the premium-harvest strategy with real order mechanics.

    python pipeline/paper.py check          # account status (no orders)
    python pipeline/paper.py sync [--commit]  # submit due orders, record fills, write paper/ledger.json

The strategy traded here is the base graduate (RESEARCH_PLAN §2): buy EVERY frozen PASS event (T0) at the
entry open with a market-on-open order, sell it at the exit-A open. T1/T2 are not traded separately; the
ledger carries their frozen decisions, so each track's paper P&L is the subset it would have bought.

Rules, all mechanical:
- only events frozen BEFORE their entry open (manifest.json exists, status PASS) - rule 1
- sizing: notional = equity x RISK_PER_EVENT / implied move, capped at equity x MAX_POSITION; whole shares
- orders are market DAY orders submitted while the market is CLOSED (16:00 -> 09:25 ET); Alpaca queues
  them and executes them at the next open. NOT "opg": the paper simulator expired NKE's market-on-open buy
  unfilled at 09:30:37 ET on 2026-10-01 (status expired, filled_qty 0) - it does not fill auction orders.
  Real money would use a true opening-auction order; the paper fill is compared with the official open
  (D008 §3), and the difference is disclosed
- idempotent: client_order_id = <season>-<TICKER>-<date>-<buy|sell>; an existing id is never resubmitted
- every fill is compared later with the official open (grade.py) - the slippage test of D008 §3
Keys come from APCA_API_KEY_ID / APCA_API_SECRET_KEY (GitHub secrets); they are never printed or stored.
"""
import datetime
import glob
import json
import math
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ET, ROOT, now_et, write_json  # noqa: E402
from sessions import is_session, shift  # noqa: E402

BASE = "https://paper-api.alpaca.markets/v2"
LEDGER = os.path.join(ROOT, "paper", "ledger.json")
RISK_PER_EVENT = 0.005   # 0.5% of equity at risk per event, where "risk" = one implied move
MAX_POSITION = 0.10      # never more than 10% of equity in one name
OPG_OPEN, OPG_CLOSE = datetime.time(16, 0), datetime.time(9, 25)  # the queue-for-the-open window


def headers():
    k, s = os.environ.get("APCA_API_KEY_ID"), os.environ.get("APCA_API_SECRET_KEY")
    if not k or not s:
        raise SystemExit("no APCA_API_KEY_ID / APCA_API_SECRET_KEY - paper trading is not configured")
    return {"APCA-API-KEY-ID": k, "APCA-API-SECRET-KEY": s}


def api(method, path, **kw):
    r = requests.request(method, BASE + path, headers=headers(), timeout=30, **kw)
    if r.status_code >= 400:
        return {"_error": r.status_code, "_body": r.text[:300]}
    return r.json() if r.text else {}


def opg_window(now):
    t = now.time()
    return t >= OPG_OPEN or t < OPG_CLOSE or not is_session(now.date())


def next_open_session(now):
    """The session whose opening auction an order placed now would join."""
    d = now.date()
    if now.time() >= OPG_OPEN or not is_session(d):
        return shift(d, 1)
    return d


def load_ledger():
    if os.path.exists(LEDGER):
        return json.load(open(LEDGER, encoding="utf-8"))
    return {"strategy": "T0 premium harvest: buy every frozen PASS event at the entry open, sell at the exit-A open",
            "sizing": {"risk_per_event": RISK_PER_EVENT, "max_position": MAX_POSITION}, "trades": {}}


def frozen_pass_events():
    out = []
    for m in sorted(glob.glob(os.path.join(ROOT, "events", "*", "*", "manifest.json"))):
        man = json.load(open(m, encoding="utf-8"))
        if man.get("status") != "PASS":
            continue
        d = os.path.dirname(m)
        gate = json.load(open(os.path.join(d, "gate.json"), encoding="utf-8"))
        dec = json.load(open(os.path.join(d, "decision.json"), encoding="utf-8"))
        # rule 1: the freeze must predate the entry open
        if datetime.datetime.fromisoformat(man["frozen_et"]) >= datetime.datetime.fromisoformat(man["entry_open_et"]):
            continue
        out.append((os.path.basename(os.path.dirname(d)), gate, dec, man))
    return out


def check():
    a = api("GET", "/account")
    if "_error" in a:
        raise SystemExit(f"Alpaca account: HTTP {a['_error']} {a['_body']}")
    print(f"paper account {a.get('status')} · equity {a.get('equity')} · buying power {a.get('buying_power')} "
          f"· trading blocked {a.get('trading_blocked')}")
    clock = api("GET", "/clock")
    print(f"market clock: open={clock.get('is_open')} next_open={clock.get('next_open')}")


def order_status(tr, side):
    o = tr.get(side)
    if not o or o.get("status") in ("filled", "canceled", "expired", "rejected"):
        return
    got = api("GET", "/orders:by_client_order_id", params={"client_order_id": o["client_order_id"]})
    if "_error" not in got:
        o.update(status=got.get("status"), filled_qty=got.get("filled_qty"),
                 filled_avg_price=got.get("filled_avg_price"), filled_at=got.get("filled_at"))


def submit(tr, side, symbol, qty, cid):
    body = {"symbol": symbol, "qty": str(qty), "side": side, "type": "market", "time_in_force": "day",
            "client_order_id": cid}
    got = api("POST", "/orders", json=body)
    tr[side] = {"client_order_id": cid, "qty": qty, "submitted_et": now_et().isoformat(),
                "status": got.get("status") if "_error" not in got else "rejected",
                "error": None if "_error" not in got else f"HTTP {got['_error']} {got['_body']}"}
    print(f"{side} {qty} {symbol} day (queued for the open) -> {tr[side]['status']}{' ' + tr[side]['error'] if tr[side]['error'] else ''}")


FAILED = ("expired", "rejected", "canceled")


def official_open(symbol, session):
    """The official daily Open of a past session (yfinance, auto_adjust=False - the price grade.py uses)."""
    import yfinance as yf
    d = datetime.date.fromisoformat(session)
    h = yf.Ticker(symbol).history(start=session, end=(d + datetime.timedelta(days=5)).isoformat(),
                                  auto_adjust=False).tz_convert(ET)
    row = h[h.index.date == d]
    return float(row["Open"].iloc[0]) if len(row) else None


def after_open(session, now):
    """True once the session's opening print is in (a few minutes after 09:30 ET)."""
    return now >= datetime.datetime.combine(datetime.date.fromisoformat(session), datetime.time(9, 35), ET)


def simulate(tr, now):
    """Jacob, 2026-10-02: an order that fails for a platform reason is booked as executed at the official
    open of its session, labelled simulated. Simulated fills never enter the execution test (D008 §3)."""
    buy, sell = tr.get("buy") or {}, tr.get("sell") or {}
    sim = tr.setdefault("simulated", {})
    if buy.get("status") in FAILED and "buy" not in sim and after_open(tr["entry_session"], now):
        px = official_open(tr["ticker"], tr["entry_session"])
        if px:
            sim["buy"] = {"price": px, "qty": buy.get("qty"), "reason": f"paper order {buy.get('status')} unfilled",
                          "source": "yfinance daily Open (official open), auto_adjust=False"}
    holding = buy.get("status") == "filled" or "buy" in sim
    sell_failed = sell.get("status") in FAILED or ("buy" in sim and not sell)  # no real position to sell
    if holding and sell_failed and "sell" not in sim and after_open(tr["exit_session"], now):
        px = official_open(tr["ticker"], tr["exit_session"])
        if px:
            sim["sell"] = {"price": px, "qty": buy.get("filled_qty") if buy.get("status") == "filled" else buy.get("qty"),
                           "reason": "no real position (buy simulated)" if "buy" in sim else f"paper order {sell.get('status')}",
                           "source": "yfinance daily Open (official open), auto_adjust=False"}
    if not sim:
        tr.pop("simulated")
    # P&L once both legs exist, real or simulated
    bp = (sim.get("buy") or {}).get("price") or (float(buy["filled_avg_price"]) if buy.get("filled_avg_price") else None)
    sp = (sim.get("sell") or {}).get("price") or (float(sell["filled_avg_price"]) if sell.get("filled_avg_price") else None)
    if bp and sp:
        qty = float((sim.get("buy") or {}).get("qty") or buy.get("filled_qty") or 0)
        tr["result"] = {"entry_price": bp, "exit_price": sp, "return": sp / bp - 1, "pnl": round((sp - bp) * qty, 2),
                        "simulated_legs": sorted(sim)}


def sync(do_commit=False):
    now = now_et()
    led = load_ledger()
    trades = led["trades"]
    # 1. refresh every open order's status (fills are recorded whenever this runs)
    for tr in trades.values():
        order_status(tr, "buy")
        order_status(tr, "sell")
        if "ticker" in tr and "entry_session" in tr:
            simulate(tr, now)
    acct = api("GET", "/account")
    equity = float(acct.get("equity") or 0) if "_error" not in acct else 0.0
    target = next_open_session(now)
    if not opg_window(now):
        print(f"{now:%H:%M} ET: the market is open - orders are only queued while it is closed "
              "(16:00-09:25 ET); statuses refreshed only")
    elif not equity:
        print(f"no account equity readable ({acct.get('_error')}) - nothing submitted")
    else:
        # 2. entries: frozen PASS events whose entry session is the next open
        for season, gate, dec, man in frozen_pass_events():
            key = f"{season}-{gate['ticker']}-{gate['report_date']}"
            if gate["timing"]["entry"]["session"] != target.isoformat() or key in trades:
                continue
            im = (gate.get("options") or {}).get("implied_move")
            spot = (gate.get("options") or {}).get("spot")
            if not im or not spot:
                trades[key] = {"skipped": "no implied move or spot in gate.json"}
                continue
            notional = min(equity * RISK_PER_EVENT / im, equity * MAX_POSITION)
            qty = math.floor(notional / spot)
            tr = trades[key] = {"season": season, "ticker": gate["ticker"], "report_date": gate["report_date"],
                                "entry_session": gate["timing"]["entry"]["session"],
                                "exit_session": gate["timing"]["exit_A"]["session"], "implied_move": im,
                                "spot_at_snapshot": spot, "notional_target": round(notional, 2), "equity": equity,
                                "t1": (dec.get("t1") or {}).get("decision"), "t2": (dec.get("t2") or {}).get("decision"),
                                "t2_confidence": (dec.get("t2") or {}).get("confidence")}
            if qty < 1:
                tr["skipped"] = "position rounds to zero shares"
                continue
            submit(tr, "buy", gate["ticker"], qty, f"{key}-buy")
        # 3. exits: filled positions whose exit-A session is the next open
        for key, tr in trades.items():
            b = tr.get("buy") or {}
            if tr.get("exit_session") == target.isoformat() and b.get("status") == "filled" and "sell" not in tr:
                submit(tr, "sell", tr["ticker"], int(float(b["filled_qty"])), f"{key}-sell")
    led["updated_et"] = now.isoformat()
    write_json(LEDGER, led)
    print(f"ledger: {len(trades)} trade(s); next open {target}")
    if do_commit:
        from due import commit
        commit([LEDGER], f"Paper ledger {now:%Y-%m-%d %H:%M} ET (Alpaca paper, code)")


def orders():
    """Read-only: the account's recent orders with every status field (diagnosis)."""
    got = api("GET", "/orders", params={"status": "all", "limit": 20, "direction": "desc"})
    if isinstance(got, dict) and "_error" in got:
        raise SystemExit(f"orders: HTTP {got['_error']} {got['_body']}")
    keep = ("client_order_id", "symbol", "side", "qty", "type", "time_in_force", "status", "submitted_at",
            "updated_at", "expired_at", "canceled_at", "failed_at", "filled_at", "filled_qty", "filled_avg_price",
            "extended_hours", "order_class")
    for o in got:
        print(json.dumps({k: o.get(k) for k in keep}))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "orders":
        orders()
    elif a and a[0] == "check":
        check()
    elif a and a[0] == "sync":
        sync("--commit" in a)
    else:
        raise SystemExit(__doc__)
