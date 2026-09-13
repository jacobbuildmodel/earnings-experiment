"""
Ledger round-trip smoke test. Uses a TEMP ledger so the real ledger.jsonl stays clean.
Run: python ledger_selftest.py
"""
import tempfile
from pathlib import Path

from pre_engine import Judgment, Market, Truth, Skew
from pre_ledger import (pre_register, record_outcome, stats, kill_switches,
                        render_stats, _hash, _read)

PASS = FAIL = 0


def check(name, got, want):
    global PASS, FAIL
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: got {got!r}, want {want!r}")
    PASS += ok
    FAIL += (not ok)


tmp = Path(tempfile.mkdtemp()) / "ledger.jsonl"
mkt = Market(price=100.0, avg_abs_open=8.0, confirmed_quarters=8,
             dollar_vol_20d=200_000_000, share_vol_20d=5_000_000, capital=500_000,
             implied_move=14.0)
truth = Truth(stock_pct_since_last_earnings=5.0)

# a clean BUY, HIGH, with skew logged
buy = Judgment(up_revisions_30d=3, down_revisions_30d=0, covering_analysts=6,
               GG=1, VEL=1, REACT=1, FLAG=0, CBR="CLEAN", G0="CONFIRMED",
               stock_pct_since_last_earnings=5.0, sector_etf_pct_same_window=4.0,
               pct_below_52w_high=10.0)
sk = Skew(realized_vol_3m=40.0, days_to_event=2, skew_25d=5.0, consensus_pt_upside=25.0,
          median_up_gap=4.0, median_down_gap=9.0, n_beats=4, n_misses=4)  # SKEW=-2

print("1) register + freeze")
e1 = pre_register("AAA", buy, mkt, truth=truth, skew=sk, event_date="2026-07-20",
                  allow_paused=True,   # temp ledger; the pause guards LIVE capital
                  note="clean buy", ledger_path=tmp)
check("action", e1["verdict"]["action"], "BUY")
check("skew logged", e1["verdict"]["skew"], -2)
check("has integrity hash", e1["integrity_hash"].startswith("sha256:"), True)
# tamper check: re-hash the frozen payload -> same hash
frozen = {k: e1[k] for k in ("schema", "engine_version", "ticker", "event_date", "inputs", "verdict")}
check("hash reproducible from frozen payload", _hash(frozen), e1["integrity_hash"])

print("\n2) a SHORT and a NO_TRADE")
short = Judgment(up_revisions_30d=0, down_revisions_30d=3, covering_analysts=6,
                 GG=-1, VEL=-1, REACT=-1, FLAG=0, CBR="CLEAN", G0="CONFIRMED",
                 stock_pct_since_last_earnings=4.0, sector_etf_pct_same_window=5.0,
                 pct_below_52w_high=10.0)
e2 = pre_register("BBB", short, Market(price=50, avg_abs_open=10, confirmed_quarters=8,
                  dollar_vol_20d=200_000_000, share_vol_20d=8_000_000, borrow_locate=True,
                  borrow_fee=2.0), truth=Truth(stock_pct_since_last_earnings=4.0),
                  event_date="2026-07-21", ledger_path=tmp, allow_paused=True)
check("short action", e2["verdict"]["action"], "SHORT")

print("\n3) outcomes (BUY correct, SHORT correct, plus an ANOMALY that must be excluded)")
record_outcome(e1["id"], stock_open_pct=6.0, etf_open_pct=1.0, ledger_path=tmp)   # idio +5 -> BUY correct
record_outcome(e2["id"], stock_open_pct=-8.0, etf_open_pct=-1.0, ledger_path=tmp)  # idio -7 -> SHORT correct

# an anomaly BUY that "lost" but is exogenous -> frozen out of stats
e3 = pre_register("CCC", buy, mkt, truth=truth, skew=sk, event_date="2026-07-22",
                  ledger_path=tmp, allow_paused=True)
record_outcome(e3["id"], stock_open_pct=-9.0, etf_open_pct=0.0,
               classification="ANOMALY", taxonomy="F", note="M&A shock", ledger_path=tmp)

s = stats(tmp)
check("n_outcome (ANOMALY excluded)", s["n_outcome"], 2)
check("accuracy 2/2", s["accuracy"], 1.0)
check("skew_logged counts all entries w/ skew", s["skew_logged"], 2)  # AAA, CCC
check("veto candidates (BUY & SKEW<=-2, NORMAL)", s["veto_candidates"], 1)  # AAA (CCC is anomaly)

print("\n4) append-only: entries never mutated by outcomes")
rows = _read(tmp)
entry_rows = [r for r in rows if r["type"] == "entry"]
outcome_rows = [r for r in rows if r["type"] == "outcome"]
check("3 entries", len(entry_rows), 3)
check("3 outcomes", len(outcome_rows), 3)

print("\n5) kill switches do NOT falsely trip at tiny n")
# v1.5.7: the dashboard now also emits non-actionable rows — "info" (the expectancy
# ex-largest-winner line) and "REVIEW" (sign and expectancy disagreeing). Neither is a
# TRIP, and this assertion is about tripping. Filtering them is not a weakening: the test
# still fails if anything actionable fires at n=2, which is what it was written to catch,
# and REVIEW is deliberately kept in the actionable set.
ACTIONABLE = {"PAUSE", "ABLATE", "REVIEW"}
tripped = [k for k in kill_switches(s) if k[1] in ACTIONABLE]
check("no kill switch tripped at n=2", tripped, [])
check("...and every emitted row carries a known status",
      all(k[1] in ACTIONABLE | {"ok", "info"} for k in kill_switches(s)), True)

print("\n--- sample dashboard ---")
print(render_stats(s))

print(f"\n=== {PASS} passed, {FAIL} failed ===")
raise SystemExit(1 if FAIL else 0)
