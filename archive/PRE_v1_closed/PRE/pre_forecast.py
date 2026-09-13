"""
PRE FORECAST layer — a directional call on EVERY name. It never abstains.
================================================================================
Built 2026-07-30 on owner instruction after the 07-29 post-mortem, where the model produced
7 NO_TRADEs across a night spanning -20.0% to +19.3% idio.

THE DIAGNOSIS THIS FIXES
The stack had ONE output answering TWO different questions:

    "what do I think will happen?"   -> a PREDICTION. Must always have an answer.
    "should I put money on it?"      -> a BET.        May legitimately say no.

Collapsing them meant that whenever the bet was unjustified the prediction vanished with it.
A prediction that is never made is never scored, and a model whose predictions are never
scored cannot improve — which is exactly why successive versions changed the verdicts and not
the outcomes. On a PAPER book, abstention protects nothing and teaches nothing; it is pure
cost. The trade gates stay exactly as they are (they exist to protect real capital later);
this layer runs alongside them and is graded on every single event.

THE CONTRACT
  * Emits UP or DOWN for every name. There is no NO_TRADE, no None, no abstention.
  * States an expected |move| and a CONVICTION so calls can be sorted by how much they claim.
  * Says which REGIME it thinks the name is in, so "when does a stock gap >5%?" becomes a
    question the accumulated log can actually answer.
  * Is logged to forecasts.jsonl — SEPARATE from ledger.jsonl, so the paper prediction record
    can never contaminate the capital track record.

WHAT IT USES THAT THE TRADE LAYER THROWS AWAY
The trade layer discards anything that cannot justify risking money. A forecast has no such
constraint, so it also reads:
  * the CONTINUOUS washout/extension distance, not the -15/+15 step. LRCX at -10.1 and ARM at
    +13.8 both scored ZERO positioning on 07-29 and then moved +19.3% and +8.2%. The step
    function threw away the fact that they were most of the way to the bar.
  * positioning/flow — put/call OI and short interest. Logged by the skew diagnostic for
    weeks and never allowed to say anything.
  * implied move as a MAGNITUDE expectation (never as a direction — that category error is
    already cut twice and is not coming back through this door).
  * a REV read even when C13 voided the feed for trading purposes: refusing to bet on a broken
    input is right, refusing to have an opinion because of it is not.

HONESTY CONSTRAINTS
  * Every forecast records `basis`: EVIDENCED (real signal), WEAK (thin), or COINFLIP (no
    information — the call is the base rate and is labelled as such). A coinflip dressed as a
    view is how a scorecard gets flattered.
  * The base rate is UP. Equities drift up and earnings announcements carry a positive average
    abnormal return; when there is genuinely nothing to say, that is the honest default.
  * NOTHING here feeds the trade verdict. It is a measurement instrument.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, time as _dtime
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Optional

__version__ = "1.0.0"

FORECAST_LOG = Path(__file__).with_name("forecasts.jsonl")

# Continuous positioning: the distance to the washout/extension bar, not the step at it.
# NORM is the existing -15/+15 trade bar reused as the scale, so this adds no new threshold.
WASH_NORM = 15.0
DD_MIN = 20.0                 # the existing drawdown condition for a true washout

# Conviction bands on |signal|. Labels only — they do not size anything.
CONV = [(0.50, "HIGH"), (0.25, "MEDIUM"), (0.10, "LOW"), (0.0, "COINFLIP")]

# Weights. PRIORS, deliberately close to the trade layer's 0.71/0.29 so the forecast is a
# fair test of the same thesis rather than a different model wearing the same name. `flow`
# is small because it has never been validated at all.
W_EXP, W_POS, W_FLOW = 0.55, 0.35, 0.10


@dataclass
class Forecast:
    ticker: str
    direction: str                  # UP | DOWN — never anything else
    conviction: str                 # HIGH | MEDIUM | LOW | COINFLIP
    basis: str                      # EVIDENCED | WEAK | COINFLIP
    signal: float                   # signed, unbounded by any dead-band
    expected_move: Optional[float]  # expected |gap| %
    regime: str
    drivers: list = field(default_factory=list)
    event_date: Optional[str] = None
    trade_stance: Optional[str] = None   # what the CAPITAL layer said, for comparison
    components: dict = field(default_factory=dict)
    # MUST STAY LAST. Forecast is constructed POSITIONALLY in forecast(), so a field
    # added anywhere above silently shifts `components` into whatever follows it --
    # which is exactly what this field did on its first attempt, caught by
    # tests/forecast_selftest.py 2a and not by any new test.
    session: str = "amc"                 # amc | bmo -- sets the cutoff it is graded against


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def forecast(ticker, *, expectations=0.0, excess=None, dd=None, rev_raw=None,
             implied_move=None, avg_gap=None, bad_gap=None, put_call=None,
             short_interest=None, event_date=None, trade_stance=None,
             gg=None, vel=None) -> Forecast:
    """Always returns a direction. See the module docstring for what that promises."""
    drivers, comps = [], {}

    # --- A. expectations (same fundamentals the trade layer uses) ----------------
    exp = float(expectations or 0.0)
    comps["expectations"] = round(exp, 3)
    if exp:
        drivers.append(f"expectations {exp:+.2f}"
                       + (f" (GG {gg:+d})" if gg else "")
                       + (f" (VEL {vel:+d})" if vel else ""))

    # --- B. positioning, CONTINUOUS ---------------------------------------------
    # The trade layer's step function scored LRCX (-10.1) and ARM (+13.8) as exactly ZERO on
    # 07-29. Both were most of the way to a bar and both then moved hard. A forecast has no
    # reason to discard that distance.
    pos = 0.0
    if excess is not None:
        pos = _clamp(-excess / WASH_NORM, -1.0, 1.0)     # washed => positive (mean-reversion up)
        if dd is not None and dd < DD_MIN and pos > 0:
            pos *= 0.5                                    # not actually beaten down; halve it
            drivers.append(f"washed vs sector but only {dd:.0f}% off high — halved")
        if abs(excess) >= 5:
            drivers.append(f"{'washed' if excess < 0 else 'extended'} {excess:+.1f}pts vs sector"
                           + (" (below the +/-15 trade bar)" if abs(excess) < 15 else ""))
    comps["positioning"] = round(pos, 3)

    # --- C. flow (logged for weeks, never allowed to speak) ----------------------
    flow = 0.0
    if put_call is not None:
        # Crowded puts into a print skew the reaction upward when the feared outcome misses.
        if put_call >= 2.0:
            flow += 0.5; drivers.append(f"put/call OI {put_call:.1f} — heavily hedged downside")
        elif put_call <= 0.5:
            flow -= 0.25; drivers.append(f"put/call OI {put_call:.2f} — call-crowded")
    if short_interest is not None and short_interest >= 10.0:
        flow += 0.5; drivers.append(f"short interest {short_interest:.0f}% of float — squeeze fuel")
    flow = _clamp(flow, -1.0, 1.0)
    comps["flow"] = round(flow, 3)

    # --- D. a REV read even when C13 voided it for TRADING -----------------------
    # Refusing to BET on a broken feed is right. Refusing to have an OPINION because of it is
    # what made MSFT silent into a +11.5% move.
    if rev_raw is not None and not exp:
        comps["rev_fallback"] = round(rev_raw, 3)
        drivers.append(f"REV feed unusable for trading; direction-only read {rev_raw:+.2f}")
        exp = rev_raw * 0.5

    signal = W_EXP * exp + W_POS * pos + W_FLOW * flow

    # --- direction: NEVER abstain ------------------------------------------------
    if signal > 0:
        direction = "UP"
    elif signal < 0:
        direction = "DOWN"
    else:
        direction = "UP"
        drivers.append("no signal at all — defaulting to the positive base rate "
                       "(drift + announcement premium), labelled COINFLIP")

    mag = abs(signal)
    conviction = next(name for lo, name in CONV if mag >= lo)
    basis = ("EVIDENCED" if mag >= 0.25 else "WEAK" if mag >= 0.10 else "COINFLIP")

    # --- expected magnitude ------------------------------------------------------
    # implied_move is the market's own magnitude estimate; the name's own bad case bounds it.
    # Used ONLY for size of move, never for its sign.
    cands = [x for x in (implied_move, avg_gap) if x]
    expected = round(sum(cands) / len(cands), 2) if cands else (bad_gap or None)

    # --- regime label: this is what makes the log answerable ---------------------
    hi_move = (expected or 0) >= 5.0
    if excess is None:
        reg = "UNKNOWN"
    elif excess <= -15:
        reg = "WASHED"
    elif excess >= 15:
        reg = "EXTENDED"
    elif excess <= -5:
        reg = "SOFT"
    elif excess >= 5:
        reg = "FIRM"
    else:
        reg = "NEUTRAL"
    regime = f"{reg}/{'HIGH_MOVE' if hi_move else 'LOW_MOVE'}"

    # LEG PROVENANCE. `expectations` is a NET number: the same -0.50 can come from REV
    # alone, from GG alone, or from a mix, and the row could not say which. rev_raw/gg/vel
    # are accepted by this function and reached only the driver STRING, so all three were
    # None on every one of the 28 rows written before 2026-09-12. That made Abstraction
    # Test limb 2 - "which previous winners would this fix break?" - UNANSWERABLE for any
    # single-leg change, which is exactly what rev-leg-points-against-the-print went RIPE
    # (3/3: PLAB, AVGO, CPRT) asking for. The trade layer already fixed its own version of
    # this by persisting fund_leg_sum / fund_norm / verified_legs so a row stays
    # re-derivable under any future norm; the forecast layer never got that plumbing and is
    # now the ONLY layer still accruing a record.
    # This MOVES NOTHING: no signal, no direction, no conviction, no label, no threshold.
    # It lives inside `components` rather than as a dataclass field because Forecast is
    # constructed POSITIONALLY and a new field silently shifts `components` (see the note
    # on `session`). It cannot repair the 28 rows already written - that gap is permanent.
    comps["rev_raw"] = rev_raw
    comps["gg"] = gg
    comps["vel"] = vel
    # MAGNITUDE PROVENANCE, added 2026-09-13 on external-review finding C3.
    # `expected_move` above is mean(implied_move, avg_gap), so where both exist
    #     expected_move - implied_move == (avg_gap - implied_move) / 2
    # identically: it is the option market's own forecast shrunk halfway toward the
    # name's gap history. A correlation between expected_move and |idio| is therefore
    # INHERITED from the market unless the components are separable, and they were not:
    # none of the three was stored, so "does this beat the implied move?" - the only
    # question the magnitude output can answer - was unanswerable from this log.
    # Storing the inputs, not just the blend, is what makes that testable from event 1.
    # NOTE the 27 rows written before today cannot be repaired: implied_move at T-1 is
    # not retrievable after the fact. 9 of them are recoverable by joining
    # ledger.jsonl `inputs.market.implied_move` on (ticker, event_date); the rest are
    # permanently gone. Recomputing avg_gap today would use prints that postdate the
    # event, so backfilling it here would inject look-ahead. Do not.
    comps["implied_move"] = implied_move
    comps["avg_gap"] = avg_gap
    comps["bad_gap"] = bad_gap

    return Forecast(ticker, direction, conviction, basis, round(signal, 4), expected,
                    regime, drivers, event_date, trade_stance, comps)


_CUTOFF = {"amc": _dtime(16, 0), "bmo": _dtime(9, 30)}
_ET = ZoneInfo("America/New_York")


def _cutoff_utc(event_date, session):
    """The instant after which a call about this event is hindsight, not a forecast.

    Deliberately a COPY of pre_batch.cutoff_utc rather than an import: pre_batch imports
    this module, so importing back would be circular. Resolved in exchange time via
    zoneinfo, so DST is handled rather than assumed.
    """
    try:
        d = datetime.strptime(event_date, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None
    return datetime.combine(d, _CUTOFF.get(session, _CUTOFF["amc"]),
                            tzinfo=_ET).astimezone(timezone.utc)


def log_forecast(f: Forecast, path: Path = FORECAST_LOG) -> dict:
    """Append a forecast. IDEMPOTENT on (ticker, event_date).

    A batch is normally run dry first and then again with --register, and both passes log.
    Without this guard the same call is written twice, which inflates the apparent sample.
    Re-running with CHANGED inputs is a different matter and is refused loudly rather than
    silently overwritten — a pre-registration that can be edited is not a pre-registration.
    """
    from pre_closed import assert_open
    assert_open(path, FORECAST_LOG)
    _now = datetime.now(timezone.utc)
    rec = {"type": "forecast", "logged_at": _now.isoformat(),
           "layer_version": __version__, **asdict(f)}
    # THE FORECAST LAYER WAS NEVER CLOCK-GUARDED. --register is refused after the cutoff,
    # but a DRY run past it printed a warning and logged the row anyway, unmarked. The
    # clock guard's own docstring says "label it VOID" -- and nothing labelled it. That is
    # void-status-in-prose-only, the first of the three defects tests/controls_fire_selftest
    # exists for, recurring a fourth time. It matters MORE here than on the trade layer:
    # the trade layer is PAUSED, so this is the only layer still accruing a record, and
    # score() is the statistic the open questions turn on. Audited 2026-09-05: 0 of 23
    # existing rows are post-cutoff, so stamping is a NO-OP on the record as it stands --
    # which is exactly when a guard should be wired.
    _cut = _cutoff_utc(f.event_date, f.session) if f.event_date else None
    if _cut is not None:
        rec["minutes_before_cutoff"] = int((_cut - _now).total_seconds() // 60)
        rec["post_cutoff"] = _now >= _cut
        rec["cutoff_session"] = f.session
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        for line in path.open(encoding="utf-8"):
            if not line.strip():
                continue
            r = json.loads(line)
            if (r.get("type") == "forecast" and r.get("ticker") == f.ticker
                    and r.get("event_date") == f.event_date):
                if (r.get("direction"), r.get("signal")) != (f.direction, f.signal):
                    raise ValueError(
                        f"REFUSED: {f.ticker} @ {f.event_date} is already forecast "
                        f"{r.get('direction')} signal={r.get('signal')}, and this run says "
                        f"{f.direction} signal={f.signal}. A frozen call cannot be revised — "
                        f"log the disagreement as a new event or leave it alone.")
                return r        # identical re-run: already recorded, nothing to do
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, default=str) + "\n")
    return rec


def log_outcome(ticker, event_date, idio_pct, path: Path = FORECAST_LOG,
                backfill: bool = False, source: str = "",
                backfill_reason: str = "") -> dict:
    """Record what actually happened, so a forecast can be graded.

    `backfill=True` marks an outcome logged LATE — days or weeks after the event —
    rather than in the normal next-day pass. It is never a synonym for "wrong": the
    outcome is public either way and the forecast was sealed before it. But a record
    that hides its own gaps is more trusted than it deserves to be, and this layer
    had 14 forecasts and ZERO outcomes for ten days without anything saying so.
    `source` names where the number came from (a ledger outcome id, or a fresh fetch).
    """
    from pre_closed import assert_open
    assert_open(path, FORECAST_LOG)
    rec = {"type": "forecast_outcome", "ticker": ticker, "event_date": event_date,
           "idio_pct": idio_pct,
           "logged_at": datetime.now(timezone.utc).isoformat()}
    if backfill:
        rec["backfill"] = True
        rec["backfill_reason"] = backfill_reason or (
            "logged late; the layer was never scored between 07-30 and 08-09")
    if source:
        rec["source"] = source
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, default=str) + "\n")
    return rec


def score(path: Path = FORECAST_LOG) -> dict:
    """Directional accuracy, sliced by conviction, basis and regime.

    The slices are the point: the standing question is 'in what circumstances does a name gap
    hard, and which way?'. That is answerable only once every event carries a labelled call.
    """
    if not Path(path).exists():
        return {"n": 0}
    rows = [json.loads(l) for l in Path(path).open(encoding="utf-8") if l.strip()]
    # A row stamped post_cutoff was written AFTER its own print: hindsight, not a forecast.
    # It is EXCLUDED from every statistic rather than deleted -- same treatment as the VOID
    # ledger rows, and for the same reason: the record must show its own gaps. A stamp that
    # nothing filters on is decoration, which is how void-status-in-prose-only survived
    # three rounds. Rows predating the stamp carry no key and are kept (audited clean).
    voided = [r for r in rows if r["type"] == "forecast" and r.get("post_cutoff") is True]
    fc = {(r["ticker"], r.get("event_date")): r for r in rows
          if r["type"] == "forecast" and r.get("post_cutoff") is not True}
    out = [r for r in rows if r["type"] == "forecast_outcome"]
    paired = []
    for o in out:
        f = fc.get((o["ticker"], o.get("event_date")))
        if not f or o.get("idio_pct") is None:
            continue
        correct = (f["direction"] == "UP") == (o["idio_pct"] > 0)
        paired.append({**f, "idio_pct": o["idio_pct"], "correct": correct,
                       "big": abs(o["idio_pct"]) >= 5.0})
    if not paired:
        # the all-excluded case is exactly when the exclusion MUST be visible: a bare n=0
        # reads as "nothing logged yet" when the truth may be "everything was hindsight".
        return {"n": 0, "logged": len(fc), "excluded_post_cutoff": len(voided)}

    def acc(rows_):
        return (round(100 * sum(r["correct"] for r in rows_) / len(rows_), 1), len(rows_))

    by = lambda key: {v: acc([r for r in paired if r[key] == v])
                      for v in sorted({r[key] for r in paired})}
    return {"n": len(paired), "overall": acc(paired),
            "excluded_post_cutoff": len(voided),
            "by_conviction": by("conviction"), "by_basis": by("basis"),
            "by_regime": by("regime"),
            "excl_coinflip": acc([r for r in paired if r["basis"] != "COINFLIP"]) or None,
            "big_movers": acc([r for r in paired if r["big"]]) if any(r["big"] for r in paired) else None}


def render(f: Forecast) -> str:
    L = [f"{f.ticker:6s} {f.direction:4s} {f.conviction:9s} [{f.basis}] "
         f"signal={f.signal:+.3f}  expect ~{f.expected_move or float('nan'):.1f}%  {f.regime}"
         + (f"   (trade layer: {f.trade_stance})" if f.trade_stance else "")]
    for d in f.drivers:
        L.append(f"       - {d}")
    return "\n".join(L)
