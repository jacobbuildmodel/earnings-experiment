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
ids = []
leg = lambda s, side, pi: {"symbol": s, "ratio_qty": "1", "side": side, "position_intent": pi}
ids.append(place({"order_class": "mleg", "qty": "1", "type": "limit", "limit_price": "0.01", "time_in_force": "day",
                  "legs": [leg(C[k], "buy", "buy_to_open"), leg(P[k], "buy", "buy_to_open")]},
                 "long straddle +0.01:"))
for lp in ("-0.01", "0.01"):
    ids.append(place({"order_class": "mleg", "qty": "1", "type": "limit", "limit_price": lp, "time_in_force": "day",
                      "legs": [leg(C[k], "sell", "sell_to_open"), leg(P[k], "sell", "sell_to_open"),
                               leg(C[hi], "buy", "buy_to_open"), leg(P[lo], "buy", "buy_to_open")]},
                     f"iron butterfly {lp}:"))
ids.append(place({"order_class": "mleg", "qty": "1", "type": "limit", "limit_price": "-0.01", "time_in_force": "day",
                  "legs": [leg(C[k], "sell", "sell_to_open"), leg(P[k], "sell", "sell_to_open")]},
                 "naked short straddle -0.01:"))
ids.append(place({"symbol": C[k], "qty": "1", "side": "buy", "type": "limit", "limit_price": "0.01",
                  "time_in_force": "day"}, "single-leg call buy 0.01:"))
ids.append(place({"symbol": C[k], "qty": "1", "side": "buy", "type": "market", "time_in_force": "day"},
                 "single-leg call MARKET (closed):"))
time.sleep(2)
for i in filter(None, ids):
    o = api("GET", f"/orders/{i}")
    print("before cancel", i[:8], o.get("status"), o.get("limit_price"), o.get("filled_qty"))
    print("cancel", i[:8], api("DELETE", f"/orders/{i}"))
time.sleep(2)
print("open orders left:", len([o for o in api("GET", "/orders", params={"status": "open"})]))
print("positions:", [p.get("symbol") for p in api("GET", "/positions")])
