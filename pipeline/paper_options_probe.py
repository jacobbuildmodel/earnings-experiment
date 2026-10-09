"""Paper-account probe for options order mechanics (2026-10-08 ET, market closed). Every order it places is
unfillable or placed while the market is closed, and is cancelled before the script ends."""
import json
import time

from paper import api


def contracts(sym, exp, typ):
    c = api("GET", "/options/contracts", params={"underlying_symbols": sym, "expiration_date": exp, "type": typ,
                                                  "limit": 1000})
    return sorted(c.get("option_contracts") or [], key=lambda x: float(x["strike_price"]))


def place(body, label):
    got = api("POST", "/orders", json=body)
    keep = ("id", "status", "order_class", "limit_price", "type", "time_in_force", "_error", "_body")
    print(label, json.dumps({k: got.get(k) for k in keep}))
    return got.get("id")


exp = "2026-10-16"
calls, puts = contracts("AAPL", exp, "call"), contracts("AAPL", exp, "put")
strikes = [float(c["strike_price"]) for c in calls]
print("AAPL", exp, len(calls), "calls", strikes[:3], "...", strikes[-3:])
k = strikes[len(strikes) // 2]
C = {float(c["strike_price"]): c["symbol"] for c in calls}
P = {float(p["strike_price"]): p["symbol"] for p in puts}
lo, hi = strikes[len(strikes) // 2 - 4], strikes[len(strikes) // 2 + 4]
leg = lambda s, side, pi: {"symbol": s, "ratio_qty": "1", "side": side, "position_intent": pi}


def one(body, label):
    """Place, read back, cancel - one at a time, so no order trips the wash-trade check of the next."""
    i = place(body, label)
    if i:
        time.sleep(1)
        o = api("GET", f"/orders/{i}")
        print("   read back:", o.get("status"), "limit", o.get("limit_price"), "legs",
              [(x.get("side"), x.get("position_intent")) for x in o.get("legs") or []])
        print("   cancel:", api("DELETE", f"/orders/{i}") or "ok")
        time.sleep(1)


fly = [leg(C[k], "sell", "sell_to_open"), leg(P[k], "sell", "sell_to_open"),
       leg(C[hi], "buy", "buy_to_open"), leg(P[lo], "buy", "buy_to_open")]
for lp in ("-0.01", "0.01", "-50", "50"):
    one({"order_class": "mleg", "qty": "1", "type": "limit", "limit_price": lp, "time_in_force": "day", "legs": fly},
        f"iron butterfly K={k} wings {lo}/{hi} limit {lp}:")
one({"order_class": "mleg", "qty": "1", "type": "limit", "limit_price": "-50", "time_in_force": "day",
     "legs": [leg(C[k], "sell", "sell_to_open"), leg(P[k], "sell", "sell_to_open")]}, "naked short straddle -50:")
one({"order_class": "mleg", "qty": "1", "type": "limit", "limit_price": "50", "time_in_force": "day",
     "legs": [leg(C[k], "sell", "sell_to_open"), leg(P[k], "sell", "sell_to_open")]}, "naked short straddle 50:")
one({"order_class": "mleg", "qty": "1", "type": "limit", "limit_price": "-0.01", "time_in_force": "day",
     "legs": [leg(C[k], "buy", "buy_to_open"), leg(P[k], "buy", "buy_to_open")]}, "long straddle -0.01:")
ids = []
time.sleep(2)
for i in filter(None, ids):
    o = api("GET", f"/orders/{i}")
    print("before cancel", i[:8], o.get("status"), o.get("limit_price"), o.get("filled_qty"))
    print("cancel", i[:8], api("DELETE", f"/orders/{i}"))
time.sleep(2)
print("open orders left:", len([o for o in api("GET", "/orders", params={"status": "open"})]))
print("positions:", [p.get("symbol") for p in api("GET", "/positions")])
