"""paper_flatten.py - sell a stray share position in the paper OPTIONS account, once, by hand (Jacob's call).

    python pipeline/paper_flatten.py <SYMBOL> <QTY> <WHY>

Written 2026-10-26 for DPZ: the 2026-10-13 straddle was held past expiry and its shares were assigned (+100,
no ledger holds them; ops/incidents/2026-10-13_DPZ_exit.md). The shares tie up margin that the peak's opens need
(ops/capacity_peak_2026-11.md). Jacob approved one market sell on 2026-10-28.

It refuses unless the account holds exactly +QTY of SYMBOL. It sends one market day order and records the order
and its fill in paper/manual/. It decides nothing and touches no ledger: this is account clean-up, not a trade of
any track. Keys come from APCA_API_KEY_ID / APCA_API_SECRET_KEY (GitHub secrets); they are never printed or stored.
"""
import json
import os
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(__file__))
from common import ET, now_et  # noqa: E402

BASE = "https://paper-api.alpaca.markets/v2"
ROOT = os.path.join(os.path.dirname(__file__), "..")


def headers():
    k, s = os.environ.get("APCA_API_KEY_ID"), os.environ.get("APCA_API_SECRET_KEY")
    if not k or not s:
        raise SystemExit("no APCA_API_KEY_ID / APCA_API_SECRET_KEY")
    return {"APCA-API-KEY-ID": k, "APCA-API-SECRET-KEY": s}


def main(symbol, qty, why):
    symbol, qty = symbol.upper(), int(qty)
    h = headers()
    r = requests.get(f"{BASE}/positions/{symbol}", headers=h, timeout=20)
    held = int(float(r.json().get("qty", 0))) if r.status_code == 200 else 0
    if held != qty:
        raise SystemExit(f"refused: the account holds {held:+d} {symbol}, not +{qty}")
    sent = now_et()
    o = requests.post(f"{BASE}/orders", headers=h, timeout=20, json={
        "symbol": symbol, "qty": str(qty), "side": "sell", "type": "market", "time_in_force": "day",
        "client_order_id": f"flatten-{symbol}-{sent:%Y%m%d%H%M}"})
    if o.status_code not in (200, 201):
        raise SystemExit(f"order refused: HTTP {o.status_code} {o.text[:300]}")
    order = o.json()
    for _ in range(24):  # up to 2 minutes for the fill
        if order.get("status") in ("filled", "canceled", "expired", "rejected"):
            break
        time.sleep(5)
        order = requests.get(f"{BASE}/orders/{order['id']}", headers=h, timeout=20).json()
    rec = {"symbol": symbol, "qty": qty, "why": why, "sent_et": sent.isoformat(timespec="seconds"),
           "order_id": order.get("id"), "status": order.get("status"),
           "filled_qty": order.get("filled_qty"), "filled_avg_price": order.get("filled_avg_price"),
           "filled_at": order.get("filled_at"), "account": "paper options (APCA_API_KEY_ID)"}
    out = os.path.join(ROOT, "paper", "manual", f"flatten_{symbol}_{sent:%Y-%m-%d}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rec, f, indent=1)
        f.write("\n")
    print(json.dumps(rec, indent=1))
    if order.get("status") != "filled":
        raise SystemExit(f"not filled: {order.get('status')}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
