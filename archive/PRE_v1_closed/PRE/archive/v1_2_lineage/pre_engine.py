"""
PRE v1.2 — Deterministic Engine (SEALED CORE)
All gate arithmetic, scoring, sizing, logging, post-mortem, and monitoring.
v1.2 adds the CANONICAL SAT(a) REV-gate (cases ACN + MU, Type B regime-blindness).

SEALED CORE (this file): gates G1/G2/G3-window/G4, SAT(a) excess-PED + REV-gate,
SAT(b) 52W math, DS sum+clamp+conviction, sizing+dampers+caps, IRM, decision
cascade, frozen pre-registration log, post-mortem idio math, accuracy/kill-switch.

Judgment inputs (G0, GG, CBR-PRE, VEL, REV, FLAG, SAT sector-ETF, REACT) are
passed IN as named RAW arguments. The engine NEVER fetches or guesses them — a
missing input scores 0 and is flagged UNAVAILABLE; gates fail closed.
"""

import json
import time
import hashlib
import datetime as dt
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

__version__ = "1.2.2"  # see docs/patch_log.md for the autopatch ledger

LOG_PATH = Path(__file__).parent / "log.jsonl"

# Independent price sources accepted for post-mortem (spec: named independent)
NAMED_INDEPENDENT_SOURCES = {"yfinance", "Polygon", "IEX official"}

# ─── Component helpers ────────────────────────────────────────────

def score_rev(up: int, down: int, covering: int) -> tuple[int, str]:
    if covering <= 0:
        return 0, "UNAVAILABLE"
    r = (up - down) / covering
    if r >= 0.30:
        s = 2
    elif r >= 0.10:
        s = 1
    elif r > -0.10:
        s = 0
    elif r > -0.30:
        s = -1
    else:
        s = -2
    return s, f"R={r:+.3f}"


def score_gg(gg: Optional[int]) -> tuple[int, str]:
    if gg is None:
        return 0, "UNAVAILABLE"
    return int(gg), f"GG={gg:+d}"


def score_vel(vel: Optional[int]) -> tuple[int, str]:
    if vel is None:
        return 0, "UNAVAILABLE"
    return int(vel), f"VEL={vel:+d}"


def score_sat(stock_pct: float, sector_pct: float,
              near_52w_high_pct: float, below_52w_high_pct: float,
              rev_score: int, vel_score: int = 0,
              inflection_override: bool = False) -> tuple[int, str, int, int]:
    """SAT = (a) excess-PED (with v1.2 REV-gate) + (b) 52W, clamp [-2,+2].

    REV-GATE (v1.2 CANONICAL): SAT(a)'s ±1 fires ONLY when its implied
    direction agrees with the sign of REV.
      - the −1 (saturation) requires REV < 0
      - the +1 (vacuum)     requires REV > 0
    If excess-PED contradicts REV's sign, or REV = 0 / unverified → (a) = 0.
    [Failure cases that motivated this: ACN, MU — Type B regime-blindness.]

    FUNDAMENTAL-INFLECTION OVERRIDE (WATCH, default OFF — cases AVAV vs NKE):
    When `inflection_override` is on AND VEL ≥ +1 (operating KPI accelerating)
    AND the name is deeply beaten (>25% below 52W high), a lagging-negative REV
    no longer vetoes the vacuum/cheapness signal — the accelerating KPI confirms
    it is inflecting, not a value trap. NKE (VEL 0) is unaffected; AVAV (VEL +1)
    is promoted. Default OFF keeps canonical scoring byte-identical.
    """
    excess = stock_pct - sector_pct
    deeply_beaten = below_52w_high_pct > 25.0
    infl = inflection_override and vel_score >= 1 and deeply_beaten

    # (a) raw excess-PED bucket, then the REV-gate.
    if excess >= 20.0:
        implied_a = -1
        if rev_score < 0:
            a = -1
            gate = "REV<0 agrees → −1 applies"
        else:
            a = 0
            gate = f"REV-gate BLOCKS −1 (REV={rev_score:+d} not <0)"
    elif excess <= -10.0:
        implied_a = 1
        if rev_score > 0:
            a = 1
            gate = "REV>0 agrees → +1 applies"
        elif infl:
            a = 1
            gate = f"INFLECTION override (VEL={vel_score:+d}≥+1) → +1 despite REV"
        else:
            a = 0
            gate = f"REV-gate BLOCKS +1 (REV={rev_score:+d} not >0)"
    else:
        implied_a = 0
        a = 0
        gate = "neutral band"

    # (b) 52-week math with falling-knife guard.
    if near_52w_high_pct <= 5.0:
        b = -1
    elif deeply_beaten:
        if rev_score >= 0:
            b = 1
        elif infl:
            b = 1  # accelerating KPI substitutes for the R≥0 confirmation
        else:
            b = 0  # falling-knife guard (unverified/negative R → 0)
    else:
        b = 0

    raw = a + b
    sat = max(-2, min(2, raw))
    detail = (f"SAT(a)={a:+d} [excess={excess:+.1f}% implied {implied_a:+d}, "
              f"{gate}] SAT(b)={b:+d} → clamped {sat:+d}")
    return sat, detail, a, b


def score_react(react: Optional[int]) -> tuple[int, str]:
    if react is None:
        return 0, "UNAVAILABLE"
    return int(react), f"REACT={react:+d}"


def score_flag(flag: Optional[int]) -> tuple[int, str]:
    if flag is None:
        return 0, "UNAVAILABLE"
    capped = max(-2, min(0, int(flag)))
    return capped, f"FLAG={capped:d}"


# ─── Gates ────────────────────────────────────────────────────────

def check_g1(avg_dollar_vol_20d: float, position_shares: int,
             avg_share_vol_20d: float) -> tuple[bool, str]:
    liq = avg_dollar_vol_20d >= 25_000_000
    pct = (position_shares / avg_share_vol_20d * 100) if avg_share_vol_20d > 0 else 999
    size_ok = pct <= 1.0
    passed = liq and size_ok
    return passed, f"G1 dvol=${avg_dollar_vol_20d/1e6:.1f}M pos%={pct:.2f}% → {'PASS' if passed else 'FAIL'}"


def check_g2(avg_abs_open: float, confirmed_quarters: int) -> tuple[bool, bool, str]:
    gap_ok = avg_abs_open >= 2.0
    estimated = confirmed_quarters < 4
    passed = gap_ok
    tag = "ESTIMATED" if estimated else "CONFIRMED"
    return passed, estimated, f"G2 gap={avg_abs_open:.2f}% qtrs={confirmed_quarters} [{tag}] → {'PASS' if passed else 'FAIL'}"


def check_g3(macro_overlap: bool) -> tuple[bool, float, str]:
    damper = 0.5 if macro_overlap else 1.0
    return True, damper, f"G3 overlap={'YES ×0.5' if macro_overlap else 'NO'}"


def check_g4(borrow_confirmed: Optional[bool], fee_annualized: Optional[float]) -> tuple[bool, str]:
    if borrow_confirmed is None:
        return False, "G4 FAIL (unknown locate)"
    if not borrow_confirmed:
        return False, "G4 FAIL (not located)"
    if fee_annualized is not None and fee_annualized > 5.0:
        return False, f"G4 FAIL (fee {fee_annualized:.1f}% > 5%)"
    return True, "G4 PASS"


# ─── CBR-PRE ──────────────────────────────────────────────────────

def evaluate_cbr(c1: Optional[bool], c2: Optional[bool], c3: Optional[bool]) -> tuple[str, str]:
    vals = [c1, c2, c3]
    if any(v is None for v in vals):
        return "MANUFACTURED", "CBR UNSURE (missing data) → treated as MANUFACTURED"
    if all(vals):
        return "CLEAN", "CBR CLEAN (3/3)"
    fails = []
    for name, v in [("C1", c1), ("C2", c2), ("C3", c3)]:
        if not v:
            fails.append(name)
    return "MANUFACTURED", f"CBR MANUFACTURED ({','.join(fails)} FAIL)"


# ─── IRM ──────────────────────────────────────────────────────────

def calc_irm(implied_move: float, avg_abs_open: float) -> tuple[float, str]:
    if avg_abs_open == 0:
        return 0.0, "IRM=N/A (avg_abs_open=0)"
    irm = implied_move / avg_abs_open
    return irm, f"IRM={irm:.2f} (impl={implied_move:.2f}% / gap={avg_abs_open:.2f}%)"


# ─── Sizing ───────────────────────────────────────────────────────

def compute_sizing(capital: float, avg_abs_open: float, price: float,
                   conviction: str, g3_damper: float,
                   vix: Optional[float], spy_vol_wow: Optional[float],
                   spx_day_pct: Optional[float]) -> dict:
    if avg_abs_open <= 0 or price <= 0:
        return {"units": 0.0, "shares": 0, "dampers": ["invalid inputs"]}

    base_unit_shares = (0.005 * capital) / (avg_abs_open / 100.0 * price)

    if conviction == "HIGH":
        raw_units = 1.5
    else:
        raw_units = 1.0

    dampers = []
    mult = g3_damper
    if g3_damper < 1.0:
        dampers.append("G3 ×0.5")

    vol_damper = False
    if vix is not None and vix > 28:
        vol_damper = True
        dampers.append(f"VIX={vix:.1f}>28")
    if spy_vol_wow is not None and spy_vol_wow > 50:
        vol_damper = True
        dampers.append(f"SPY 5d vol +{spy_vol_wow:.0f}% WoW")
    if spx_day_pct is not None and abs(spx_day_pct) > 1.5:
        vol_damper = True
        dampers.append(f"SPX day {spx_day_pct:+.1f}%")
    if vol_damper:
        mult *= 0.5

    final_units = raw_units * mult
    final_shares = int(base_unit_shares * final_units)

    return {
        "base_unit_shares": int(base_unit_shares),
        "raw_units": raw_units,
        "damper_mult": mult,
        "final_units": round(final_units, 4),
        "shares": final_shares,
        "dampers": dampers if dampers else ["None"],
    }


# ─── Cap checks (informational — caller enforces) ────────────────

def check_caps(final_units: float, weekly_gross: float, weekly_net: float,
               concurrent: int, sector_count: int) -> list[str]:
    warnings = []
    if weekly_gross + final_units > 6.0:
        warnings.append(f"WEEKLY GROSS {weekly_gross + final_units:.1f} > 6.0")
    if abs(weekly_net + final_units) > 4.0:
        warnings.append(f"WEEKLY NET {abs(weekly_net + final_units):.1f} > 4.0")
    if concurrent + 1 > 5:
        warnings.append(f"CONCURRENT {concurrent + 1} > 5")
    if sector_count + 1 > 2:
        warnings.append(f"SECTOR {sector_count + 1} > 2")
    return warnings


# ─── Decision cascade ────────────────────────────────────────────

# Reachable range of each judgment component that can be UNAVAILABLE (scored 0).
# Used for the worst-case flip test: an unavailable input could legitimately
# take any value in its range, so a verdict that an unavailable input could
# erase is INCOMPLETE, not a trade. (audit fix #B1, fail-closed)
UNAVAIL_RANGE = {"GG": (-1, 1), "VEL": (-1, 1), "REACT": (-1, 1), "FLAG": (-2, 0)}


def decide(ds: int, gates_passed: bool, cbr_verdict: str,
           g4_passed: bool, unavailable: Optional[list] = None,
           g0_status: Optional[str] = "CONFIRMED") -> tuple[str, str, str]:
    unavailable = unavailable or []
    # G0 fail-closed: missing/unresolved date blocks; out-of-window → DRY RUN.
    if g0_status is None:
        return "NO TRADE", "G0 UNAVAILABLE → fail closed", "NONE"
    if g0_status == "UNRESOLVED":
        return "NO TRADE", "G0 sources disagree → unresolved", "NONE"
    if g0_status == "DRY_RUN":
        return "DRY RUN", "G0 not T−1 → out of window", "NONE"

    if not gates_passed:
        return "NO TRADE", "Gate failure", "NONE"

    conviction = "HIGH" if abs(ds) >= 5 else ("MEDIUM" if abs(ds) >= 3 else "NONE")

    # Worst-case DS if every unavailable input took its most adverse value.
    ds_floor = ds + sum(UNAVAIL_RANGE.get(c, (0, 0))[0] for c in unavailable)
    ds_ceil = ds + sum(UNAVAIL_RANGE.get(c, (0, 0))[1] for c in unavailable)

    if ds >= 3 and cbr_verdict == "CLEAN":
        if unavailable and ds_floor < 3:
            return ("INCOMPLETE",
                    f"DS={ds:+d} but unavailable {unavailable} could drop it to {ds_floor:+d} (<+3)",
                    "NONE")
        return "BUY SHARES", f"DS={ds:+d} ≥ +3, CBR CLEAN", conviction
    if ds >= 3 and cbr_verdict != "CLEAN":
        return "NO TRADE", f"DS={ds:+d} ≥ +3 but CBR {cbr_verdict} → long blocked", conviction
    if ds <= -3 and g4_passed:
        if unavailable and ds_ceil > -3:
            return ("INCOMPLETE",
                    f"DS={ds:+d} but unavailable {unavailable} could lift it to {ds_ceil:+d} (>−3)",
                    "NONE")
        return "SHORT SHARES", f"DS={ds:+d} ≤ −3, G4 PASS", conviction
    if ds <= -3 and not g4_passed:
        return "NO TRADE", f"DS={ds:+d} ≤ −3 but G4 FAIL → short blocked", conviction

    # In-band: INCOMPLETE only if an unavailable input could actually reach a
    # trade band (±3); otherwise it is a genuine NO TRADE.
    if unavailable and (ds_floor <= -3 or ds_ceil >= 3):
        return ("INCOMPLETE",
                f"DS={ds:+d} in band but unavailable {unavailable} could reach "
                f"[{ds_floor:+d},{ds_ceil:+d}]", "NONE")

    return "NO TRADE", f"DS={ds:+d} inside ±3 band", "NONE"


# ─── Post-mortem idio math ────────────────────────────────────────

def post_mortem_idio(stock_open_pct: float, sector_etf_open_pct: float,
                     direction: str) -> dict:
    idio = stock_open_pct - sector_etf_open_pct
    if direction == "BUY SHARES":
        correct = idio > 0
    elif direction == "SHORT SHARES":
        correct = idio < 0
    else:
        correct = None
    return {
        "stock_open_pct": round(stock_open_pct, 4),
        "sector_etf_open_pct": round(sector_etf_open_pct, 4),
        "idio_open_pct": round(idio, 4),
        "direction_correct": correct,
    }


# ─── Accuracy + kill-switch monitor ──────────────────────────────

def monitor_accuracy(log_path: Path = LOG_PATH) -> dict:
    """All three spec kill switches over the log:
      - idio accuracy <50% @ n≥15 → PAUSE
      - Type-B >2/10 → recalibrate SAT
      - any component standalone hit <50% @ n_nonzero≥20 → ablation candidate
    ANOMALY-classified outcomes are isolated: they never drive these stats
    (model coefficients are frozen against exogenous noise)."""
    if not log_path.exists():
        return {"n": 0, "message": "No log data"}

    preregs, postmortems = [], []
    for line in log_path.read_text().splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        rt = e.get("record_type")
        if rt == "prereg":
            preregs.append(e)
        elif rt == "postmortem" and e.get("idio_sign_correct") is not None:
            postmortems.append(e)

    # Isolate anomalies — frozen, never tune the model.
    n_anomaly = sum(1 for e in postmortems if e.get("classification") == "ANOMALY")
    entries = [e for e in postmortems if e.get("classification") != "ANOMALY"]

    n = len(entries)
    if n == 0:
        return {"n": 0, "anomalies_isolated": n_anomaly, "message": "No scored post-mortems"}

    correct = sum(1 for e in entries if e["idio_sign_correct"])
    accuracy = correct / n
    result: dict = {"n": n, "correct": correct, "accuracy": round(accuracy, 4),
                    "anomalies_isolated": n_anomaly}

    if n >= 15 and accuracy < 0.50:
        result["kill_switch"] = "PAUSE: idio accuracy <50% at n≥15"

    recent = entries[-10:]
    type_b = sum(1 for e in recent if e.get("taxonomy") == "B")
    if type_b > 2:
        result["recalibrate"] = f"Type B {type_b}/10 → recalibrate SAT"

    # Component ablation (audit fix #C3): join postmortems to their prereg by
    # ticker+earnings_date and test each component's standalone idio-sign hit.
    prereg_by_key = {(p.get("ticker"), p.get("earnings_date")): p for p in preregs}
    for comp in COMPONENTS:
        nz = 0; hits = 0
        for e in entries:
            pre = prereg_by_key.get((e.get("ticker"), e.get("earnings_date")))
            if pre is None:
                continue
            sc = (pre.get("components", {}).get(comp) or {}).get("score")
            if not sc:
                continue
            nz += 1
            if _sign(sc) == _sign(e["idio_open_pct"]):
                hits += 1
        if nz >= 20 and hits / nz < 0.50:
            result.setdefault("ablation_candidates", []).append(
                f"{comp}: standalone hit {hits}/{nz}={hits/nz:.0%} <50% @ n≥20")

    return result


# ─── Logging layer (append-only log.jsonl, two record_types) ─────
#
# Schema per PRE_review_mode_spec.md LOG SCHEMA.
#   prereg     — written at entry, frozen, carries integrity_hash
#   postmortem — written after exit, keyed to prereg by ticker+earnings_date
#
# The six required components, each with raw value(s), score, and source.
REQUIRED_COMPONENTS = ("REV", "GG", "VEL", "SAT", "REACT", "FLAG")


class PreregValidationError(Exception):
    """Raised when a prereg is missing a component, source, or timestamp."""


def compute_integrity_hash(frozen: dict) -> str:
    """SHA-256 over all frozen fields in canonical (sorted-key) JSON form.

    The hash field itself is excluded so the digest can be recomputed and
    compared on load. Any later mutation of a frozen field changes the digest.
    """
    payload = {k: v for k, v in frozen.items() if k != "integrity_hash"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_prereg(record: dict) -> None:
    """Fail-closed: refuse any prereg missing a component, source, or timestamp."""
    if not record.get("ts"):
        raise PreregValidationError("prereg missing timestamp (ts)")
    if not record.get("ticker"):
        raise PreregValidationError("prereg missing ticker")
    if not record.get("earnings_date"):
        raise PreregValidationError("prereg missing earnings_date")

    components = record.get("components")
    if not isinstance(components, dict):
        raise PreregValidationError("prereg missing components block")

    for name in REQUIRED_COMPONENTS:
        comp = components.get(name)
        if not isinstance(comp, dict):
            raise PreregValidationError(f"prereg missing component {name}")
        if "score" not in comp:
            raise PreregValidationError(f"component {name} missing score")
        # SAT carries raw_a/raw_b; the rest carry raw.
        if name == "SAT":
            if "raw_a" not in comp or "raw_b" not in comp:
                raise PreregValidationError("component SAT missing raw_a/raw_b")
        elif "raw" not in comp:
            raise PreregValidationError(f"component {name} missing raw")
        if not comp.get("source"):
            raise PreregValidationError(f"component {name} missing source")


def write_prereg(*, ticker: str, earnings_date: str, session: str,
                 price: float, sector_etf: str, components: dict,
                 ds: int, direction: str, conviction: str,
                 avg_abs_open: float, irm: float, units: float, shares: int,
                 gates: dict, regime: dict,
                 log_path: Path = LOG_PATH) -> dict:
    """Build, validate, hash, and append a frozen prereg record.

    `components` must be a dict mapping each of REV/GG/VEL/SAT/REACT/FLAG to a
    sub-dict with raw value(s), score, and source. Missing any → refuse.
    """
    record = {
        "record_type": "prereg",
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "ticker": ticker,
        "earnings_date": earnings_date,
        "session": session,
        "price": price,
        "sector_etf": sector_etf,
        "components": components,
        "DS": ds,
        "direction": direction,
        "conviction": conviction,
        "avg_abs_open": avg_abs_open,
        "IRM": irm,
        "units": units,
        "shares": shares,
        "gates": gates,
        "regime": regime,
    }

    _validate_prereg(record)                       # refuse before hashing
    record["integrity_hash"] = compute_integrity_hash(record)

    with open(log_path, "a") as f:
        f.write(json.dumps(record) + "\n")
    return record


def _fetch_open_pct(ticker: str, on_date: str) -> tuple[float, str]:
    """Return (open%, source) for the reaction-day session via yfinance.

    open% is the session's open relative to the prior session's close, the
    overnight gap that the model trades. Raises on missing data — the engine
    never invents a price.
    """
    import yfinance as yf

    start = (dt.date.fromisoformat(on_date) - dt.timedelta(days=7)).isoformat()
    end = (dt.date.fromisoformat(on_date) + dt.timedelta(days=3)).isoformat()
    hist = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=False)
    if hist.empty:
        raise ValueError(f"yfinance returned no data for {ticker} around {on_date}")

    hist = hist.reset_index()
    hist["d"] = hist["Date"].dt.date.astype(str)
    idx = hist.index[hist["d"] == on_date]
    if len(idx) == 0:
        raise ValueError(f"yfinance has no session for {ticker} on {on_date}")
    i = idx[0]
    if i == 0:
        raise ValueError(f"no prior-close available for {ticker} before {on_date}")

    prev_close = float(hist.loc[i - 1, "Close"])
    today_open = float(hist.loc[i, "Open"])
    open_pct = (today_open / prev_close - 1.0) * 100.0
    return open_pct, "yfinance"


def write_postmortem(*, ticker: str, earnings_date: str, reaction_date: str,
                     sector_etf: str, direction: str,
                     stock_open_pct: Optional[float] = None,
                     etf_open_pct: Optional[float] = None,
                     price_source: Optional[str] = None,
                     raw_pnl: Optional[float] = None,
                     taxonomy: Optional[str] = None,
                     classification: str = "NORMAL",
                     postprint_cbr: Optional[dict] = None,
                     log_path: Path = LOG_PATH) -> dict:
    """Compute idio_open% from independent open prices and append a postmortem.

    If stock_open_pct / etf_open_pct are not supplied, they are pulled live from
    yfinance for `reaction_date`. Keyed to its prereg by ticker + earnings_date.
    idio_open% = stock open% − sector ETF open%; idio_sign_correct compares the
    realized idio SIGN against the traded direction.

    classification: "NORMAL" or "ANOMALY". ANOMALY (verified exogenous shock —
    surprise CEO exit, litigation/raid, geopolitical shock) FREEZES the model:
    the outcome is logged but never drives accuracy / Type-B / ablation stats,
    so exogenous variance cannot distort the sustainable core.
    """
    if classification not in ("NORMAL", "ANOMALY"):
        raise ValueError("classification must be NORMAL or ANOMALY")
    if stock_open_pct is None or etf_open_pct is None:
        stock_open_pct, src = _fetch_open_pct(ticker, reaction_date)
        etf_open_pct, _ = _fetch_open_pct(sector_etf, reaction_date)
        price_source = price_source or src

    if not price_source:
        raise ValueError("postmortem requires a named price_source")

    idio = stock_open_pct - etf_open_pct
    if direction in ("BUY", "BUY SHARES"):
        idio_sign_correct = idio > 0
    elif direction in ("SHORT", "SHORT SHARES"):
        idio_sign_correct = idio < 0
    else:
        idio_sign_correct = None  # NO_TRADE recorded for audit, not scored

    record = {
        "record_type": "postmortem",
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "ticker": ticker,
        "earnings_date": earnings_date,
        "price_source": price_source,
        "stock_open_pct": round(stock_open_pct, 4),
        "etf_open_pct": round(etf_open_pct, 4),
        "idio_open_pct": round(idio, 4),
        "idio_sign_correct": idio_sign_correct,
        "raw_pnl": raw_pnl,
        "taxonomy": taxonomy,
        "classification": classification,
        "postprint_CBR": postprint_cbr,
    }

    with open(log_path, "a") as f:
        f.write(json.dumps(record) + "\n")
    return record


# ─── T+1 deduction & learning loop ───────────────────────────────

def attribute_failure(prereg: dict, idio_open_pct: float) -> dict:
    """Deterministic attribution: for a logged run, which components pointed the
    WRONG way vs the realized idio sign, and which signed component was heaviest
    in the wrong direction. This is the engine half — it surfaces evidence; the
    LLM assigns the taxonomy (A–F) / ANOMALY classification on top.
    """
    realized = _sign(idio_open_pct)
    comps = prereg.get("components", {})
    wrong, right = [], []
    for name in COMPONENTS:
        sc = (comps.get(name) or {}).get("score")
        if not sc:
            continue
        if _sign(sc) == realized:
            right.append((name, sc))
        else:
            wrong.append((name, sc))
    heaviest_wrong = max(wrong, key=lambda kv: abs(kv[1]), default=(None, 0))[0]
    return {
        "realized_idio_sign": realized,
        "ds": prereg.get("DS"),
        "wrong_components": [n for n, _ in wrong],
        "right_components": [n for n, _ in right],
        "heaviest_wrong": heaviest_wrong,
        "component_scores": {n: (comps.get(n) or {}).get("score") for n in COMPONENTS},
    }


def evaluate_outcome(*, ticker: str, earnings_date: str, reaction_date: str,
                     sector_etf: str, classification: str = "NORMAL",
                     taxonomy: Optional[str] = None,
                     deduction: str = "", raw_pnl: Optional[float] = None,
                     price_source: Optional[str] = None,
                     log_path: Path = LOG_PATH) -> dict:
    """The T+1 learning loop. Joins the frozen prereg, pulls independent open
    prices, labels the prediction CORRECT/WRONG, runs failure attribution, and
    appends a 'deduction' record to the log (keyed to the prereg). Writes the
    post-mortem too. Never alters scoring logic — it produces evidence the
    governance layer acts on.
    """
    # Locate the matching frozen prereg (verify its integrity).
    prereg = None
    for line in Path(log_path).read_text().splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e.get("record_type") == "prereg" and \
           e.get("ticker") == ticker and e.get("earnings_date") == earnings_date:
            prereg = e
    if prereg is None:
        raise ValueError(f"no prereg for {ticker} {earnings_date} — unregistered, excluded")
    if compute_integrity_hash(prereg) != prereg.get("integrity_hash"):
        raise ValueError(f"prereg integrity hash mismatch for {ticker} {earnings_date}")

    direction = prereg.get("direction", "NO_TRADE")
    pm = write_postmortem(ticker=ticker, earnings_date=earnings_date,
                          reaction_date=reaction_date, sector_etf=sector_etf,
                          direction=direction, raw_pnl=raw_pnl,
                          taxonomy=taxonomy, classification=classification,
                          price_source=price_source, log_path=log_path)

    idio = pm["idio_open_pct"]
    label = "CORRECT" if pm["idio_sign_correct"] else \
            ("WRONG" if pm["idio_sign_correct"] is False else "N/A (no trade)")

    attribution = attribute_failure(prereg, idio) if label == "WRONG" else None

    record = {
        "record_type": "deduction",
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "ticker": ticker, "earnings_date": earnings_date,
        "direction": direction, "DS": prereg.get("DS"),
        "idio_open_pct": idio, "label": label,
        "classification": classification,
        "frozen": classification == "ANOMALY",
        "attribution": attribution,
        "deduction": deduction,
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(record) + "\n")
    return {"postmortem": pm, "deduction": record}


# ─── Full run (orchestrator) ─────────────────────────────────────

def run(ticker: str, *,
        # Market data (caller provides)
        price: float,
        avg_dollar_vol_20d: float,
        avg_share_vol_20d: float,
        avg_abs_open: float,
        confirmed_quarters: int,
        implied_move: float,
        capital: float,
        # SAT inputs
        stock_pct_since_last_earnings: float,
        sector_pct_since_last_earnings: float,
        near_52w_high_pct: float,
        below_52w_high_pct: float,
        # REV inputs
        rev_up: int = 0,
        rev_down: int = 0,
        rev_covering: int = 0,
        # REACT
        react: Optional[int] = None,
        # Judgment inputs — passed in, never guessed
        g0_status: Optional[str] = "CONFIRMED",  # CONFIRMED/UNRESOLVED/DRY_RUN/None
        gg: Optional[int] = None,
        vel: Optional[int] = None,
        flag: Optional[int] = None,
        cbr_c1: Optional[bool] = None,
        cbr_c2: Optional[bool] = None,
        cbr_c3: Optional[bool] = None,
        # Gate inputs
        macro_overlap: bool = False,
        g4_borrow_confirmed: Optional[bool] = None,
        g4_fee: Optional[float] = None,
        # Volatility damper inputs
        vix: Optional[float] = None,
        spy_vol_wow: Optional[float] = None,
        spx_day_pct: Optional[float] = None,
        # Cap context
        weekly_gross_units: float = 0.0,
        weekly_net_units: float = 0.0,
        concurrent_positions: int = 0,
        sector_positions: int = 0,
        # Logging context (required to write a prereg)
        earnings_date: Optional[str] = None,
        session: str = "AMC",
        sector_etf: Optional[str] = None,
        sources: Optional[dict] = None,
        # WATCH flags (default OFF = canonical; flip only after holdouts + sign-off)
        inflection_override: bool = False,
        # Control
        log: bool = True,
        ) -> dict:

    unavailable = []

    # --- Gates ---
    g1_pass, g1_detail = check_g1(avg_dollar_vol_20d, 0, avg_share_vol_20d)
    g2_pass, g2_estimated, g2_detail = check_g2(avg_abs_open, confirmed_quarters)
    g3_pass, g3_damper, g3_detail = check_g3(macro_overlap)
    g4_pass, g4_detail = check_g4(g4_borrow_confirmed, g4_fee)

    gates_passed = g1_pass and g2_pass
    gates = {"G1": g1_detail, "G2": g2_detail, "G3": g3_detail, "G4": g4_detail}

    # --- CBR ---
    cbr_verdict, cbr_detail = evaluate_cbr(cbr_c1, cbr_c2, cbr_c3)

    # --- Components ---
    rev_s, rev_d = score_rev(rev_up, rev_down, rev_covering)
    gg_s, gg_d = score_gg(gg)
    vel_s, vel_d = score_vel(vel)
    sat_s, sat_d, sat_a, sat_b = score_sat(
        stock_pct_since_last_earnings, sector_pct_since_last_earnings,
        near_52w_high_pct, below_52w_high_pct, rev_s,
        vel_score=vel_s, inflection_override=inflection_override)
    react_s, react_d = score_react(react)
    flag_s, flag_d = score_flag(flag)

    if gg is None: unavailable.append("GG")
    if vel is None: unavailable.append("VEL")
    if flag is None: unavailable.append("FLAG")
    if react is None: unavailable.append("REACT")

    components = {
        "REV": rev_s, "GG": gg_s, "VEL": vel_s,
        "SAT": sat_s, "REACT": react_s, "FLAG": flag_s,
    }
    details = {
        "REV": rev_d, "GG": gg_d, "VEL": vel_d,
        "SAT": sat_d, "REACT": react_d, "FLAG": flag_d,
    }

    ds = sum(components.values())

    # --- IRM ---
    irm_val, irm_detail = calc_irm(implied_move, avg_abs_open)

    # --- Decision ---
    direction, reason, conviction = decide(ds, gates_passed, cbr_verdict, g4_pass,
                                           unavailable, g0_status=g0_status)

    # --- G2 ESTIMATED enforcement (audit fix #B2) ---
    # <4 confirmed quarters → the reaction inputs (avg_abs_open) are ESTIMATED.
    # Spec: an ESTIMATED input may never be the deciding margin — remove it and
    # if the verdict flips → NO TRADE. Removing avg_abs_open leaves G2
    # unevaluable, so any would-be trade fails closed.
    if g2_estimated and direction in ("BUY SHARES", "SHORT SHARES"):
        direction = "NO TRADE"
        reason += (" → G2 ESTIMATED (<4 confirmed qtrs): reaction inputs are the "
                   "deciding margin, fail closed")
        conviction = "NONE"

    # --- Sizing ---
    if direction in ("BUY SHARES", "SHORT SHARES"):
        sizing = compute_sizing(capital, avg_abs_open, price, conviction,
                                g3_damper, vix, spy_vol_wow, spx_day_pct)
        # Update G1 with actual position size
        g1_pass2, g1_detail2 = check_g1(avg_dollar_vol_20d, sizing["shares"], avg_share_vol_20d)
        if not g1_pass2:
            gates["G1"] = g1_detail2
            direction = "NO TRADE"
            reason += " → G1 FAIL on sized position"
            sizing["shares"] = 0
            sizing["final_units"] = 0
    else:
        sizing = {"final_units": 0.0, "shares": 0, "dampers": ["N/A"]}

    cap_warnings = check_caps(sizing.get("final_units", 0),
                              weekly_gross_units, weekly_net_units,
                              concurrent_positions, sector_positions)

    # --- Log ---
    logged = None
    if log and direction in ("BUY SHARES", "SHORT SHARES"):
        src = sources or {}
        # Rich per-component structure with raw value(s), score, and source.
        components_log = {
            "REV":   {"raw": (rev_up - rev_down) / rev_covering if rev_covering else None,
                      "score": rev_s, "source": src.get("REV", "analyst-revisions-30d")},
            "GG":    {"raw": gg, "score": gg_s, "source": src.get("GG")},
            "VEL":   {"raw": vel, "score": vel_s, "source": src.get("VEL")},
            "SAT":   {"raw_a": sat_a, "raw_b": sat_b, "score": sat_s,
                      "source": src.get("SAT", "excess-PED+52w")},
            "REACT": {"raw": react, "score": react_s, "source": src.get("REACT")},
            "FLAG":  {"raw": flag, "score": flag_s, "source": src.get("FLAG")},
        }
        gates_log = {**gates, "CBR": cbr_verdict}
        regime = {"VIX": vix, "SPX_entry_move": spx_day_pct, "macro_flag": macro_overlap}
        short_dir = "BUY" if direction == "BUY SHARES" else "SHORT"
        logged = write_prereg(
            ticker=ticker, earnings_date=earnings_date, session=session,
            price=price, sector_etf=sector_etf, components=components_log,
            ds=ds, direction=short_dir, conviction=conviction,
            avg_abs_open=avg_abs_open, irm=round(irm_val, 4),
            units=sizing.get("final_units", 0), shares=sizing.get("shares", 0),
            gates=gates_log, regime=regime)

    result = {
        "ticker": ticker,
        "direction": direction,
        "reason": reason,
        "DS": ds,
        "conviction": conviction,
        "components": components,
        "component_details": details,
        "gates": gates,
        "cbr": {"verdict": cbr_verdict, "detail": cbr_detail},
        "IRM": {"value": round(irm_val, 4), "detail": irm_detail},
        "sizing": sizing,
        "cap_warnings": cap_warnings,
        "unavailable": unavailable,
    }
    if g2_estimated:
        result["g2_estimated"] = True
    if logged:
        result["logged_at"] = logged["ts"]
        result["integrity_hash"] = logged["integrity_hash"]

    return result


# ═══════════════════════════════════════════════════════════════════
# REVIEW MODE — `python pre_engine.py --review`  (READ-ONLY ANALYSIS)
# Per PRE_review_mode_spec.md. Opens log.jsonl read-only, proposes nothing,
# changes no threshold/weight/rule, writes ONLY a timestamped copy of its
# own report into review_runs/. Every metric prints n; below its kill-switch
# n threshold it is labelled "DESCRIPTIVE ONLY — below decision threshold".
# ═══════════════════════════════════════════════════════════════════

REVIEW_RUNS_DIR = Path(__file__).parent / "review_runs"
# v1.2 SAT(a) REV-gate activation date (for section 9 before/after split).
REV_GATE_ACTIVATION_DATE = "2026-06-26"
DESC_ONLY = "DESCRIPTIVE ONLY — below decision threshold"
REVIEW_FOOTER = ("Rule changes remain WATCH → 2 holdouts → Jacob sign-off. "
                 "This report decides nothing.")
COMPONENTS = ("REV", "GG", "VEL", "SAT", "REACT", "FLAG")


def _sign(x: float) -> int:
    return (x > 0) - (x < 0)


def _load_log_readonly(log_path: Path) -> list[dict]:
    """Read log.jsonl read-only. Never writes, edits, or reorders it."""
    records = []
    if not log_path.exists():
        return records
    with open(log_path, "r") as f:           # 'r' — read-only handle
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                records.append({"record_type": "_corrupt", "raw": line})
    return records


def _comp_score(prereg: dict, name: str):
    c = prereg.get("components", {}).get(name)
    if not isinstance(c, dict):
        return None
    return c.get("score")


def build_review_report(log_path: Path = LOG_PATH,
                        since: Optional[str] = None,
                        ticker: Optional[str] = None) -> str:
    records = _load_log_readonly(log_path)

    # Optional filters (read-only; do not mutate the log).
    def _keep(r: dict) -> bool:
        if ticker and r.get("ticker") != ticker:
            return False
        if since:
            d = r.get("earnings_date") or (r.get("ts", "")[:10])
            if d and d < since:
                return False
        return True

    records = [r for r in records if r.get("record_type") in ("prereg", "postmortem", "_corrupt") and _keep(r)]

    preregs = [r for r in records if r.get("record_type") == "prereg"]
    postmortems = [r for r in records if r.get("record_type") == "postmortem"]
    corrupt = [r for r in records if r.get("record_type") == "_corrupt"]

    # ── Integrity: recompute hash for every prereg; mismatch → exclude ──
    integrity_mismatch = []
    invalid_preregs = []
    for p in preregs:
        stored = p.get("integrity_hash")
        recomputed = compute_integrity_hash(p)
        if stored != recomputed:
            integrity_mismatch.append(p)
        try:
            _validate_prereg(p)
        except PreregValidationError as e:
            invalid_preregs.append((p, str(e)))

    excluded_ids = {id(p) for p in integrity_mismatch} | {id(p) for p, _ in invalid_preregs}
    valid_preregs = [p for p in preregs if id(p) not in excluded_ids]

    # Key preregs by ticker+earnings_date for joining to postmortems.
    def _key(r):
        return (r.get("ticker"), r.get("earnings_date"))

    prereg_by_key = {_key(p): p for p in valid_preregs}

    # Outcomes = postmortems with a scorable idio sign, joined to a valid prereg.
    # ANOMALY-classified outcomes are ISOLATED — frozen exogenous variance that
    # must never drive accuracy / attribution / Type-B / ablation.
    outcomes = []
    n_anomaly_isolated = 0
    for pm in postmortems:
        if pm.get("idio_sign_correct") is None:
            continue
        pre = prereg_by_key.get(_key(pm))
        if pre is None:
            continue  # orphan/excluded prereg → not in accuracy stats
        if pm.get("classification") == "ANOMALY":
            n_anomaly_isolated += 1
            continue
        outcomes.append((pre, pm))

    # ── Build report ──
    L = []
    def line(s=""):
        L.append(s)

    line("═" * 67)
    line("PRE v1.2 — REVIEW MODE REPORT (read-only)")
    line(f"generated: {dt.datetime.now(dt.timezone.utc).isoformat()}")
    flt = []
    if since:  flt.append(f"since={since}")
    if ticker: flt.append(f"ticker={ticker}")
    line(f"filters: {', '.join(flt) if flt else 'none (full log)'}")
    line("═" * 67)

    # 1. HEADLINE ----------------------------------------------------
    dates = [r.get("earnings_date") for r in preregs if r.get("earnings_date")]
    dr = f"{min(dates)} .. {max(dates)}" if dates else "n/a"
    n_traded = sum(1 for p in preregs if p.get("direction") in ("BUY", "SHORT"))
    n_no_trade = sum(1 for p in preregs if p.get("direction") in ("NO_TRADE", "NO TRADE"))
    line("\n1. HEADLINE")
    line(f"   date range          : {dr}")
    line(f"   n_prereg            : {len(preregs)}")
    line(f"   n_traded (BUY+SHORT): {n_traded}")
    line(f"   n_no_trade          : {n_no_trade}")
    line(f"   n_outcome (postmortem present): {len(outcomes)}")
    line(f"   n_anomaly_isolated (frozen, excluded from tuning): {n_anomaly_isolated}")
    line(f"   n_unregistered/rejected (invalid preregs): {len(invalid_preregs)}")

    # 2. IDIO SIGN ACCURACY ------------------------------------------
    n_out = len(outcomes)
    correct = sum(1 for _, pm in outcomes if pm["idio_sign_correct"])
    line("\n2. IDIO SIGN ACCURACY  (THE number)")
    if n_out == 0:
        line("   n_outcome=0 — no scored outcomes yet")
    else:
        acc = correct / n_out
        line(f"   idio-sign accuracy : {acc*100:.1f}%  ({correct}/{n_out})   n_outcome={n_out}")
        if n_out >= 15:
            if acc < 0.50:
                line("   *** KILL SWITCH: PAUSE (idio acc <50% @ n≥15) ***")
            else:
                line("   kill switch armed (n≥15): not tripped")
        else:
            line(f"   {DESC_ONLY} (n_outcome<15)")

    # 3. PER-COMPONENT ATTRIBUTION -----------------------------------
    line("\n3. PER-COMPONENT ATTRIBUTION  (standalone, no interaction fitting)")
    for comp in COMPONENTS:
        sub = [(pre, pm) for pre, pm in outcomes if (_comp_score(pre, comp) or 0) != 0]
        n_nz = len(sub)
        if n_nz == 0:
            line(f"   {comp:5s}: n_nonzero=0 — no signed contributions")
            continue
        hits = sum(1 for pre, pm in sub
                   if _sign(_comp_score(pre, comp)) == _sign(pm["idio_open_pct"]))
        hr = hits / n_nz
        tag = ""
        if n_nz >= 20:
            if hr < 0.50:
                tag = "  *** ABLATION CANDIDATE (harming cumulative idio acc @ n≥20) ***"
        else:
            tag = f"   [{DESC_ONLY}]"
        line(f"   {comp:5s}: n_nonzero={n_nz:2d}  standalone hit={hr*100:.1f}% ({hits}/{n_nz}){tag}")
    line("   (report only — no reweightings computed)")

    # 4. CALIBRATION -------------------------------------------------
    line("\n4. CALIBRATION")
    def _tier(pre):
        ds = abs(pre.get("DS", 0))
        if ds >= 5: return "HIGH"
        if ds >= 3: return "MEDIUM"
        return "OTHER"
    for tier in ("MEDIUM", "HIGH"):
        ts_ = [(pre, pm) for pre, pm in outcomes if _tier(pre) == tier]
        n = len(ts_)
        if n == 0:
            line(f"   {tier:6s}: n=0")
            continue
        hr = sum(1 for pre, pm in ts_ if pm["idio_sign_correct"]) / n
        mean_abs = sum(abs(pm["idio_open_pct"]) for pre, pm in ts_) / n
        suf = "" if n >= 5 else f"   [interpretation suppressed, n<5]"
        line(f"   {tier:6s}: n={n:2d}  idio-sign hit={hr*100:.1f}%  mean|idio|={mean_abs:.2f}%{suf}")
    irms = [pre.get("IRM") for pre, pm in outcomes if isinstance(pre.get("IRM"), (int, float))]
    if irms:
        mean_irm = sum(irms) / len(irms)
        med = sorted(irms)[len(irms)//2]
        above = [(pre, pm) for pre, pm in outcomes if isinstance(pre.get("IRM"), (int, float)) and pre["IRM"] >= med]
        below = [(pre, pm) for pre, pm in outcomes if isinstance(pre.get("IRM"), (int, float)) and pre["IRM"] < med]
        line(f"   mean IRM={mean_irm:.2f}  (median={med:.2f})")
        for lbl, grp in (("IRM≥median", above), ("IRM<median", below)):
            n = len(grp)
            if n == 0:
                line(f"     {lbl}: n=0"); continue
            mai = sum(abs(pm["idio_open_pct"]) for pre, pm in grp) / n
            suf = "" if n >= 5 else "   [suppressed, n<5]"
            line(f"     {lbl}: n={n:2d}  mean|idio|={mai:.2f}%{suf}")
    else:
        line("   IRM: n=0")

    # 5. TYPE-B COUNTER ----------------------------------------------
    line("\n5. TYPE-B COUNTER  (SAT regime-blindness; live holdout for v1.2 REV-gate)")
    last10 = outcomes[-10:]
    type_b = sum(1 for pre, pm in last10 if pm.get("taxonomy") == "B")
    line(f"   taxonomy=B in last {len(last10)} outcomes: {type_b}")
    if type_b > 2:
        line("   *** KILL SWITCH: recalibrate SAT (Type-B >2/10) ***")
    line("   note: v1.2 REV-gate on trial here — sustained Type-B at 0–1/10 "
         "post-v1.2 is the evidence the gate worked.")

    # 6. REGIME SLICES -----------------------------------------------
    line("\n6. REGIME SLICES  (descriptive, n-gated)")
    def _slice(pred):
        grp = [(pre, pm) for pre, pm in outcomes if pred(pre)]
        n = len(grp)
        if n == 0:
            return "n=0"
        hr = sum(1 for pre, pm in grp if pm["idio_sign_correct"]) / n
        suf = "" if n >= 5 else "  [suppressed, n<5]"
        return f"n={n:2d}  idio hit={hr*100:.1f}%{suf}"
    def _reg(pre, k):
        return (pre.get("regime") or {}).get(k)
    line(f"   VIX>28            : {_slice(lambda p: (_reg(p,'VIX') or 0) > 28)}")
    line(f"   VIX≤28            : {_slice(lambda p: (_reg(p,'VIX') or 0) <= 28)}")
    line(f"   G3 macro-overlap  : {_slice(lambda p: bool(_reg(p,'macro_flag')))}")
    line(f"   macro-clean       : {_slice(lambda p: not _reg(p,'macro_flag'))}")
    line(f"   SPX move >±1.5%   : {_slice(lambda p: abs(_reg(p,'SPX_entry_move') or 0) > 1.5)}")
    line(f"   SPX move within   : {_slice(lambda p: abs(_reg(p,'SPX_entry_move') or 0) <= 1.5)}")

    # 7. NO-TRADE AUDIT WORKLIST -------------------------------------
    line("\n7. NO-TRADE AUDIT WORKLIST  (owed a re-run per spec)")
    pm_keys = {_key(pm) for pm in postmortems}
    owed = []
    for p in preregs:
        if p.get("direction") not in ("NO_TRADE", "NO TRADE"):
            continue
        if _key(p) in pm_keys:
            # has a postmortem; flag if idio>3% remains (already resolved)
            continue
        owed.append(p)
    if not owed:
        line("   none — every NO_TRADE has a postmortem")
    else:
        line("   NO_TRADE preregs with no postmortem yet (re-run to confirm |idio|>3%):")
        for p in owed:
            line(f"     - {p.get('ticker')}  {p.get('earnings_date')}  DS={p.get('DS')}")

    # 8. DISCIPLINE / INTEGRITY --------------------------------------
    line("\n8. DISCIPLINE / INTEGRITY")
    if integrity_mismatch:
        line("   integrity_hash MISMATCHES (altered frozen records — excluded from stats):")
        for p in integrity_mismatch:
            line(f"     - {p.get('ticker')} {p.get('earnings_date')}  stored≠recomputed")
    else:
        line("   integrity_hash: all preregs verify")
    bad_src = [pm for pm in postmortems
               if pm.get("price_source") not in NAMED_INDEPENDENT_SOURCES]
    if bad_src:
        line("   postmortems with NON-INDEPENDENT price_source:")
        for pm in bad_src:
            line(f"     - {pm.get('ticker')} {pm.get('earnings_date')}  source={pm.get('price_source')!r}")
    else:
        line("   price_source: all postmortems from a named independent source")
    if invalid_preregs:
        line("   preregs missing component/source/timestamp (should be rejected at write):")
        for p, why in invalid_preregs:
            line(f"     - {p.get('ticker')} {p.get('earnings_date')}: {why}")
    else:
        line("   preregs: none missing component/source/timestamp")
    if corrupt:
        line(f"   corrupt/unparseable lines: {len(corrupt)}")
    n_excluded = len(integrity_mismatch) + len(invalid_preregs)
    line(f"   records excluded from stats: {n_excluded} "
         f"({len(integrity_mismatch)} hash-mismatch, {len(invalid_preregs)} invalid)")

    # 9. PENDING-CHANGE HOLDOUT TRACKER ------------------------------
    line("\n9. PENDING-CHANGE HOLDOUT TRACKER  (counts only; Jacob promotes)")
    # [P2] GG sandbag-overlay
    p2_conf = 0
    p2_total = 0
    for pre, pm in outcomes:
        beater = pre.get("guidance_beat_4q")  # optional LLM-supplied flag
        gg = _comp_score(pre, "GG")
        if beater and gg == -1:
            p2_total += 1
            if pm["idio_open_pct"] > 0:        # −1 contradicted by positive idio
                p2_conf += 1
    line(f"   [P2 GG sandbag-overlay] WATCH — confirming holdouts: {p2_conf}/2 "
         f"(from {p2_total} ≥3-of-4 beaters where GG applied −1)")
    if p2_total == 0:
        line("       (no qualifying records carry the guidance_beat_4q flag)")
    line("       promotion still needs a 2nd holdout AND Jacob's REACT-ablation call.")
    # [v1.2 REV-gate] Type-B before vs after activation
    b_before = sum(1 for pre, pm in outcomes
                   if pm.get("taxonomy") == "B" and (pre.get("earnings_date") or "") < REV_GATE_ACTIVATION_DATE)
    b_after = sum(1 for pre, pm in outcomes
                  if pm.get("taxonomy") == "B" and (pre.get("earnings_date") or "") >= REV_GATE_ACTIVATION_DATE)
    line(f"   [v1.2 REV-gate] Type-B before {REV_GATE_ACTIVATION_DATE}: {b_before} | "
         f"on/after: {b_after}  (validation: expect decline)")

    # Footer ---------------------------------------------------------
    line("\n" + "─" * 67)
    line(REVIEW_FOOTER)
    line("─" * 67)

    return "\n".join(L)


def run_review(log_path: Path = LOG_PATH, since: Optional[str] = None,
               ticker: Optional[str] = None) -> str:
    """Build the report, write ONLY a timestamped copy into review_runs/, then
    print to stdout. The log itself is never touched. The file is written
    BEFORE printing so an unattended scheduled run always captures the report
    even if the console encoding rejects a character."""
    report = build_review_report(log_path, since=since, ticker=ticker)

    REVIEW_RUNS_DIR.mkdir(exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = REVIEW_RUNS_DIR / f"review_{stamp}.txt"
    out.write_text(report, encoding="utf-8")

    try:
        print(report)
        print(f"\n[report copy written: {out}]")
    except UnicodeEncodeError:
        # Non-UTF8 console (e.g. Windows cp1252 under Task Scheduler):
        # the file copy above already holds the full report verbatim.
        print(f"[report written: {out}] (console encoding could not render it)")
    return report


# ─── CLI ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="PRE engine")
    ap.add_argument("--review", action="store_true",
                    help="read-only descriptive analysis of log.jsonl")
    ap.add_argument("--since", default=None, help="YYYY-MM-DD lower bound")
    ap.add_argument("--ticker", default=None, help="restrict to one ticker")
    ap.add_argument("--log", default=str(LOG_PATH), help="path to log.jsonl")
    args = ap.parse_args()

    if args.review:
        run_review(Path(args.log), since=args.since, ticker=args.ticker)
    else:
        ap.print_help()
