"""
DECISION BACKTEST — live calc-risk vs the proposed Edge Score, replayed on the FROZEN ledger.
================================================================================
Run: python backtest_edgescore.py

WHAT THIS IS
  Every ledger entry froze its full inputs (judgment/market/truth/skew/cfg) with an integrity
  hash BEFORE the print. So both scorers can be replayed on the exact information available at
  decision time. No look-ahead in the INPUTS.

WHAT THIS IS NOT — read before believing any number below
  * It is NOT an out-of-sample test. I designed the Edge Score already knowing these outcomes.
    The P&L column is therefore CONTAMINATED BY HINDSIGHT and must not be read as evidence of
    edge. Treat it as "what would have happened", never as "what will happen".
  * n is tiny (17 scored events, 2 of them real trades under the live model).
  * The reliable output is the DECISION-BEHAVIOUR column: how many abstentions convert to
    live bets, at what tier, at what size. That is a property of the design, not of luck.
"""
from __future__ import annotations
import warnings
warnings.filterwarnings("ignore")

from pre_engine import Judgment, Market, Truth, Skew, EngineConfig
from pre_calcrisk import calc_risk
from pre_edgescore import edge_score, SECTOR_OF
from pre_ledger import _read, DEFAULT_LEDGER


def _window(entry):
    """The real identity of a trade: (ticker, entry_close_date, exit_open_date).
    `event_date` is only a LABEL and has been applied inconsistently — AMC names were logged
    with event_date = the EXIT day, while their T-3 previews used the PRINT day. Keying on it
    splits one print into two 'events' and double-counts it. Falls back to event_date for old
    rows that carry no exit spec."""
    ex = (entry.get("verdict") or {}).get("exit") or {}
    if ex.get("entry_close_date") and ex.get("exit_open_date"):
        return (entry["ticker"], ex["entry_close_date"], ex["exit_open_date"])
    return (entry["ticker"], entry.get("event_date"), None)


def _is_retro(entry):
    """True if the row was written AFTER its own event — i.e. it is not a genuine
    pre-registration and its 'no look-ahead' guarantee does not hold.

    Found by external review #2: `AMKR:2026-07-27:2e7e8dcb` was logged 2026-07-28T13:44:52Z,
    fifteen minutes after the 13:30Z open at which its -14.52% gap printed. Its ONLY input
    difference from the genuine T-3 preview row is G0 DRY_RUN -> CONFIRMED. It carried an
    integrity hash indistinguishable from a real pre-registration, and it was the single
    trade sitting at the top of the conviction table that justified a design change.
    The directional call itself WAS made pre-print (documented in the 07-25 note), but the
    LEDGER ROW is not a pre-registration and must never be counted as one.
    """
    ex = (entry.get("verdict") or {}).get("exit") or {}
    ref = ex.get("exit_open_date") or entry.get("event_date")
    logged = (entry.get("logged_at") or "")[:10]
    return bool(ref and logged and logged > ref)


def _rebuild(inp):
    """Reconstruct the frozen dataclasses, tolerating fields added after an entry was written."""
    def mk(cls, d):
        if not d:
            return None
        allowed = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in allowed})
    return (mk(Judgment, inp.get("judgment")), mk(Market, inp.get("market")),
            mk(Truth, inp.get("truth")), mk(Skew, inp.get("skew")),
            mk(EngineConfig, inp.get("cfg")) or EngineConfig(fasttrack=True, watch=False,
                                                             react_in_ds=False))


def main():
    rows = _read(DEFAULT_LEDGER)
    entries = [r for r in rows if r.get("type") == "entry"]
    by_id = {e["id"]: e for e in entries}

    # BUG FIX (external review #2). Outcomes were looked up by full entry-id while entries
    # were de-duplicated by (ticker, event_date) keeping last-in-file. When a name was
    # RE-REGISTERED (AEHR, ASML, NFLX, TSM were re-logged by a later layer), the surviving
    # entry had a different id from the one the outcome was attached to — so the outcome
    # became unreachable and the trade silently vanished from every statistic.
    # Three real outcomes were being dropped: AEHR +35.04%, NFLX -10.64%, ASML +1.69% —
    # i.e. both tails of the distribution. Every downstream figure (tier table, abstention
    # rate, P&L, variant sweep) was computed on a truncated sample.
    # Fix: key outcomes by (ticker, event_date) via their parent entry.
    outcomes = {}
    for r in rows:
        if r.get("type") == "outcome":
            parent = by_id.get(r["entry_id"])
            if parent:
                outcomes[_window(parent)] = r

    # de-dup on the TRADE WINDOW, not (ticker, event_date).
    # SECOND de-dup defect, same class as the first: the SAME print was registered under two
    # different event_date labels — a T-3 preview dated to the print day, and the live row dated
    # to the exit day (AMC names were logged with event_date = exit date). APLD / AZN / NVTS each
    # have two rows for the identical 07-27->07-28 window. Keying on event_date treats them as
    # two separate events, which would DOUBLE-COUNT one print. The window (ticker, entry_close,
    # exit_open) is the real identity of a trade; event_date is just a label.
    #
    # THIRD defect in the same family: sign-layer rows carry NO exit spec at all. They are
    # diagnostics, not tradeable decisions — there is no window to enter or exit, so they can
    # never be scored. Counting them as events inflated the denominator of the abstention rate
    # and made AEHR/ASML/NFLX appear twice (once as a real trade, once as an unscoreable stub).
    # A row without a trade window is not an event. Excluded.
    tradeable = [e for e in entries
                 if ((e.get("verdict") or {}).get("exit") or {}).get("exit_open_date")]
    dropped_stubs = len(entries) - len(tradeable)

    uniq = {}
    for e in tradeable:
        k = _window(e)
        if k in uniq and _is_retro(e) and not _is_retro(uniq[k]):
            continue                      # never let a retro row supersede a genuine one
        uniq[k] = e
    entries = sorted(uniq.values(), key=lambda x: (x["event_date"], x["ticker"]))
    if dropped_stubs:
        print(f"[note] {dropped_stubs} sign-layer row(s) excluded: no trade window, unscoreable.")

    print("=" * 108)
    print("  DECISION BACKTEST — live calc-risk  vs  proposed Edge Score   (frozen inputs, no look-ahead in inputs)")
    print("=" * 108)
    print(f"{'ticker':7s}{'date':12s}{'LIVE':>10s}{'conv':>7s} | {'EDGE':>9s}{'conv':>12s}{'score':>8s}{'size$':>7s} |"
          f"{'idio':>7s}{'  P&L(gap)':>11s}  note")
    print("-" * 108)

    conv_old = {"BUY": 0, "SHORT": 0, "NO_TRADE": 0}
    conv_new = {"BUY": 0, "SHORT": 0, "NO_TRADE": 0}
    changed, pnl_old, pnl_new = [], 0.0, 0.0
    praw_old = praw_new = 0.0
    BOOK = 18_000.0
    tiers = {}
    scored_old = scored_new = 0
    wins_old = wins_new = 0

    for e in entries:
        j, m, t, sk, cfg = _rebuild(e["inputs"])
        if j is None or m is None:
            continue
        # Normalise the book. Early entries were frozen with capital=500_000 (the pre-2026-07-23
        # default); replaying them at face value produced four-figure P&L on a $18k account and
        # made the totals meaningless. All rows are replayed on the CURRENT book.
        m.capital = BOOK
        tick = e["ticker"]
        try:
            live = calc_risk(tick, j, m, t, cfg, skew=sk)
        except Exception as ex:
            print(f"{tick:7s}{e['event_date']:12s}  live-replay error: {ex}")
            continue
        new = edge_score(tick, j, m, t, cfg, skew=sk)

        conv_old[live.stance] += 1
        conv_new[new.stance] += 1
        if new.stance != "NO_TRADE":
            tiers[new.conviction] = tiers.get(new.conviction, 0) + 1

        o = outcomes.get(_window(e))
        idio = o["idio_open_pct"] if o else None

        # P&L in $ on the real book: gap_at_risk is the loss at a ONE-AVG-GAP adverse move,
        # so $ P&L = shares * price * (idio/100) with the correct sign for the stance.
        def pnl(stance, shares, price):
            if idio is None or stance == "NO_TRADE" or not shares:
                return 0.0
            return shares * price * (idio / 100.0) * (1 if stance == "BUY" else -1)

        # RAW = what the ACCOUNT actually earns (unhedged single leg).
        # IDIO = beta-stripped, the correct measure of MODEL SKILL but NOT of P&L.
        # Reporting idio under a "$ P&L" heading systematically flatters the model; both now shown.
        raw = (o["stock_open_pct"] if o else None)

        def pnl_raw(stance, shares, price):
            if raw is None or stance == "NO_TRADE" or not shares:
                return 0.0
            return shares * price * (raw / 100.0) * (1 if stance == "BUY" else -1)

        p_old = pnl(live.stance, live.shares, m.price)
        p_new = pnl(new.stance, new.shares, m.price)
        praw_old += pnl_raw(live.stance, live.shares, m.price)
        praw_new += pnl_raw(new.stance, new.shares, m.price)
        pnl_old += p_old
        pnl_new += p_new
        if idio is not None:
            if live.stance != "NO_TRADE":
                scored_old += 1; wins_old += (p_old > 0)
            if new.stance != "NO_TRADE":
                scored_new += 1; wins_new += (p_new > 0)

        flag = "" if live.stance == new.stance else "  <-- CHANGED"
        if flag:
            changed.append((tick, live.stance, new.stance, new.conviction, idio, p_new))
        idio_s = f"{idio:+6.2f}" if idio is not None else "     —"
        pnl_s = f"{p_new:+9.2f}" if (idio is not None and new.stance != "NO_TRADE") else "         —"
        print(f"{tick:7s}{e['event_date']:12s}{live.stance:>10s}{live.conviction[:6]:>7s} | "
              f"{new.stance:>9s}{new.conviction:>12s}{new.edge_score:>8.3f}"
              f"{(('$'+str(int(new.gap_at_risk))) if new.shares else '—'):>7s} |"
              f"{idio_s}{pnl_s}  {flag}")

    print("-" * 108)
    print(f"\nVERDICT MIX      live: BUY {conv_old['BUY']}  SHORT {conv_old['SHORT']}  NO_TRADE {conv_old['NO_TRADE']}")
    print(f"                 edge: BUY {conv_new['BUY']}  SHORT {conv_new['SHORT']}  NO_TRADE {conv_new['NO_TRADE']}")
    n = len(entries)
    print(f"\nABSTENTION RATE  live {conv_old['NO_TRADE']}/{n} = {conv_old['NO_TRADE']/n*100:.0f}%"
          f"   ->   edge {conv_new['NO_TRADE']}/{n} = {conv_new['NO_TRADE']/n*100:.0f}%")
    print(f"TIER MIX (new)   " + "  ".join(f"{k} {v}" for k, v in sorted(tiers.items())) or "none")

    print(f"\nRESULTS ON SCORED EVENTS (uniform ${BOOK:,.0f} book)")
    print(f"  live calc-risk : {scored_old:2d} trades, {wins_old} win | "
          f"SKILL(idio) ${pnl_old:+8.2f}   BOOK(raw) ${praw_old:+8.2f}")
    print(f"  edge score     : {scored_new:2d} trades, {wins_new} win | "
          f"SKILL(idio) ${pnl_new:+8.2f}   BOOK(raw) ${praw_new:+8.2f}")
    print("  SKILL is beta-stripped — the right measure of the MODEL, and NOT what the account")
    print("  earns. BOOK(raw) is what the account earns. The gap is the market/sector move you")
    print("  are unhedged against: real money, previously reported as if it did not exist.")
    print("  BOTH are HINDSIGHT-CONTAMINATED — the scorer was written knowing these outcomes.")
    print("  So is the TIER LABEL: `edge_score()` post-dates every row here, so a tier is not")
    print("  something a trade earned in advance. Tier-vs-outcome tables prove nothing.")

    if changed:
        print(f"\nCHANGED DECISIONS ({len(changed)}):")
        for tick, o_s, n_s, conv, idio, p in changed:
            got = f"idio {idio:+.2f}%  P&L ${p:+.2f}" if idio is not None else "no outcome yet"
            print(f"  {tick:6s} {o_s:9s} -> {n_s:9s} ({conv:11s})   {got}")


if __name__ == "__main__":
    main()
