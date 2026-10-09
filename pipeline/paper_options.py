"""Paper options (D011): the earnings straddle with real order mechanics on Alpaca paper. Code only, no AI.

    python pipeline/paper_options.py sync [--commit]         # submit due orders, record fills, write the ledger
    python pipeline/paper_options.py dry TICKER EXPIRY STRIKE  # build both orders from live quotes, submit nothing

One structure per event, on the gate's expiry and ATM strike (registry/D011_paper_options_v1.md):
  PX-F  short iron butterfly: sell the call and the put, buy a call and a put about two straddle prices away.
        The paper account refuses uncovered short calls ("account not eligible to trade uncovered option
        contracts", probed 2026-10-08), so SH-X's exact naked short straddle cannot be placed. The wings cap it.
  The long straddle (structure L, kept in legs_for) is NOT traded: one account nets positions by contract, and
  Alpaca refused a sell on contracts with an opposite open order ("potential wash trade detected"). It needs a
  second paper account.

Rules, all mechanical:
- events: every gate.json of a live season (not the pilot) that SH-X takes (both ATM bids), committed to main,
  whose snapshot session is today, with expiry on or after the reaction session
- entry: on the snapshot session, while the market is open and before 15:50 ET; exit: on the reaction session,
  the first run at or after 14:30 ET (late runs close as soon as they can, flagged)
- orders: one multi-leg DAY limit order per structure at the natural price (the far side of every leg) from
  Alpaca's quotes at that moment; an order still open 15 minutes later is cancelled and resent once at a
  fresh natural. Debits are positive limits and credits negative
- size: n = max(1, floor(equity x 0.5% / (100 x the gate's straddle mid)))
- fills are read leg by leg, so the net price never depends on the sign convention
- a leg that fails for a platform reason (expired or cancelled unfilled) is booked at the natural recorded when
  it was sent, labelled simulated (Jacob, 2026-10-02). Simulated legs never enter the execution comparison.
  A rejection for buying power is NOT simulated: it is the account's real capacity, recorded as such
- idempotent: client_order_id = <season>-<TICKER>-<date>-<L|F>-<open|close>[-r1]; an id is never resent
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
from paper import api, headers  # noqa: E402

LEDGER = os.path.join(ROOT, "paper", "options_ledger.json")
DATA = "https://data.alpaca.markets/v1beta1/options/snapshots"
RISK_PER_EVENT = 0.005
WING_MULT = 2.0
ENTRY_CUTOFF = datetime.time(15, 55)
EXIT_FROM = datetime.time(14, 30)
CLOSE_BY = datetime.time(15, 55)
RETRY_AFTER_MIN = 15
FAILED = ("expired", "canceled", "rejected")
STRUCTURES = "F"
SEASONS_EXCLUDED = ("pilot",)


# ---------------------------------------------------------------- market data
def chain(ticker, expiry):
    """{strike: {"call": symbol, "put": symbol}} for one expiry, from Alpaca's contract list."""
    out, token = {}, None
    while True:
        params = {"underlying_symbols": ticker.replace("-", "."), "expiration_date": expiry, "limit": 1000}
        if token:
            params["page_token"] = token
        got = api("GET", "/options/contracts", params=params)
        if "_error" in got:
            return None
        for c in got.get("option_contracts") or []:
            if c.get("tradable"):
                out.setdefault(float(c["strike_price"]), {})[c["type"]] = c["symbol"]
        token = got.get("next_page_token")
        if not token:
            return out


def quotes(symbols):
    """{symbol: {"bid", "ask", "t"}} from the indicative feed (the paper account's free feed)."""
    r = requests.get(DATA, params={"symbols": ",".join(symbols), "feed": "indicative"}, headers=headers(), timeout=30)
    if r.status_code != 200:
        return {}
    out = {}
    for s, snap in (r.json().get("snapshots") or {}).items():
        q = snap.get("latestQuote") or {}
        out[s] = {"bid": q.get("bp"), "ask": q.get("ap"), "t": q.get("t")}
    return out


def cents_up(x):
    return math.ceil(round(x * 100, 6)) / 100


def cents_down(x):
    return math.floor(round(x * 100, 6)) / 100


# ---------------------------------------------------------------- structures
def legs_for(structure, ch, k, wings, opening):
    """The legs of one structure, as (symbol, side, intent). Closing reverses every side."""
    if structure == "L":
        base = [(ch[k]["call"], "buy"), (ch[k]["put"], "buy")]
    else:
        lo, hi = wings
        base = [(ch[k]["call"], "sell"), (ch[k]["put"], "sell"), (ch[hi]["call"], "buy"), (ch[lo]["put"], "buy")]
    out = []
    for sym, side in base:
        if not opening:
            side = "sell" if side == "buy" else "buy"
        intent = f"{side}_to_{'open' if opening else 'close'}"
        out.append({"symbol": sym, "ratio_qty": "1", "side": side, "position_intent": intent})
    return out


def natural(legs, q):
    """Net cash per unit at the far side of every leg: + = we pay (debit), - = we receive (credit).
    None if any needed quote is missing, or a leg we sell has no bid."""
    net = 0.0
    for lg in legs:
        qq = q.get(lg["symbol"]) or {}
        if lg["side"] == "buy":
            if not qq.get("ask"):
                return None
            net += qq["ask"]
        else:
            if qq.get("bid") is None or (lg["position_intent"].endswith("open") and qq["bid"] <= 0):
                return None
            net -= qq["bid"]
    return net


def limit_of(net):
    """Marketable limit in Alpaca's convention: a debit is positive, a credit negative; rounded to the cent
    on the side that keeps it marketable."""
    return cents_up(net) if net >= 0 else -cents_down(-net)


def pick_wings(ch, k, straddle_mid):
    w = WING_MULT * straddle_mid
    hi = [s for s in ch if s >= k + w and "call" in ch[s]]
    lo = [s for s in ch if s <= k - w and "put" in ch[s]]
    return (max(lo), min(hi)) if hi and lo else None


# ---------------------------------------------------------------- orders
def send(tr, which, legs, q, cid):
    net = natural(legs, q)
    rec = {"client_order_id": cid, "sent_et": now_et().isoformat(), "natural": net,
           "quotes": {lg["symbol"]: q.get(lg["symbol"]) for lg in legs}}
    if net is None:
        rec.update(status="not_sent", error="a needed quote is missing or a sold leg has no bid")
    else:
        body = {"order_class": "mleg", "qty": str(tr["n"]), "type": "limit", "limit_price": f"{limit_of(net):.2f}",
                "time_in_force": "day", "client_order_id": cid, "legs": legs}
        got = api("POST", "/orders", json=body)
        rec.update(limit_price=body["limit_price"], id=got.get("id"),
                   status=got.get("status") if "_error" not in got else "rejected",
                   error=None if "_error" not in got else f"HTTP {got['_error']} {got['_body']}")
    tr.setdefault("orders", {}).setdefault(which, []).append(rec)
    print(f"{tr['key']} {which}: n={tr['n']} natural {net} -> {rec['status']}{' ' + rec['error'] if rec.get('error') else ''}")
    return rec


def refresh(rec):
    if not rec.get("id") or rec.get("status") in FAILED + ("filled",):
        return
    o = api("GET", f"/orders/{rec['id']}")
    if "_error" in o:
        return
    rec["status"] = o.get("status")
    rec["filled_at"] = o.get("filled_at")
    rec["legs_filled"] = [{"symbol": lg.get("symbol"), "side": lg.get("side"), "qty": lg.get("filled_qty"),
                           "price": lg.get("filled_avg_price")} for lg in o.get("legs") or []]


def fill_net(rec):
    """Net cash per unit actually traded, from the legs: + paid, - received."""
    if rec.get("status") != "filled" or not rec.get("legs_filled"):
        return None
    net = 0.0
    for lg in rec["legs_filled"]:
        if lg["price"] is None:
            return None
        net += float(lg["price"]) * (1 if lg["side"] == "buy" else -1)
    return net


def capacity_rejection(rec):
    return rec.get("status") == "rejected" and "buying power" in (rec.get("error") or "").lower()


def leg_state(tr, which):
    """'filled', 'open', 'failed', 'capacity' or None for the opening or closing order chain."""
    recs = (tr.get("orders") or {}).get(which) or []
    if not recs:
        return None
    last = recs[-1]
    if last["status"] == "filled":
        return "filled"
    if capacity_rejection(last):
        return "capacity"
    if last["status"] in FAILED + ("not_sent", "simulated"):
        return "failed"
    return "open"


def maybe_retry(tr, which, legs_fn, now):
    """An order still open RETRY_AFTER_MIN after it was sent is cancelled and resent once at a fresh natural."""
    recs = tr["orders"][which]
    last = recs[-1]
    if len(recs) > 1 or last.get("status") in FAILED + ("filled", "not_sent") or not last.get("id"):
        return
    age = (now - datetime.datetime.fromisoformat(last["sent_et"])).total_seconds() / 60
    if age < RETRY_AFTER_MIN or now.time() >= CLOSE_BY:
        return
    api("DELETE", f"/orders/{last['id']}")
    refresh(last)
    if last.get("status") == "filled":
        return
    legs = legs_fn()
    send(tr, which, legs, quotes([lg["symbol"] for lg in legs]), last["client_order_id"] + "-r1")


# ---------------------------------------------------------------- events
def live_gates(today):
    out = []
    for gp in sorted(glob.glob(os.path.join(ROOT, "events", "*", "*", "gate.json"))):
        season = os.path.basename(os.path.dirname(os.path.dirname(gp)))
        if season in SEASONS_EXCLUDED:
            continue
        g = json.load(open(gp, encoding="utf-8"))
        o = g.get("options") or {}
        c, p = o.get("call") or {}, o.get("put") or {}
        if g.get("dry") or g.get("snapshot_session") != today:
            continue
        if not (o.get("expiry") and o.get("strike") and o.get("spot") and c.get("bid") is not None
                and p.get("bid") is not None and c.get("ask") and p.get("ask")):
            continue
        out.append((season, g))
    return out


def open_event(trades, season, g, equity, now):
    o = g["options"]
    base = f"{season}-{g['ticker']}-{g['report_date']}"
    mid = (o["call"]["bid"] + o["call"]["ask"] + o["put"]["bid"] + o["put"]["ask"]) / 2
    n = max(1, math.floor(equity * RISK_PER_EVENT / (100 * mid)))
    common = {"season": season, "ticker": g["ticker"], "report_date": g["report_date"], "session": g["session"],
              "snapshot_session": g["snapshot_session"], "reaction_session": g["timing"]["reaction_day"],
              "expiry": o["expiry"], "strike": o["strike"], "spot_at_gate": o["spot"], "gate_status": g.get("status"),
              "gate_captured_et": g.get("captured_et"), "gate_straddle_mid": mid,
              "gate_natural_long": o["call"]["ask"] + o["put"]["ask"], "gate_natural_short": o["call"]["bid"] + o["put"]["bid"],
              "n": n, "equity": equity}
    if o["expiry"] < g["timing"]["reaction_day"]:
        for s in STRUCTURES:
            trades[f"{base}-{s}"] = dict(common, key=f"{base}-{s}", structure=s, skipped="expiry_before_reaction")
        return
    ch = chain(g["ticker"], o["expiry"])
    k = float(o["strike"])
    for s in STRUCTURES:
        key = f"{base}-{s}"
        tr = trades[key] = dict(common, key=key, structure=s)
        if not ch or k not in ch or "call" not in ch[k] or "put" not in ch[k]:
            tr["skipped"] = "contract_not_listed_at_alpaca"
            continue
        if s == "F":
            wings = pick_wings(ch, k, mid)
            if not wings:
                tr["skipped"] = "no_wing_strike"
                continue
            tr["wings"] = list(wings)
        legs = legs_for(s, ch, k, tr.get("wings"), True)
        tr["legs"] = legs
        send(tr, "open", legs, quotes([lg["symbol"] for lg in legs]), f"{key}-open")


def close_legs(tr):
    return [dict(lg, side="sell" if lg["side"] == "buy" else "buy",
                 position_intent=("sell" if lg["side"] == "buy" else "buy") + "_to_close") for lg in tr["legs"]]


def settle(tr):
    """Result once the opening and closing nets exist, real or simulated. Per unit, + = profit."""
    sim = {}
    nets = {}
    for which in ("open", "close"):
        recs = (tr.get("orders") or {}).get(which) or []
        if not recs:
            return
        st = leg_state(tr, which)
        if st == "filled":
            nets[which] = fill_net(recs[-1])
        elif st == "failed":
            nat = next((r["natural"] for r in reversed(recs) if r.get("natural") is not None), None)
            if nat is None:
                return
            nets[which] = nat
            sim[which] = f"order {recs[-1]['status']}; booked at the natural recorded when sent"
        else:
            return
        if nets[which] is None:
            return
    pnl_unit = -(nets["open"] + nets["close"])
    tr["result"] = {"open_net": nets["open"], "close_net": nets["close"], "pnl_per_unit": pnl_unit,
                    "pnl": round(pnl_unit * 100 * tr["n"], 2), "pnl_on_spot": pnl_unit / tr["spot_at_gate"],
                    "simulated_legs": sorted(sim), "simulated_why": sim or None}
    if "open" not in sim:
        o = tr["orders"]["open"][-1]
        tr["result"]["entry_vs_alpaca_natural"] = nets["open"] - o["natural"] if o.get("natural") is not None else None
        if tr["structure"] == "L":
            tr["result"]["entry_vs_gate_natural"] = nets["open"] - tr["gate_natural_long"]


# ---------------------------------------------------------------- the run
def load_ledger():
    if os.path.exists(LEDGER):
        return json.load(open(LEDGER, encoding="utf-8"))
    return {"rule": "D011_paper_options_v1", "structures": {"F": "short iron butterfly"},
            "trades": {}}


def sync(do_commit=False):
    now = now_et()
    today = now.date().isoformat()
    led = load_ledger()
    trades = led["trades"]
    before = json.dumps(trades, sort_keys=True)
    for tr in trades.values():
        for recs in (tr.get("orders") or {}).values():
            for r in recs:
                refresh(r)
    clock = api("GET", "/clock")
    acct = api("GET", "/account")
    equity = float(acct.get("equity") or 0) if "_error" not in acct else 0.0
    if not clock.get("is_open"):
        print(f"{now:%H:%M} ET: market closed - statuses refreshed only")
    elif not equity:
        print(f"no account equity readable ({acct.get('_error')}) - nothing sent")
    else:
        # entries: today's gates, before the cutoff
        if now.time() < ENTRY_CUTOFF:
            for season, g in live_gates(today):
                if f"{season}-{g['ticker']}-{g['report_date']}-{STRUCTURES[0]}" not in trades:
                    open_event(trades, season, g, equity, now)
        for tr in trades.values():
            if tr.get("skipped") or not tr.get("legs"):
                continue
            if leg_state(tr, "open") == "open" and tr["snapshot_session"] == today:
                maybe_retry(tr, "open", lambda tr=tr: tr["legs"], now)
            # exits: reaction session from 14:30 ET; a missed exit closes on the next run before expiry
            due = (tr["reaction_session"] == today and now.time() >= EXIT_FROM) or \
                  (tr["reaction_session"] < today <= tr["expiry"])
            if due and leg_state(tr, "open") == "failed" and leg_state(tr, "close") is None:
                # no real position (the entry was simulated): the exit is simulated at the natural now
                legs = close_legs(tr)
                q = quotes([lg["symbol"] for lg in legs])
                tr["orders"]["close"] = [{"client_order_id": None, "sent_et": now.isoformat(),
                                          "natural": natural(legs, q), "status": "simulated",
                                          "quotes": {lg["symbol"]: q.get(lg["symbol"]) for lg in legs}}]
            if due and leg_state(tr, "open") == "filled":
                if leg_state(tr, "close") is None:
                    if tr["reaction_session"] < today:
                        tr["exit_late"] = True
                    legs = close_legs(tr)
                    send(tr, "close", legs, quotes([lg["symbol"] for lg in legs]), f"{tr['key']}-close")
                elif leg_state(tr, "close") == "open":
                    maybe_retry(tr, "close", lambda tr=tr: close_legs(tr), now)
    for tr in trades.values():
        if tr.get("legs") and leg_state(tr, "open") == "filled" and leg_state(tr, "close") is None \
                and today > tr["expiry"]:
            tr["flag"] = "held_past_expiry - never closed; see the account's exercise activity"
        if tr.get("legs") and "result" not in tr:
            settle(tr)
    done = sum(1 for t in trades.values() if "result" in t)
    print(f"options ledger: {len(trades)} structure(s), {done} with a result")
    if json.dumps(trades, sort_keys=True) == before and os.path.exists(LEDGER):
        print("nothing changed - no write, no commit")
        return
    led["updated_et"] = now.isoformat()
    write_json(LEDGER, led)
    if do_commit:
        from due import commit
        commit([LEDGER], f"Paper options ledger {now:%Y-%m-%d %H:%M} ET (Alpaca paper, code, D011)")


def dry(ticker, expiry, strike):
    """Build both structures from live contracts and quotes; print the orders; submit nothing."""
    ch = chain(ticker, expiry)
    k = float(strike)
    if not ch or k not in ch:
        raise SystemExit(f"{ticker} {expiry} {k}: not listed ({len(ch or {})} strikes)")
    q0 = quotes([ch[k]["call"], ch[k]["put"]])
    c, p = q0[ch[k]["call"]], q0[ch[k]["put"]]
    mid = (c["bid"] + c["ask"] + p["bid"] + p["ask"]) / 2
    acct = api("GET", "/account")
    n = max(1, math.floor(float(acct.get("equity") or 0) * RISK_PER_EVENT / (100 * mid)))
    wings = pick_wings(ch, k, mid)
    print(f"{ticker} {expiry} K={k} straddle mid {mid:.2f} n={n} wings {wings}")
    for s in "LF":
        for opening in (True, False):
            legs = legs_for(s, ch, k, wings, opening)
            q = quotes([lg["symbol"] for lg in legs])
            net = natural(legs, q)
            print(f"  {s} {'open ' if opening else 'close'} natural {net} limit "
                  f"{limit_of(net) if net is not None else None} legs "
                  f"{[(lg['symbol'], lg['side'], q.get(lg['symbol'])) for lg in legs]}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "sync":
        sync("--commit" in a)
    elif a and a[0] == "dry" and len(a) == 4:
        dry(a[1], a[2], a[3])
    else:
        raise SystemExit(__doc__)
