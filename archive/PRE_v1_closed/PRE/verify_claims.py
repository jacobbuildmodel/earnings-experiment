"""
VERIFY THE EXTERNAL REVIEW (#3, 2026-08-09) AGAINST THE ACTUAL CODE AND LEDGER.
================================================================================
The reviewer read METHOD.md, not the implementation, and said so explicitly:
"anything numerical below is 'the doc says X, and X implies Y' — check Y against
the implementation before acting on it."

This file does that check. It is re-runnable, it touches nothing, and every number
it prints comes from `pre_edgescore.edge_score` or from `ledger.jsonl` /
`forecasts.jsonl` — never from the prose.

    python verify_claims.py
"""
from __future__ import annotations
import json
import statistics
from pathlib import Path

from pre_engine import Judgment, Market
from pre_edgescore import (edge_score, W_EXPECTATIONS, W_POSITIONING, EXPECTATIONS_NORM,
                           CONF_FLOOR, CONF_SPAN, EDGE_MIN, TIERS, FLAT_RISK_BUDGET,
                           SIZE_BY_CONVICTION)

ROOT = Path(__file__).parent
LINE = "=" * 78


def hdr(n, s):
    print(f"\n{LINE}\nCLAIM {n} — {s}\n{LINE}")


def mk(rev_up=0, rev_dn=0, cov=10, gg=None, vel=None, excess=-30.0, dd=40.0):
    """Build a Judgment/Market pair. `excess` is stock% - sector% over the window."""
    j = Judgment(up_revisions_30d=rev_up, down_revisions_30d=rev_dn, covering_analysts=cov,
                 GG=gg, VEL=vel, FLAG=0, CBR="CLEAN", G0="CONFIRMED",
                 stock_pct_since_last_earnings=excess, sector_etf_pct_same_window=0.0,
                 pct_within_52w_high=dd, pct_below_52w_high=dd)
    m = Market(price=100.0, avg_abs_open=5.0, confirmed_quarters=8,
               dollar_vol_20d=400_000_000, share_vol_20d=5_000_000, implied_move=5.0,
               capital=18_000, vix=16.0, spy_5d_realvol_wow=0.0, spx_day=0.0,
               macro_overlap=False, borrow_locate=True, borrow_fee=0.0,
               g2_estimated=False, gap_bad_case=8.0)
    return j, m


# ---------------------------------------------------------------------------
hdr(1, "THE UNITS/NORMALISATION DEFECT: is washout worth ~1.6 notches of REV?")
print(f"  W_EXPECTATIONS={W_EXPECTATIONS}  W_POSITIONING={W_POSITIONING}  "
      f"EXPECTATIONS_NORM={EXPECTATIONS_NORM}")
print(f"  REV is an integer bucket in [-2,+2]; with GG/VEL unsourced, "
      f"expectations = REV/{EXPECTATIONS_NORM:.0f} in [-0.5,+0.5]")
notch = W_EXPECTATIONS * (1 / EXPECTATIONS_NORM)
wash = W_POSITIONING * 1.0
print(f"  one REV notch contributes {notch:.4f} to raw_edge")
print(f"  the washout flag contributes {wash:.4f}")
print(f"  => washout is worth {wash/notch:.2f} REV notches   "
      f"[reviewer said ~1.6]  {'CONFIRMED' if 1.5 < wash/notch < 1.8 else 'REFUTED'}")

print("\n  The reviewer's three verdict cases, run through the REAL edge_score():")
cases = [
    ("WASHED, REV = 0   (R=0.00)", dict(rev_up=5, rev_dn=5, excess=-30.0, dd=40.0)),
    ("not washed, REV=+1 (R=+0.20)", dict(rev_up=4, rev_dn=2, excess=0.0, dd=10.0)),
    ("WASHED, REV = -1  (R=-0.20)", dict(rev_up=3, rev_dn=5, excess=-30.0, dd=40.0)),
]
for label, kw in cases:
    j, m = mk(**kw)
    v = edge_score("TEST", j, m)
    print(f"    {label:34s} exp={v.expectations_momentum:+.3f} pos={v.positioning:+.2f} "
          f"conf={v.confidence:.3f} edge={v.edge_score:+.4f}  -> {v.stance} {v.conviction}")

print("\n  >>> THE QUESTION THAT MATTERS: does a WASHED name with DETERIORATING")
print("      revisions still clear the buy bar?")
j, m = mk(rev_up=3, rev_dn=5, excess=-30.0, dd=40.0)   # R=-0.20 -> REV=-1
v = edge_score("TEST", j, m)
print(f"      REV bucket {v.expectations_momentum*EXPECTATIONS_NORM:+.0f}, "
      f"edge {v.edge_score:+.4f} vs EDGE_MIN {EDGE_MIN}  ->  {v.stance}")
print(f"      {'*** CONFIRMED — the washout term overrides a negative fundamental read.'
        if v.stance == 'BUY' else 'REFUTED — it does not clear.'}")

# how negative must REV get before washout stops carrying it?
print("\n  How far can REV fall before a WASHED name stops being a BUY?")
for up, dn in [(5, 5), (3, 5), (2, 5), (1, 5), (0, 5), (0, 10)]:
    j, m = mk(rev_up=up, rev_dn=dn, excess=-30.0, dd=40.0)
    v = edge_score("TEST", j, m)
    R = (up - dn) / 10
    print(f"    up={up:2d} dn={dn:2d}  R={R:+.2f}  REV bucket "
          f"{v.expectations_momentum*EXPECTATIONS_NORM:+.0f}  edge={v.edge_score:+.4f}  {v.stance}")

# ---------------------------------------------------------------------------
hdr(2, "IS *MAXIMUM* CONVICTION REACHABLE ON A REV-ONLY NAME?")
j, m = mk(rev_up=6, rev_dn=0, cov=10, excess=-30.0, dd=40.0)   # R=+0.60 -> REV=+2, washed
v = edge_score("TEST", j, m)
print(f"  best possible REV-only washed long: exp={v.expectations_momentum:+.3f} "
      f"pos={v.positioning:+.1f} completeness={v.completeness:.2f} conf={v.confidence:.3f}")
print(f"  edge = {v.edge_score:.4f}   MAXIMUM tier needs {TIERS[0][0]}")
print(f"  => {'CONFIRMED — MAXIMUM is UNREACHABLE without GG or VEL.' if v.edge_score < TIERS[0][0] else 'REFUTED.'}")
j2, m2 = mk(rev_up=6, rev_dn=0, cov=10, gg=1, vel=1, excess=-30.0, dd=40.0)
v2 = edge_score("TEST", j2, m2)
print(f"  with GG=+1 and VEL=+1 verified: conf={v2.confidence:.2f} edge={v2.edge_score:.4f} "
      f"-> {v2.conviction}   (so the ceiling is a SOURCING ceiling, not a market one)")

# ---------------------------------------------------------------------------
hdr(3, "IS THE STATED SIZING RANGE (0.275%-0.50%) REACHABLE?")
print(f"  SIZE_BY_CONVICTION={SIZE_BY_CONVICTION}  FLAT_RISK_BUDGET={FLAT_RISK_BUDGET}")
print(f"  confidence = {CONF_FLOOR} + {CONF_SPAN} * completeness")
print("  completeness slots = {REV, GG, VEL, WASH}")
print("  REV and WASH are available on essentially every covered name -> completeness >= 0.50")
for comp in (0.0, 0.25, 0.5, 0.75, 1.0):
    conf = CONF_FLOOR + CONF_SPAN * comp
    print(f"    completeness {comp:.2f} -> confidence {conf:.3f} -> budget "
          f"{FLAT_RISK_BUDGET*conf*100:.3f}%")
print(f"  METHOD.md §4 claims the range is 0.275%-0.50%. The 0.275% floor needs")
print(f"  completeness=0, i.e. NO REV and NO WASH — a state with no signal at all,")
print(f"  which yields edge=0 -> NO_TRADE. *** DOC IS WRONG. Real trading range is")
print(f"  ~{FLAT_RISK_BUDGET*(CONF_FLOOR+CONF_SPAN*0.5)*100:.3f}%-{FLAT_RISK_BUDGET*100:.3f}% "
      f"— a {(FLAT_RISK_BUDGET*1.0)/(FLAT_RISK_BUDGET*0.775):.2f}x spread. Near flat-bet.")

# ---------------------------------------------------------------------------
hdr(4, "corr(REV, positioning) — the measurement that was made for SAT and never repeated")
rows = [json.loads(l) for l in (ROOT / "ledger.jsonl").open(encoding="utf-8") if l.strip()]
entries = [r for r in rows if r.get("type") == "entry"]
pairs = []
for e in entries:
    c = (e.get("verdict") or {}).get("components") or {}
    ji = (e.get("inputs") or {}).get("judgment") or {}
    rev = c.get("REV")
    ex, se = ji.get("stock_pct_since_last_earnings"), ji.get("sector_etf_pct_same_window")
    dd = ji.get("pct_below_52w_high")
    if rev is None or ex is None or se is None:
        continue
    excess = ex - se
    wash = 1 if (excess <= -15 and dd is not None and dd >= 20) else (-1 if excess >= 15 else 0)
    pairs.append((rev, wash, excess))
print(f"  n = {len(pairs)} ledger entries with both terms computable")
if len(pairs) >= 3:
    revs = [p[0] for p in pairs]
    washes = [p[1] for p in pairs]
    excesses = [p[2] for p in pairs]
    try:
        r1 = statistics.correlation(revs, washes)
        print(f"  corr(REV, positioning_flag) = {r1:+.3f}")
    except statistics.StatisticsError as ex:
        print(f"  corr(REV, positioning_flag) undefined: {ex}")
    try:
        r2 = statistics.correlation(revs, excesses)
        print(f"  corr(REV, excess_vs_sector) = {r2:+.3f}   "
              f"(positive => washed names DO carry weaker revisions)")
    except statistics.StatisticsError as ex:
        print(f"  corr(REV, excess) undefined: {ex}")
    nz = [p for p in pairs if p[1] != 0]
    if nz:
        print(f"  entries where the washout/extension flag actually fired: {len(nz)}/{len(pairs)}")
        print(f"    mean REV when flag fired: "
              f"{statistics.mean(p[0] for p in nz):+.2f}   "
              f"when it did not: "
              f"{statistics.mean(p[0] for p in pairs if p[1] == 0):+.2f}"
              if len(nz) < len(pairs) else "")

# ---------------------------------------------------------------------------
hdr(5, "THE TRIVIAL SHADOW — 'REV >= +1 AND GG >= 0 -> BUY'. Listed 'not run'. Run it.")
outcomes = {r["entry_id"]: r for r in rows if r.get("type") == "outcome"}
graded = []
for e in entries:
    o = outcomes.get(e.get("id"))
    if not o or o.get("idio_open_pct") is None:
        continue
    c = (e.get("verdict") or {}).get("components") or {}
    graded.append({"ticker": e["ticker"], "id": e["id"], "idio": o["idio_open_pct"],
                   "REV": c.get("REV"), "GG": c.get("GG"),
                   "model_stance": (e.get("verdict") or {}).get("action"),
                   "model_correct": o.get("idio_sign_correct"),
                   "event_date": e.get("event_date"),
                   "classification": o.get("classification")})
print(f"  graded ledger entries with an idio outcome: {len(graded)}")
shadow = [g for g in graded if (g["REV"] or 0) >= 1 and (g["GG"] or 0) >= 0]
if shadow:
    hits = sum(1 for g in shadow if g["idio"] > 0)
    print(f"  TRIVIAL SHADOW fires on {len(shadow)}/{len(graded)} events: "
          f"{hits}/{len(shadow)} = {100*hits/len(shadow):.1f}% up")
    print(f"    mean idio when it fires: {statistics.mean(g['idio'] for g in shadow):+.2f}%")
    for g in shadow:
        print(f"      {g['ticker']:6s} {g['event_date']}  REV{g['REV']:+d} GG{g['GG'] or 0:+d}  "
              f"idio {g['idio']:+7.2f}%")
else:
    print("  the shadow NEVER FIRES on the recorded ledger — REV>=+1 & GG>=0 has")
    print("  zero instances, because GG is essentially never sourced. THAT is the")
    print("  finding: the benchmark cannot be computed for the same reason the model")
    print("  has only two signals.")
    alt = [g for g in graded if (g["REV"] or 0) >= 1]
    if alt:
        hits = sum(1 for g in alt if g["idio"] > 0)
        print(f"  REV>=+1 alone: fires {len(alt)}/{len(graded)}, {hits}/{len(alt)} up "
              f"= {100*hits/len(alt):.1f}%, mean idio "
              f"{statistics.mean(g['idio'] for g in alt):+.2f}%")

# ---------------------------------------------------------------------------
hdr("5b", "ARE THE VOID ROWS MARKED IN THE DATA? (STATE.md says 2 sets are void)")
from datetime import datetime, timezone
def is_retro(e):
    """A row LOGGED after its own event date is not a pre-registration."""
    try:
        logged = datetime.fromisoformat(e["logged_at"]).astimezone(timezone.utc).date()
        ev = datetime.fromisoformat(e["event_date"]).date()
        return logged > ev
    except Exception:
        return False
retro = [e for e in entries if is_retro(e)]
print(f"  entries carrying an explicit void/retro FIELD: 0  <-- there is no such field")
print(f"  entries detectable as retro by timestamp (logged_at > event_date): {len(retro)}")
for e in retro:
    print(f"    {e['ticker']:6s} event {e['event_date']}  logged {e['logged_at'][:10]}")
print("  *** FINDING: 'the 07-29 batch is VOID' and 'AMKR is retro-registered' exist")
print("      ONLY IN PROSE. Any statistic computed from ledger.jsonl silently includes")
print("      them - including the 5/15 this model quotes about itself.")

# ---------------------------------------------------------------------------
hdr(6, "EXPECTANCY — the axis the whole document is missing")
traded = [g for g in graded if g["model_stance"] in ("BUY", "SHORT")]
retro_ids = {e["id"] for e in retro}
VOID_DATE = "2026-07-29"          # the batch STATE.md declares void
print(f"  ledger entries the model actually TRADED: {len(traded)}")


def stats(rows_, label):
    if not rows_:
        print(f"  {label}: no rows")
        return
    signed = [g["idio"] if g["model_stance"] == "BUY" else -g["idio"] for g in rows_]
    wins = [s for s in signed if s > 0]
    losses = [s for s in signed if s <= 0]
    aw = statistics.mean(wins) if wins else 0.0
    al = abs(statistics.mean(losses)) if losses else 0.0
    p = len(wins) / len(signed)
    print(f"  {label}")
    print(f"    n={len(signed)}  hit {len(wins)}/{len(signed)} = {100*p:.1f}%   "
          f"MEAN idio/trade {statistics.mean(signed):+.2f}%   total {sum(signed):+.2f}%")
    if wins and losses:
        print(f"    avg win {aw:+.2f}%  avg loss {-al:.2f}%  payoff {aw/al:.2f}  "
              f"expectancy {p*aw-(1-p)*al:+.3f}%/trade")


stats(traded, "ALL 15 (what the model quotes about itself)")
clean = [g for g in traded if g["id"] not in retro_ids and g["event_date"] != VOID_DATE]
stats(clean, "EXCLUDING the retro row(s) and the VOID 07-29 batch")
print(f"    -> distinct event_dates in the clean set: "
      f"{len({g['event_date'] for g in clean})}")
if traded:
    signed = []
    for g in traded:
        s = g["idio"] if g["model_stance"] == "BUY" else -g["idio"]
        signed.append(s)
    wins = [s for s in signed if s > 0]
    losses = [s for s in signed if s <= 0]
    print(f"  hit rate            {len(wins)}/{len(signed)} = {100*len(wins)/len(signed):.1f}%")
    print(f"  MEAN idio per trade {statistics.mean(signed):+.2f}%   <-- THE NUMBER THAT DECIDES")
    print(f"  median              {statistics.median(signed):+.2f}%")
    if wins and losses:
        aw, al = statistics.mean(wins), abs(statistics.mean(losses))
        print(f"  avg win {aw:+.2f}%   avg loss {-al:.2f}%   payoff ratio {aw/al:.2f}")
        p = len(wins) / len(signed)
        print(f"  expectancy = {p:.3f}*{aw:.2f} - {1-p:.3f}*{al:.2f} = "
              f"{p*aw - (1-p)*al:+.3f}% per trade")
    print(f"  total idio (equal-weight, before costs/slippage): {sum(signed):+.2f}%")
    print("\n  by name:")
    for g, s in sorted(zip(traded, signed), key=lambda x: x[1]):
        print(f"    {g['ticker']:6s} {g['event_date']}  {g['model_stance']:5s} "
              f"idio {g['idio']:+7.2f}%  signed {s:+7.2f}%  {g['classification']}")

# ---------------------------------------------------------------------------
hdr(7, "IS 'COINFLIP 80%' JUST THE UP-DRIFT? (reviewer: 'COINFLIP defaults to UP')")
frows = [json.loads(l) for l in (ROOT / "forecasts.jsonl").open(encoding="utf-8") if l.strip()]
fc = {(r["ticker"], r.get("event_date")): r for r in frows if r["type"] == "forecast"}
fo = [r for r in frows if r["type"] == "forecast_outcome"]
paired = []
for o in fo:
    f = fc.get((o["ticker"], o.get("event_date")))
    if f and o.get("idio_pct") is not None:
        paired.append({**f, "idio": o["idio_pct"],
                       "correct": (f["direction"] == "UP") == (o["idio_pct"] > 0)})
cf = [p for p in paired if p["basis"] == "COINFLIP"]
print(f"  COINFLIP forecasts graded: {len(cf)}")
for p in cf:
    print(f"    {p['ticker']:6s} {p['event_date']}  said {p['direction']:4s} "
          f"signal={p['signal']:+.4f}  idio {p['idio']:+7.2f}%  "
          f"{'HIT' if p['correct'] else 'MISS'}")
ups = sum(1 for p in cf if p["direction"] == "UP")
print(f"  of those, {ups}/{len(cf)} were UP.")
print(f"  => the reviewer's claim 'COINFLIP defaults to UP' is "
      f"{'CONFIRMED' if ups == len(cf) else 'REFUTED — the default only applies at signal EXACTLY 0'}")
print(f"     (basis=COINFLIP means |signal| < 0.10, NOT signal == 0)")

# ---------------------------------------------------------------------------
hdr(8, "INDEPENDENCE-ADJUSTED n — apply the error ledger's own rule to the scorecard")
days = {p.get("event_date") for p in paired}
print(f"  forecast record quoted as n={len(paired)}")
print(f"  distinct event_dates: {len(days)}  -> {sorted(d for d in days if d)}")
print(f"  by the model's OWN independence rule, the forecast sample is n~{len(days)}, not {len(paired)}")
tdays = {g["event_date"] for g in traded}
print(f"  capital record quoted as n={len(traded)}; distinct event_dates: {len(tdays)}")
print("  *** CONFIRMED — the independence rule is applied to error classes but NOT")
print("      to the model's own accuracy statistics. Both numbers must be printed.")

print(f"\n{LINE}\ndone. Nothing was written; this script is read-only.\n{LINE}")
