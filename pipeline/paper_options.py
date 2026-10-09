"""Paper options (D011): the short earnings straddle, as a short iron butterfly, with real order mechanics on
Alpaca paper. Code only, no AI. Rules: registry/D011_paper_options_v1.md (this file implements it exactly).

    python pipeline/paper_options.py sync [--commit] [--exits-only]  # send due orders, record fills, write the ledger
    python pipeline/paper_options.py dry TICKER EXPIRY STRIKE        # build the orders from live quotes, send nothing

PX-F, the one structure: sell the gate's ATM call and put, buy a call at the lowest listed strike >= K + 2M and a
put at the highest listed strike <= K - 2M (M = the gate's straddle mid). The paper account refuses uncovered
short calls (probed 2026-10-08), so SH-X's naked short straddle cannot be placed; the wings make it placeable.
The long straddle (structure "L", kept in legs_for) is not traded: one account nets the same contracts, and
Alpaca refuses an order against an opposite open order ("potential wash trade").

State lives in Alpaca, not only in the ledger: before any order is sent its client_order_id is looked up, and an
existing order is adopted, never resent. The ledger is written after every send.
Keys come from APCA_API_KEY_ID / APCA_API_SECRET_KEY (GitHub secrets); they are never printed or stored.
"""
import datetime
import glob
import json
import math
import os
import subprocess
import sys
import traceback

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ET, ROOT, now_et, write_json  # noqa: E402
from paper import BASE, headers  # noqa: E402

LEDGER = os.path.join(ROOT, "paper", "options_ledger.json")
DATA = "https://data.alpaca.markets/v1beta1/options/snapshots"
RISK_PER_EVENT = 0.005
WING_MULT = 2.0
ENTRY_CUTOFF = datetime.time(15, 55)          # no opening order at or after this (snapshot session)
EXIT_FROM = datetime.time(14, 30)             # the primary exit starts here (reaction session)
EXIT_PRIMARY_END = datetime.time(15, 0)       # a first close sent after this is exit_late
LAST_SEND = datetime.time(15, 55)             # no order of any kind at or after this
RETRY_AFTER_MIN = 15                          # a live order this old is cancelled; the next run resends
MAX_OPEN_ATTEMPTS = 2                         # the opening order is sent at most twice (-open, -open-r1)
UNVERIFIED_OPEN_CAP = 3                       # opens allowed before the first real fill passes the sanity check
SEASONS_EXCLUDED = ("pilot",)
STRUCTURES = "F"
TERMINAL = ("filled", "canceled", "expired", "rejected", "done_for_day", "replaced")
LIVE_WAIT = ("pending_cancel", "pending_new", "accepted", "new", "partially_filled", "pending_replace",
             "accepted_for_bidding", "calculated", "held")


class Transient(Exception):
    """A network or 5xx error: nothing is decided, the next run tries again."""


# ---------------------------------------------------------------- broker
def call(method, path, **kw):
    """Alpaca trading API. Returns (status_code, json). Raises Transient on network errors and 5xx/429."""
    try:
        r = requests.request(method, BASE + path, headers=headers(), timeout=30, **kw)
    except requests.RequestException as e:
        raise Transient(f"{method} {path}: {type(e).__name__}")
    if r.status_code >= 500 or r.status_code == 429:
        raise Transient(f"{method} {path}: HTTP {r.status_code}")
    try:
        body = r.json() if r.text else {}
    except ValueError:
        body = {"_text": r.text[:300]}
    return r.status_code, body


def chain(ticker, expiry):
    """{strike: {"call": symbol, "put": symbol}} for one expiry: standard 100-share contracts only; a strike with
    two contracts of one type (an adjusted series) is dropped. {} = nothing listed. Raises Transient."""
    out, seen_twice, token = {}, set(), None
    while True:
        params = {"underlying_symbols": ticker.replace("-", "."), "expiration_date": expiry, "limit": 1000}
        if token:
            params["page_token"] = token
        code, got = call("GET", "/options/contracts", params=params)
        if code != 200:
            raise Transient(f"contracts {ticker} {expiry}: HTTP {code}")
        for c in got.get("option_contracts") or []:
            if not c.get("tradable") or str(c.get("size")) != "100":
                continue
            k = float(c["strike_price"])
            if c["type"] in out.get(k, {}):
                seen_twice.add(k)
            out.setdefault(k, {})[c["type"]] = c["symbol"]
        token = got.get("next_page_token")
        if not token:
            return {k: v for k, v in out.items() if k not in seen_twice}


def quotes(symbols):
    """{symbol: {"bid", "ask", "t"}} from the indicative feed. Raises Transient on any failure."""
    try:
        r = requests.get(DATA, params={"symbols": ",".join(symbols), "feed": "indicative"}, headers=headers(),
                         timeout=30)
    except requests.RequestException as e:
        raise Transient(f"quotes: {type(e).__name__}")
    if r.status_code != 200:
        raise Transient(f"quotes: HTTP {r.status_code}")
    out = {}
    for s, snap in (r.json().get("snapshots") or {}).items():
        q = snap.get("latestQuote") or {}
        out[s] = {"bid": q.get("bp"), "ask": q.get("ap"), "t": q.get("t")}
    return out


def cents_up(x):
    return math.ceil(round(x * 100, 6)) / 100


def cents_down(x):
    return math.floor(round(x * 100, 6)) / 100


# ---------------------------------------------------------------- structures and prices
def legs_for(structure, ch, k, wings, opening):
    """The legs of one structure. Closing reverses every side."""
    if structure == "L":
        base = [(ch[k]["call"], "buy"), (ch[k]["put"], "buy")]
    else:
        lo, hi = wings
        base = [(ch[k]["call"], "sell"), (ch[k]["put"], "sell"), (ch[hi]["call"], "buy"), (ch[lo]["put"], "buy")]
    out = []
    for sym, side in base:
        if not opening:
            side = "sell" if side == "buy" else "buy"
        out.append({"symbol": sym, "ratio_qty": "1", "side": side,
                    "position_intent": f"{side}_to_{'open' if opening else 'close'}"})
    return out


def close_legs(legs):
    return [dict(lg, side="sell" if lg["side"] == "buy" else "buy",
                 position_intent=("sell" if lg["side"] == "buy" else "buy") + "_to_close") for lg in legs]


def natural(legs, q):
    """Net cash per unit at the far side of every leg: + = we pay (debit), - = we receive (credit). None if a
    needed quote is missing, or a leg we sell to open has no bid. A sold wing with a zero bid counts as 0."""
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
    """Marketable limit in Alpaca's documented convention: debit positive, credit negative; rounded to the cent
    on the side that keeps it marketable."""
    return cents_up(net) if net >= 0 else -cents_down(-net)


def pick_wings(ch, k, straddle_mid):
    w = WING_MULT * straddle_mid
    hi = [s for s in ch if s >= k + w and "call" in ch[s]]
    lo = [s for s in ch if s <= k - w and "put" in ch[s]]
    return (max(lo), min(hi)) if hi and lo else None


def fly_payoff(s, k, lo, hi):
    """What closing a short iron butterfly costs at expiry with the underlying at s (per unit, >= 0)."""
    return max(0.0, s - k) - max(0.0, s - hi) + max(0.0, k - s) - max(0.0, lo - s)


# ---------------------------------------------------------------- orders
def to_rec(o, sent_sides):
    """The fields we keep of an Alpaca order. Leg sides come from what WE sent, never from the response."""
    legs = []
    for lg in o.get("legs") or []:
        legs.append({"symbol": lg.get("symbol"), "side": sent_sides.get(lg.get("symbol")),
                     "qty": float(lg.get("filled_qty") or 0),
                     "price": float(lg["filled_avg_price"]) if lg.get("filled_avg_price") else None})
    return {"id": o.get("id"), "status": o.get("status"), "filled_qty": float(o.get("filled_qty") or 0),
            "filled_at": o.get("filled_at"), "legs_filled": legs}


def lookup(cid):
    code, o = call("GET", "/orders:by_client_order_id", params={"client_order_id": cid})
    return o if code == 200 and o.get("id") else None


def send(tr, which, legs, qty, cid, now):
    """Send one mleg order, or adopt the existing order with this id. Returns the attempt record (or None when
    no order could be built: no id is consumed and the next run tries again)."""
    sides = {lg["symbol"]: lg["side"] for lg in legs}
    existing = lookup(cid)
    q = quotes([lg["symbol"] for lg in legs])
    net = natural(legs, q)
    rec = {"client_order_id": cid, "sent_et": now.isoformat(), "qty": qty, "natural": net, "sides": sides,
           "quotes": {lg["symbol"]: q.get(lg["symbol"]) for lg in legs}}
    if existing:
        rec.update(to_rec(existing, sides), adopted=True)
    elif net is None:
        tr.setdefault("not_sent", []).append({"which": which, "at": now.isoformat(),
                                              "why": "a needed quote is missing or a sold leg has no bid"})
        print(f"{tr['key']} {which}: not sent (quote missing) - retried next run")
        return None
    else:
        body = {"order_class": "mleg", "qty": str(qty), "type": "limit", "limit_price": f"{limit_of(net):.2f}",
                "time_in_force": "day", "client_order_id": cid, "legs": legs}
        code, got = call("POST", "/orders", json=body)
        rec["limit_price"] = body["limit_price"]
        if code < 300:
            rec.update(to_rec(got, sides))
        else:
            again = lookup(cid)                   # a duplicate-id refusal means the order exists: adopt it
            if again:
                rec.update(to_rec(again, sides), adopted=True)
            else:
                msg = json.dumps(got)[:300]
                kind = "capacity" if "buying power" in msg.lower() else "rejected_code"
                rec.update(status="rejected", reject_kind=kind, error=f"HTTP {code} {msg}", filled_qty=0.0,
                           legs_filled=[])
    tr.setdefault("orders", {}).setdefault(which, []).append(rec)
    print(f"{tr['key']} {which} {cid}: qty {qty} natural {net} -> {rec['status']}"
          f"{' (adopted)' if rec.get('adopted') else ''}{' ' + rec['error'] if rec.get('error') else ''}")
    return rec


def refresh(rec):
    if not rec.get("id") or rec.get("status") in TERMINAL:
        return
    code, o = call("GET", f"/orders/{rec['id']}")
    if code == 200:
        rec.update(to_rec(o, rec.get("sides") or {}))


def chain_state(tr, which):
    """(filled_qty, live_record_or_None, attempts, records) for the opening or closing chain."""
    recs = (tr.get("orders") or {}).get(which) or []
    filled = sum(r.get("filled_qty") or 0 for r in recs if r.get("id"))
    live = next((r for r in recs if r.get("id") and r.get("status") not in TERMINAL), None)
    return filled, live, len(recs), recs


def fill_net(recs):
    """Quantity-weighted net cash per unit over every filled leg of a chain: + paid, - received. None if a
    leg's fill is incomplete (a leg quantity differs from its order's)."""
    total, qty = 0.0, 0.0
    for r in recs:
        if not r.get("filled_qty"):
            continue
        for lg in r["legs_filled"]:
            if lg["price"] is None or lg["side"] is None or abs(lg["qty"] - r["filled_qty"]) > 1e-9:
                return None
            total += lg["price"] * lg["qty"] * (1 if lg["side"] == "buy" else -1)
        qty += r["filled_qty"]
    return total / qty if qty else None


def maybe_cancel_stale(rec, now):
    """A live order RETRY_AFTER_MIN old is cancelled. The resend happens on a LATER run, once Alpaca reports the
    cancel as final - so a cancel that loses the race with a fill can never double the position."""
    age = (now - datetime.datetime.fromisoformat(rec["sent_et"])).total_seconds() / 60
    if age >= RETRY_AFTER_MIN and not rec.get("cancel_requested"):
        call("DELETE", f"/orders/{rec['id']}")
        rec["cancel_requested"] = now.isoformat()


# ---------------------------------------------------------------- events
def committed(path):
    out = subprocess.run(["git", "log", "-1", "--format=%cI", "--", path], cwd=ROOT, capture_output=True,
                         text=True).stdout.strip()
    return bool(out)


def live_gates():
    """Every live-season gate.json, with why SH-X or D011 would not take it."""
    out = []
    for gp in sorted(glob.glob(os.path.join(ROOT, "events", "*", "*", "gate.json"))):
        season = os.path.basename(os.path.dirname(os.path.dirname(gp)))
        if season in SEASONS_EXCLUDED:
            continue
        g = json.load(open(gp, encoding="utf-8"))
        o = g.get("options") or {}
        c, p = o.get("call") or {}, o.get("put") or {}
        why = None
        if g.get("dry"):
            why = "dry_gate"
        elif not (o.get("expiry") and o.get("strike") and o.get("spot") and c.get("bid") is not None
                  and p.get("bid") is not None):
            why = "not_in_shx"
        elif not (c.get("ask") and p.get("ask")):
            why = "not_eligible_vs_shx (no ask)"
        out.append((season, g, why, committed(gp)))
    return out


def open_event(trades, season, g, equity, now):
    """Create the trade record for one gate. Raises Transient (the record is then not created)."""
    o = g["options"]
    base = f"{season}-{g['ticker']}-{g['report_date']}"
    mid = (o["call"]["bid"] + o["call"]["ask"] + o["put"]["bid"] + o["put"]["ask"]) / 2
    common = {"season": season, "ticker": g["ticker"], "report_date": g["report_date"], "session": g["session"],
              "snapshot_session": g["snapshot_session"], "reaction_session": g["timing"]["reaction_day"],
              "expiry": o["expiry"], "strike": float(o["strike"]), "spot_at_gate": o["spot"],
              "gate_status": g.get("status"), "gate_captured_et": g.get("captured_et"), "gate_straddle_mid": mid,
              "gate_bid_sum": o["call"]["bid"] + o["put"]["bid"],
              "n": max(1, math.floor(equity * RISK_PER_EVENT / (100 * mid))), "equity": equity,
              "created_et": now.isoformat()}
    for s in STRUCTURES:
        key = f"{base}-{s}"
        if o["expiry"] < g["timing"]["reaction_day"]:
            trades[key] = dict(common, key=key, structure=s, skipped="expiry_before_reaction")
            continue
        ch = chain(g["ticker"], o["expiry"])
        k = float(o["strike"])
        tr = dict(common, key=key, structure=s)
        if k not in ch or "call" not in ch[k] or "put" not in ch[k]:
            tr["skipped"] = "contract_not_listed_at_alpaca"
        else:
            wings = pick_wings(ch, k, mid)
            if not wings:
                tr["skipped"] = "no_wing_strike"
            else:
                tr["wings"] = list(wings)
                tr["legs"] = legs_for(s, ch, k, wings, True)
        trades[key] = tr


def sanity(tr, led):
    """D011 §5: a real opening fill whose net has the wrong sign, or sits far from the natural, halts new opens."""
    filled, _, _, recs = chain_state(tr, "open")
    if not filled or tr.get("sanity_checked") or any(r.get("adopted") for r in recs if r.get("filled_qty")):
        return
    net = fill_net(recs)
    if net is None:
        tr["fill_unreadable"] = True                 # an alert: the leg-by-leg fill could not be read
        return
    nat = next((r["natural"] for r in recs if r.get("filled_qty") and r.get("natural") is not None), None)
    if net is None or nat is None:
        return
    tr["sanity_checked"] = True
    if (net > 0) != (nat > 0) or abs(net - nat) > max(0.25 * abs(nat), 0.30):
        led["halt"] = {"since": now_et().isoformat(), "trade": tr["key"], "fill_net": net, "natural": nat,
                       "why": "fill anomaly - new opens stopped until a person clears 'halt' in the ledger"}
    elif not led.get("convention_verified"):
        led["convention_verified"] = {"trade": tr["key"], "fill_net": net, "natural": nat}


def settle(tr):
    """The result once both chains are complete, real or simulated. Per unit, + = profit."""
    o_f, o_live, _, o_recs = chain_state(tr, "open")
    c_f, c_live, _, c_recs = chain_state(tr, "close")
    if o_live or c_live or "result" in tr:
        return
    sim = {}
    if o_f:
        o_net = fill_net(o_recs)
        if o_f < tr["n"]:
            tr["partial_open"] = o_f
    elif tr.get("open_failed") == "platform":
        o_net = next((r["natural"] for r in o_recs if r.get("natural") is not None), None)
        sim["open"] = "opening order unfilled for a platform reason; booked at the natural when sent"
    else:
        return
    if o_f and c_f >= o_f:
        c_net = fill_net(c_recs)
    elif tr.get("close_sim"):
        cs = tr["close_sim"]
        if o_f and c_f:   # part real, part simulated: weight by quantity
            real = fill_net(c_recs)
            c_net = None if real is None or cs["net"] is None else (real * c_f + cs["net"] * (o_f - c_f)) / o_f
        else:
            c_net = cs["net"]
        sim["close"] = cs["why"]
    else:
        return
    if o_net is None or c_net is None:
        return
    unit = -(o_net + c_net)
    qty = o_f or tr["n"]
    tr["result"] = {"open_net": o_net, "close_net": c_net, "pnl_per_unit": unit, "qty": qty,
                    "pnl": round(unit * 100 * qty, 2), "pnl_on_spot": unit / tr["spot_at_gate"],
                    "simulated_legs": sorted(sim), "simulated_why": sim or None}
    if "open" not in sim and not any(r.get("adopted") for r in o_recs if r.get("filled_qty")):
        nat = next((r["natural"] for r in o_recs if r.get("filled_qty") and r.get("natural") is not None), None)
        # negative = the fill beat the natural (we received more credit than the far sides)
        tr["result"]["entry_vs_alpaca_natural"] = o_net - nat if nat is not None else None
        tr["result"]["entry_credit_vs_gate_bid_sum"] = -o_net - tr["gate_bid_sum"]


def expiry_close(ticker, expiry):
    import yfinance as yf
    d = datetime.date.fromisoformat(expiry)
    h = yf.Ticker(ticker).history(start=expiry, end=(d + datetime.timedelta(days=5)).isoformat(),
                                  auto_adjust=False).tz_convert(ET)
    row = h[h.index.date == d]
    return float(row["Close"].iloc[0]) if len(row) else None


# ---------------------------------------------------------------- the run
def load_ledger():
    if os.path.exists(LEDGER):
        return json.load(open(LEDGER, encoding="utf-8"))
    return {"rule": "D011_paper_options_v1", "structures": {"F": "short iron butterfly"}, "trades": {}}


def step(tr, led, now, today, market_open, exits_only, opens_left):
    """One trade, one run. Returns the number of NEW opening orders sent."""
    sent = 0
    if tr.get("skipped") or not tr.get("legs"):
        return 0
    o_f, o_live, o_n, o_recs = chain_state(tr, "open")
    t = now.time()
    can_send = market_open and t < LAST_SEND
    # ---- opening chain (snapshot session only)
    if o_live and can_send and tr["snapshot_session"] == today:
        maybe_cancel_stale(o_live, now)
    if (not exits_only and can_send and not o_live and not o_f and tr["snapshot_session"] == today
            and t < ENTRY_CUTOFF and o_n < MAX_OPEN_ATTEMPTS and not any(r.get("reject_kind") for r in o_recs)):
        if led.get("halt") and o_n == 0:
            tr["open_blocked"] = "halt"
        elif opens_left <= 0 and o_n == 0:            # a retry of an order already sent is not a new open
            tr["open_blocked"] = "held_by_cap"
        else:
            cid = f"{tr['key']}-open" + ("" if o_n == 0 else f"-r{o_n}")
            if send(tr, "open", tr["legs"], tr["n"], cid, now):
                sent = 1 if o_n == 0 else 0
                tr.pop("open_blocked", None)
                write_json(LEDGER, led)
        o_f, o_live, o_n, o_recs = chain_state(tr, "open")
    # the opening chain is final once nothing is live and either it filled or it can never be sent again
    open_over = not o_live and (o_f or tr["snapshot_session"] < today or o_n >= MAX_OPEN_ATTEMPTS
                                or any(r.get("reject_kind") for r in o_recs)
                                or (tr["snapshot_session"] == today and t >= ENTRY_CUTOFF))
    if open_over and not o_f and "open_failed" not in tr:
        kinds = [r.get("reject_kind") for r in o_recs if r.get("reject_kind")]
        if kinds:
            tr["open_failed"] = kinds[-1]           # capacity or rejected_code: never simulated
        elif o_recs:
            tr["open_failed"] = "platform"          # expired / cancelled unfilled: simulated (Jacob, 2026-10-02)
        else:
            # no order ever existed: blocked by the sign-guard cap or a halt, or quotes never readable
            tr["open_failed"] = tr.get("open_blocked") or "never_sent"
    # ---- closing chain (reaction session from 14:30 ET; a missed exit closes on any later run before expiry)
    due = (tr["reaction_session"] == today and t >= EXIT_FROM) or (tr["reaction_session"] < today <= tr["expiry"])
    c_f, c_live, c_n, c_recs = chain_state(tr, "close")
    if due and can_send and o_f and c_f < o_f:
        if c_live:
            maybe_cancel_stale(c_live, now)
        elif sum(1 for r in c_recs if r.get("reject_kind")) >= 3:
            tr["close_rejected"] = [r.get("error") for r in c_recs if r.get("reject_kind")][-1]
        else:
            if c_n == 0:
                late = tr["reaction_session"] < today or t >= EXIT_PRIMARY_END
                tr["exit_first_sent_et"] = now.isoformat()
                tr["exit_late"] = late
            cid = f"{tr['key']}-close" + ("" if c_n == 0 else f"-r{c_n}")
            if send(tr, "close", close_legs(tr["legs"]), int(o_f - c_f), cid, now):
                write_json(LEDGER, led)
    if due and can_send and not o_f and tr.get("open_failed") == "platform" and "close_sim" not in tr:
        q = quotes([lg["symbol"] for lg in close_legs(tr["legs"])])
        net = natural(close_legs(tr["legs"]), q)
        if net is not None:                          # no price yet: the next run tries again
            tr["close_sim"] = {"net": net, "at": now.isoformat(),
                               "why": "no real position (the entry was simulated); natural at this run"}
    # ---- never closed by expiry: flagged, and the remainder settled at the expiry close (as SH-X does)
    c_f, c_live, _, _ = chain_state(tr, "close")
    if o_f and c_f < o_f and today > tr["expiry"] and not c_live and "close_sim" not in tr:
        tr["flag"] = "held_past_expiry - see the account's exercise and assignment activity"
        s = expiry_close(tr["ticker"], tr["expiry"])
        if s is not None:
            lo, hi = tr["wings"]
            tr["close_sim"] = {"net": fly_payoff(s, tr["strike"], lo, hi), "at": now.isoformat(),
                               "why": f"held past expiry; settled at intrinsic on the expiry close {s}"}
    sanity(tr, led)
    settle(tr)
    return sent


def sync(do_commit=False, exits_only=False):
    now = now_et()
    today = now.date().isoformat()
    led = load_ledger()
    trades = led["trades"]
    before = json.dumps(led, sort_keys=True)
    errors = []
    try:
        for tr in trades.values():
            for recs in (tr.get("orders") or {}).values():
                for r in recs:
                    refresh(r)
        code, clock = call("GET", "/clock")
        market_open = code == 200 and bool(clock.get("is_open"))
        code, acct = call("GET", "/account")
        equity = float(acct.get("equity") or 0) if code == 200 else 0.0
    except Transient as e:
        print(f"broker unreachable ({e}) - nothing decided this run")
        return 1
    gates = live_gates()
    # new trade records: today's committed gates, while the entry window is open
    if not exits_only and market_open and equity and now.time() < ENTRY_CUTOFF:
        for season, g, why, is_committed in gates:
            key = f"{season}-{g['ticker']}-{g['report_date']}-{STRUCTURES[0]}"
            if key in trades or g.get("snapshot_session") != today or why or not is_committed:
                continue
            try:
                open_event(trades, season, g, equity, now)
            except Transient as e:
                errors.append(f"{key}: {e}")
    # bookkeeping: every live gate that never got a trade record says why
    for season, g, why, _ in gates:
        key = f"{season}-{g['ticker']}-{g['report_date']}-{STRUCTURES[0]}"
        if key in trades or not g.get("snapshot_session"):
            continue
        if why:
            trades[key] = {"key": key, "ticker": g["ticker"], "report_date": g["report_date"], "skipped": why,
                           "gate_status": g.get("status")}
        elif g["snapshot_session"] < today or (g["snapshot_session"] == today and now.time() >= ENTRY_CUTOFF):
            try:
                orphan = lookup(f"{key}-open")        # a lost ledger must not hide a real order
            except Transient:
                continue
            trades[key] = {"key": key, "ticker": g["ticker"], "report_date": g["report_date"],
                           "gate_status": g.get("status")}
            if orphan:
                trades[key]["orphan_order"] = {"id": orphan.get("id"), "status": orphan.get("status")}
            else:
                trades[key]["skipped"] = "missed_entry_window"
    unverified_opens = 0 if led.get("convention_verified") else sum(
        1 for t in trades.values() if (t.get("orders") or {}).get("open"))
    opens_left = 10 ** 6 if led.get("convention_verified") else max(0, UNVERIFIED_OPEN_CAP - unverified_opens)
    for tr in trades.values():
        try:
            opens_left -= step(tr, led, now, today, market_open, exits_only, opens_left)
        except Transient as e:
            errors.append(f"{tr.get('key')}: {e}")
        except Exception:
            errors.append(f"{tr.get('key')}: {traceback.format_exc(limit=3)}")
    led["errors_last_run"] = errors or None
    alerts = [t["key"] for t in trades.values()
              if t.get("open_failed") in ("rejected_code", "held_by_cap", "halt") or t.get("flag")
              or t.get("partial_open") or t.get("close_rejected") or t.get("orphan_order")
              or t.get("fill_unreadable")
              or any(r.get("reject_kind") for r in (t.get("orders") or {}).get("close") or [])]
    led["alerts"] = alerts or None
    done = sum(1 for t in trades.values() if "result" in t)
    print(f"options ledger: {len(trades)} record(s), {done} with a result; errors {len(errors)}; "
          f"alerts {alerts}; halt {bool(led.get('halt'))}")
    for e in errors:
        print("  error:", e)
    if json.dumps(led, sort_keys=True) != before or not os.path.exists(LEDGER):
        led["updated_et"] = now.isoformat()
        write_json(LEDGER, led)
        if do_commit and not commit_ledger(f"Paper options ledger {now:%Y-%m-%d %H:%M} ET (Alpaca paper, code, D011)"):
            print("PUSH FAILED - the ledger is not on GitHub")
            return 1
    else:
        print("nothing changed - no write, no commit")
    # any alert, an unexpected exception, or a halt turns the run red so it is seen
    return 1 if alerts or any("Traceback" in e for e in errors) or led.get("halt") else 0


def commit_ledger(message):
    """Commit the ledger and push to every remote; False if any push failed."""
    from freeze import git, push_all
    git("add", os.path.relpath(LEDGER, ROOT).replace(os.sep, "/"))
    if not git("diff", "--cached", "--name-only"):
        return True
    git("commit", "-q", "-m", message + "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
    res = push_all()
    print(f"pushed: {res}")
    return all(res.values())


def dry(ticker, expiry, strike):
    """Build the structure from live contracts and quotes; print the orders; send nothing."""
    ch = chain(ticker, expiry)
    k = float(strike)
    if k not in ch:
        raise SystemExit(f"{ticker} {expiry} {k}: not listed ({len(ch)} strikes)")
    q0 = quotes([ch[k]["call"], ch[k]["put"]])
    c, p = q0[ch[k]["call"]], q0[ch[k]["put"]]
    mid = (c["bid"] + c["ask"] + p["bid"] + p["ask"]) / 2
    code, acct = call("GET", "/account")
    n = max(1, math.floor(float(acct.get("equity") or 0) * RISK_PER_EVENT / (100 * mid)))
    wings = pick_wings(ch, k, mid)
    print(f"{ticker} {expiry} K={k} straddle mid {mid:.2f} n={n} wings {wings}")
    for opening in (True, False):
        legs = legs_for("F", ch, k, wings, opening)
        q = quotes([lg["symbol"] for lg in legs])
        net = natural(legs, q)
        print(f"  F {'open ' if opening else 'close'} natural {net} limit {limit_of(net) if net is not None else None}"
              f" legs {[(lg['symbol'], lg['side'], q.get(lg['symbol'])) for lg in legs]}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "sync":
        sys.exit(sync("--commit" in a, "--exits-only" in a))
    elif a and a[0] == "dry" and len(a) == 4:
        dry(a[1], a[2], a[3])
    else:
        raise SystemExit(__doc__)
