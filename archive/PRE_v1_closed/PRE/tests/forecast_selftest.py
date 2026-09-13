"""
PRE forecast self-test — pre_forecast.py.
Run: PYTHONPATH=. python tests/forecast_selftest.py

The contract being pinned: THIS LAYER NEVER ABSTAINS. Every other assertion exists to stop
that promise being met dishonestly (a coinflip dressed as a view, or the layer leaking into
the trade verdict).
"""
import json
import tempfile
from pathlib import Path

from pre_forecast import forecast, log_forecast, log_outcome, score, render, Forecast

PASS, FAIL = 0, 0


def check(name, got, want):
    global PASS, FAIL
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: got {got!r}, want {want!r}")
    PASS += ok
    FAIL += (not ok)


# ---------------------------------------------------------------------------
print("1) THE CONTRACT — it never abstains, on any input")
cases = [
    dict(),                                                   # nothing at all
    dict(expectations=0.0, excess=0.0, dd=0.0),               # all exactly neutral
    dict(expectations=1.0), dict(expectations=-1.0),
    dict(excess=-40.0, dd=55.0), dict(excess=+40.0),
    dict(put_call=14.9), dict(short_interest=12.0),
    dict(expectations=0.25, excess=-10.1, put_call=14.9),     # LRCX, real
]
dirs = [forecast("T", **c).direction for c in cases]
check("1a every input yields UP or DOWN", set(dirs) <= {"UP", "DOWN"}, True)
check("1b none is None/NO_TRADE/empty", all(d in ("UP", "DOWN") for d in dirs), True)
check("1c a totally empty read still returns a direction",
      forecast("T").direction in ("UP", "DOWN"), True)
check("1d ...defaulting to the positive base rate", forecast("T").direction, "UP")
check("1e ...and labelling itself COINFLIP rather than pretending",
      forecast("T").basis, "COINFLIP")
check("1f ...and saying so in the drivers",
      any("base rate" in d for d in forecast("T").drivers), True)

# ---------------------------------------------------------------------------
print("\n2) the sub-15pt positioning the TRADE layer discards is used here")
# LRCX 07-29: excess -10.1 scored ZERO positioning for trading, then moved +19.25%.
lrcx = forecast("LRCX", expectations=0.0, excess=-10.13, dd=40.56, put_call=14.89,
                avg_gap=4.16, implied_move=7.89)
check("2a a sub-bar washout still produces signal", lrcx.components["positioning"] > 0, True)
check("2b LRCX forecasts UP", lrcx.direction, "UP")
check("2c ...as EVIDENCED, not a coinflip", lrcx.basis, "EVIDENCED")
check("2d and the driver says it was below the trade bar",
      any("below the +/-15 trade bar" in d for d in lrcx.drivers), True)
# ARM 07-29: +13.8 extended, also sub-bar.
arm = forecast("ARM", excess=13.80, dd=48.06, put_call=7.07, short_interest=12.0)
check("2e a sub-bar extension also produces signal", arm.components["positioning"] < 0, True)
# Monotonicity: more washed must never mean less bullish.
a, b = forecast("T", excess=-5.0), forecast("T", excess=-12.0)
check("2f positioning is monotonic in excess",
      b.components["positioning"] > a.components["positioning"], True)
check("2g and is clamped at the bar", forecast("T", excess=-90.0).components["positioning"], 1.0)
# A "washed" name that is not actually down much gets halved, not trusted.
check("2h washed-vs-sector but near its high is halved",
      forecast("T", excess=-15.0, dd=5.0).components["positioning"]
      < forecast("T", excess=-15.0, dd=45.0).components["positioning"], True)

# ---------------------------------------------------------------------------
print("\n3) a voided REV feed still yields an OPINION (MSFT was silent into +11.5%)")
msft = forecast("MSFT", expectations=0.0, excess=-13.97, dd=29.36, rev_raw=-0.25, put_call=0.43)
check("3a C13-voided name still gets a direction", msft.direction in ("UP", "DOWN"), True)
check("3b the fallback read is recorded", "rev_fallback" in msft.components, True)
check("3c ...and disclosed as not-tradeable",
      any("unusable for trading" in d for d in msft.drivers), True)
check("3d the fallback does NOT fire when real expectations exist",
      "rev_fallback" in forecast("T", expectations=0.5, rev_raw=-1.0).components, False)

# ---------------------------------------------------------------------------
print("\n4) implied move sets MAGNITUDE and must never touch DIRECTION")
lo = forecast("T", expectations=0.5, implied_move=2.0, avg_gap=2.0)
hi = forecast("T", expectations=0.5, implied_move=20.0, avg_gap=20.0)
check("4a direction is unchanged by implied move", lo.direction, hi.direction)
check("4b signal is unchanged by implied move", lo.signal, hi.signal)
check("4c but the expected magnitude moves", hi.expected_move > lo.expected_move, True)
check("4d regime flags a high-expected-move name",
      "HIGH_MOVE" in forecast("T", implied_move=8.0, avg_gap=8.0).regime, True)
check("4e and a quiet one", "LOW_MOVE" in forecast("T", implied_move=2.0, avg_gap=2.0).regime, True)

# ---------------------------------------------------------------------------
print("\n5) conviction ladder is ordered and honest")
check("5a a strong read is HIGH",
      forecast("T", expectations=1.0, excess=-30.0, dd=40.0).conviction, "HIGH")
check("5b a nothing read is COINFLIP", forecast("T").conviction, "COINFLIP")
check("5c basis tracks conviction", forecast("T", expectations=1.0).basis, "EVIDENCED")
strong = abs(forecast("T", expectations=1.0).signal)
weak = abs(forecast("T", expectations=0.1).signal)
check("5d |signal| is monotonic in the read", strong > weak, True)

# ---------------------------------------------------------------------------
print("\n6) regime labels — the thing that makes 'when does a name gap hard?' answerable")
check("6a deep washout", forecast("T", excess=-30.0, dd=40.0).regime.split("/")[0], "WASHED")
check("6b extended", forecast("T", excess=+30.0).regime.split("/")[0], "EXTENDED")
check("6c mild soft", forecast("T", excess=-8.0).regime.split("/")[0], "SOFT")
check("6d neutral", forecast("T", excess=0.0).regime.split("/")[0], "NEUTRAL")
check("6e unknown when positioning is absent", forecast("T").regime.split("/")[0], "UNKNOWN")

# ---------------------------------------------------------------------------
print("\n7) logging + scoring round-trip, in a TEMP file (forecasts.jsonl untouched)")
tmp = Path(tempfile.mkdtemp()) / "fc.jsonl"
# The event date must be in the FUTURE. These fixtures are logged at test-run time, so a
# past date makes them post-cutoff -- hindsight -- and log_forecast now stamps them and
# score() excludes them (see controls_fire_selftest case 9). That guard is correct and
# this suite is testing scoring ARITHMETIC, not clock behaviour, so the fixture is what
# was unrealistic: it never represented a real pre-print freeze. Dated far out so it
# cannot quietly expire and re-break this suite years from now.
_ED = "2099-08-01"
f1 = forecast("AAA", expectations=1.0, event_date=_ED)     # UP, EVIDENCED
f2 = forecast("BBB", expectations=-1.0, event_date=_ED)    # DOWN, EVIDENCED
f3 = forecast("CCC", event_date=_ED)                       # COINFLIP UP
for f in (f1, f2, f3):
    log_forecast(f, tmp)
log_outcome("AAA", _ED, +6.0, tmp)     # UP  -> correct
log_outcome("BBB", _ED, +4.0, tmp)     # DOWN-> wrong
log_outcome("CCC", _ED, -2.0, tmp)     # UP  -> wrong
s = score(tmp)
check("7a all three pairs scored", s["n"], 3)
check("7b overall accuracy", s["overall"], (33.3, 3))
check("7c coinflips can be excluded", s["excl_coinflip"], (50.0, 2))
check("7d big movers tracked separately", s["big_movers"], (100.0, 1))
check("7e sliced by conviction", "HIGH" in s["by_conviction"] or "MEDIUM" in s["by_conviction"], True)
check("7f sliced by regime", len(s["by_regime"]) >= 1, True)
check("7g empty log is handled", score(Path(tempfile.mkdtemp()) / "none.jsonl")["n"], 0)

# ---------------------------------------------------------------------------
print("\n8) separation — the forecast must never touch the trade verdict")
import ast
import inspect
import sys
import pre_edgescore
src = inspect.getsource(pre_edgescore)

# STRENGTHENED 2026-08-09. This used to be `"pre_forecast" in src == False` — a SUBSTRING
# search over the whole module, comments and docstrings included. Two ways that was wrong,
# and they point in opposite directions:
#   * FALSE POSITIVE: it failed the moment a COMMENT mentioned the module by name, which is
#     what happened when the v1.5.7b note explained that pre_batch feeds expectations into
#     pre_forecast. Nothing about the separation had changed.
#   * FALSE NEGATIVE, and this is the serious one: it would have PASSED an import performed
#     via importlib, a late import inside a function, or an attribute reached through
#     sys.modules — the exact ways a real coupling would sneak in.
# It now tests the PROPERTY (is there an import edge?) rather than the TEXT. That is the
# standing rule this session produced: assert what the control is FOR, not that it exists.
_imports = set()
for node in ast.walk(ast.parse(src)):
    if isinstance(node, ast.Import):
        _imports.update(a.name.split(".")[0] for a in node.names)
    elif isinstance(node, ast.ImportFrom) and node.module:
        _imports.add(node.module.split(".")[0])
check("8a pre_edgescore has NO import edge to pre_forecast (AST, not substring)",
      "pre_forecast" in _imports, False)
check("8a2 ...and no dynamic import either",
      any(k in src for k in ("importlib", "__import__", "sys.modules")), False)
check("8a3 ...and the module object holds no reference to it at runtime",
      any(getattr(v, "__name__", "") == "pre_forecast"
          for v in vars(pre_edgescore).values()), False)
check("8b the forecast records what the trade layer said, one-way",
      forecast("T", trade_stance="NO_TRADE").trade_stance, "NO_TRADE")
check("8c the trade stance does not alter the forecast",
      forecast("T", expectations=0.5, trade_stance="NO_TRADE").signal,
      forecast("T", expectations=0.5).signal)

print(f"\n=== {PASS} passed, {FAIL} failed ===")
raise SystemExit(1 if FAIL else 0)
