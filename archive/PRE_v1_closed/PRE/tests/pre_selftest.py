"""
PRE engine self-test / forward-equivalence checks.
Run: python pre_selftest.py
These are ASSERTIONS against the disclosure's own worked examples and against the
documented AEHR failure. They are NOT a backtest (no historical dataset exists).
"""
from pre_engine import Judgment, Market, Truth, Skew, EngineConfig, evaluate

PASS, FAIL = 0, 0


def check(name, got, want):
    global PASS, FAIL
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: got {got!r}, want {want!r}")
    PASS += ok
    FAIL += (not ok)


# ---------------------------------------------------------------------------
# 1) §11 AEHR walkthrough — CORRECT inputs -> INCOMPLETE (not BUY)
#    REV=+2, VEL=+1, GG/REACT UNAVAILABLE, SAT=+1 -> DS=+4; DS_floor=+2 -> INCOMPLETE.
# ---------------------------------------------------------------------------
print("1) AEHR §11 (correct inputs) — expect INCOMPLETE")
aehr = Judgment(
    up_revisions_30d=2, down_revisions_30d=0, covering_analysts=4,
    VEL=+1, GG=None, REACT=None, FLAG=0, CBR="CLEAN", G0="CONFIRMED",
    stock_pct_since_last_earnings=190.0, sector_etf_pct_same_window=30.0,
    pct_below_52w_high=40.0,
)
aehr_mkt = Market(price=76.0, avg_abs_open=21.05, confirmed_quarters=8,
                  dollar_vol_20d=50_000_000, share_vol_20d=2_000_000,
                  capital=500_000, vix=18.0)
r = evaluate(aehr, aehr_mkt)  # no truth supplied -> unreconciled warning, still evaluates
check("REV", r.components["REV"], 2)
check("SAT", r.components["SAT"], 1)          # a=0 (REV-gated), b=+1
check("DS", r.ds, 4)
check("DS_floor", r.ds_floor, 2)              # GG(-1)+REACT(-1) worst-case
check("action", r.action, "INCOMPLETE")

# ---------------------------------------------------------------------------
# 2) The ACTUAL AEHR loss driver: a wrong PED (-10 guessed vs +190 real).
#    Sealed core alone -> flips SAT and produces a (wrong) tradeable verdict.
#    C4 with a pinned-source Truth CATCHES it -> INPUT_INVALID.
# ---------------------------------------------------------------------------
print("\n2) AEHR bad PED (-10 vs source +190) — expect C4 INPUT_INVALID")
aehr_bad = Judgment(
    up_revisions_30d=2, down_revisions_30d=0, covering_analysts=4,
    VEL=+1, GG=None, REACT=None, FLAG=0, CBR="CLEAN", G0="CONFIRMED",
    stock_pct_since_last_earnings=-10.0,      # WRONG (the documented error)
    sector_etf_pct_same_window=30.0,
    pct_below_52w_high=40.0,
)
truth = Truth(stock_pct_since_last_earnings=190.0)   # from pre-registered source
r2 = evaluate(aehr_bad, aehr_mkt, t=truth)
check("action", r2.action, "INPUT_INVALID")
print("       reason:", r2.warnings[0] if r2.warnings else "(none)")

# Without C4 (fasttrack off) the bad input silently changes SAT — show the danger.
r2b = evaluate(aehr_bad, aehr_mkt, t=truth, cfg=EngineConfig(fasttrack=False))
print(f"       (fasttrack OFF -> SAT={r2b.components['SAT']}, action={r2b.action}"
      f"  <-- this is how the loss happened)")

# ---------------------------------------------------------------------------
# 3) Clean optimal BUY — strong aligned signals, all inputs present.
# ---------------------------------------------------------------------------
print("\n3) Clean optimal BUY — expect BUY, HIGH")
buy = Judgment(
    up_revisions_30d=3, down_revisions_30d=0, covering_analysts=6,   # R=0.5 -> +2
    GG=+1, VEL=+1, REACT=+1, FLAG=0, CBR="CLEAN", G0="CONFIRMED",
    stock_pct_since_last_earnings=5.0, sector_etf_pct_same_window=4.0,  # excess ~ +1 -> SAT_a 0
    pct_below_52w_high=10.0,                                            # not >25 -> SAT_b 0
)
buy_truth = Truth(stock_pct_since_last_earnings=5.0)
buy_mkt = Market(price=100.0, avg_abs_open=8.0, confirmed_quarters=8,
                 dollar_vol_20d=200_000_000, share_vol_20d=5_000_000, capital=500_000, vix=15.0)
r3 = evaluate(buy, buy_mkt, t=buy_truth)
check("DS", r3.ds, 5)                          # 2+1+1+0+1+0
check("action", r3.action, "BUY")
check("conviction", r3.conviction, "HIGH")
print(f"       shares={r3.shares}, gap_at_risk=${r3.gap_at_risk:,.0f}, "
      f"units={r3.final_units}, sensitivity={r3.sensitivity}")

# ---------------------------------------------------------------------------
# 4) CBR long-block — strong bull DS but MANUFACTURED -> NO_TRADE / LONG_BLOCKED (C2 subtype)
# ---------------------------------------------------------------------------
print("\n4) CBR long-block — expect NO_TRADE / LONG_BLOCKED")
r4 = evaluate(Judgment(**{**buy.__dict__, "CBR": "MANUFACTURED"}), buy_mkt, t=buy_truth)
check("action", r4.action, "NO_TRADE")
check("subtype", r4.no_trade_subtype, "LONG_BLOCKED")

# ---------------------------------------------------------------------------
# 5) C9 both-dampers kill — a would-be BUY dies when macro overlap AND vol spike.
# ---------------------------------------------------------------------------
print("\n5) C9 both dampers (macro + VIX>28) — expect NO_TRADE (fasttrack)")
hot_mkt = Market(price=100.0, avg_abs_open=8.0, confirmed_quarters=8,
                 dollar_vol_20d=200_000_000, share_vol_20d=5_000_000,
                 capital=500_000, vix=35.0, macro_overlap=True)
r5 = evaluate(buy, hot_mkt, t=buy_truth)
check("action (fasttrack ON)", r5.action, "NO_TRADE")
r5b = evaluate(buy, hot_mkt, t=buy_truth, cfg=EngineConfig(fasttrack=False))
check("action (fasttrack OFF -> trades, 0.25x)", r5b.action, "BUY")

# ---------------------------------------------------------------------------
# 6) C7 parabolic quirk (WATCH shadow): the +200% pullback that reads "cheap".
#    Sealed core: SAT_b=+1. With watch=True: SAT_b suppressed (excess>=+20) -> SAT lower.
# ---------------------------------------------------------------------------
print("\n6) C7 SAT(b) parabolic fix (watch shadow) — expect SAT+1 -> 0")
para = Judgment(
    up_revisions_30d=1, down_revisions_30d=0, covering_analysts=5,   # R=0.2 -> +1
    VEL=0, GG=None, REACT=None, FLAG=0, CBR="CLEAN", G0="CONFIRMED",
    stock_pct_since_last_earnings=200.0, sector_etf_pct_same_window=20.0,  # excess=+180
    pct_below_52w_high=40.0,                                              # >25 -> SAT_b +1
)
para_truth = Truth(stock_pct_since_last_earnings=200.0)
base = evaluate(para, aehr_mkt, t=para_truth, cfg=EngineConfig(fasttrack=True, watch=False))
shad = evaluate(para, aehr_mkt, t=para_truth, cfg=EngineConfig(fasttrack=True, watch=True))
check("sealed SAT", base.components["SAT"], 1)
check("watch SAT (fixed)", shad.components["SAT"], 0)

# ---------------------------------------------------------------------------
# 7) C6 — REV UNAVAILABLE now swings the worst-case band (was a hole).
# ---------------------------------------------------------------------------
print("\n7) C6 REV-unavailable widens the band")
noRev = Judgment(
    up_revisions_30d=None, down_revisions_30d=None, covering_analysts=None,  # REV UNAVAILABLE
    GG=+1, VEL=+1, REACT=+1, FLAG=0, CBR="CLEAN", G0="CONFIRMED",
    stock_pct_since_last_earnings=5.0, sector_etf_pct_same_window=4.0, pct_below_52w_high=10.0,
)
nr = evaluate(noRev, buy_mkt, t=Truth(stock_pct_since_last_earnings=5.0))
check("REV in unavailable set", "REV" in nr.unavailable, True)
# DS=+3 (GG+VEL+REACT); floor should drop below +3 because REV can be -2 -> INCOMPLETE
check("action", nr.action, "INCOMPLETE")

# ---------------------------------------------------------------------------
# 8) Stage-1 skew DIAGNOSTIC — logged, and VERDICT-INVARIANT (never gates).
# ---------------------------------------------------------------------------
print("\n8) Stage-1 skew diagnostic — logged, must NOT change the action")

# 8a) A richly-priced, bearish-skew event laid over the clean BUY (test 3).
#     SKEW should read negative BUT the action must stay BUY (Stage 1 = no gating).
rich_bear = Skew(realized_vol_3m=40.0, days_to_event=2, skew_25d=5.0,
                 consensus_pt_upside=25.0, median_up_gap=4.0, median_down_gap=9.0,
                 n_beats=4, n_misses=4)
buy_mkt_iv = Market(price=100.0, avg_abs_open=8.0, confirmed_quarters=8,
                    dollar_vol_20d=200_000_000, share_vol_20d=5_000_000,
                    capital=500_000, vix=15.0, implied_move=14.0)  # implied 14 vs realized-horizon ~3.6
r8 = evaluate(buy, buy_mkt_iv, t=buy_truth, skew=rich_bear)
check("8a action unchanged (still BUY)", r8.action, "BUY")
check("8a RICH = -1 (implied rich)", r8.skew_components.get("RICH"), -1)
check("8a POS = -1 (bearish positioning)", r8.skew_components.get("POS"), -1)
check("8a PAYOFF = -1 (down-skewed)", r8.skew_components.get("PAYOFF"), -1)
check("8a SKEW clamped to -2", r8.skew, -2)

# 8b) Same verdict with and without skew data => proof of verdict-invariance.
r_no = evaluate(buy, buy_mkt_iv, t=buy_truth, skew=None)
check("8b verdict identical w/ and w/o skew", r8.action, r_no.action)
check("8b DS identical", r8.ds, r_no.ds)
check("8b no-skew status flagged", r_no.skew_status, ["NO_SKEW_DATA"])

# 8c) Cheap-vol comeback flavor: implied << realized-horizon => RICH = +1.
cheap = Skew(realized_vol_3m=120.0, days_to_event=5, skew_25d=-2.0,
             consensus_pt_upside=-5.0, median_up_gap=18.0, median_down_gap=6.0,
             n_beats=3, n_misses=3)
cheap_mkt = Market(price=76.0, avg_abs_open=21.05, confirmed_quarters=8,
                   dollar_vol_20d=50_000_000, share_vol_20d=2_000_000,
                   capital=500_000, vix=18.0, implied_move=10.0)
r8c = evaluate(aehr, cheap_mkt, skew=cheap)   # aehr judgment => INCOMPLETE regardless
check("8c action still INCOMPLETE (skew never gates)", r8c.action, "INCOMPLETE")
check("8c RICH = +1 (implied cheap)", r8c.skew_components.get("RICH"), +1)
check("8c PAYOFF = +1 (up-skewed comeback)", r8c.skew_components.get("PAYOFF"), +1)

# 8d) Partial data => sub-scores flagged UNAVAILABLE, not fabricated.
partial = Skew(realized_vol_3m=None, skew_25d=None, median_up_gap=None)
r8d = evaluate(buy, buy_mkt_iv, t=buy_truth, skew=partial)
check("8d RICH unavailable flagged", "RICH:UNAVAILABLE" in r8d.skew_status, True)
check("8d POS unavailable flagged", "POS:UNAVAILABLE" in r8d.skew_status, True)
check("8d PAYOFF unavailable flagged", "PAYOFF:UNAVAILABLE" in r8d.skew_status, True)
check("8d SKEW = 0 (all sub-scores 0)", r8d.skew, 0)

# ---------------------------------------------------------------------------
# 9) C13 REV-FEED INTEGRITY (v1.5.6). Each case is pinned to a REAL feed reading taken
#    from the live vendor response on 2026-07-29 before the 16:00 ET prints.
# ---------------------------------------------------------------------------
print("\n9) C13 REV-feed integrity")
from pre_engine import rev_feed_integrity

_ok_mkt = Market(price=100.0, avg_abs_open=5.0, confirmed_quarters=10,
                 dollar_vol_20d=500_000_000, share_vol_20d=5_000_000, capital=18_000)


def _j(u30, d30, u7, d7, cov):
    return Judgment(up_revisions_30d=u30, down_revisions_30d=d30,
                    up_revisions_7d=u7, down_revisions_7d=d7, covering_analysts=cov,
                    rev_basis="ESTIMATE_REVISIONS", GG=None, VEL=None,
                    REACT=None, FLAG=0, CBR="CLEAN", G0="CONFIRMED",
                    stock_pct_since_last_earnings=0.0, sector_etf_pct_same_window=0.0,
                    pct_below_52w_high=30.0)


# 9a) MSFT as actually served: up7=10 > up30=8. Arithmetically impossible.
check("9a MSFT 10>8 rejected", len(rev_feed_integrity(8, 17, 10, 17, 54)) >= 1, True)
check("9a MSFT names the subset violation",
      "SUBSET" in rev_feed_integrity(8, 17, 10, 17, 54)[0], True)
check("9a and the whole evaluation fails CLOSED",
      evaluate(_j(8, 17, 10, 17, 54), _ok_mkt).action, "INPUT_INVALID")

# 9b) FTNT as actually served: 38 up / 0 down against 37 covering analysts -> R = +1.03.
#     Without C13 this scores REV=+2 — the maximum bullish fundamental read available.
from pre_engine import score_rev
check("9b FTNT would have scored REV=+2", score_rev(38, 0, 37)[0], 2)
check("9b FTNT R out of domain -> rejected", len(rev_feed_integrity(38, 0, 38, 0, 37)), 1)
check("9b FTNT fails closed", evaluate(_j(38, 0, 38, 0, 37), _ok_mkt).action, "INPUT_INVALID")

# 9c) The mirror case must also be caught — a re-basing that lands on the SHORT side.
check("9c R=-1.03 rejected too", len(rev_feed_integrity(0, 38, 0, 38, 37)), 1)

# 9d) R exactly at the domain edge is rejected; just inside is accepted.
check("9d |R|=1.00 rejected (edge is out)", len(rev_feed_integrity(10, 0, 0, 0, 10)), 1)
check("9d |R|=0.90 accepted", rev_feed_integrity(9, 0, 0, 0, 10), [])

# 9e) A COHERENT feed passes untouched — the gate must not be a blanket refusal.
#     META as actually served: up30=22 down30=13 up7=1 down7=0, 57 analysts, R=+0.16.
check("9e META coherent feed passes", rev_feed_integrity(22, 13, 1, 0, 57), [])
check("9e META still scores REV=+1", score_rev(22, 13, 57)[0], 1)
check("9e META evaluates normally", evaluate(_j(22, 13, 1, 0, 57), _ok_mkt).action != "INPUT_INVALID", True)

# 9f) Missing 7d counts must NOT trip the subset rule (older rows have no up_7d at all).
#     This is the regression guard for every pre-v1.5.2 ledger entry.
check("9f no 7d data -> no subset complaint", rev_feed_integrity(2, 0, None, None, 4), [])
check("9f AEHR's own inputs still clean", rev_feed_integrity(2, 0, None, None, 4), [])

# 9g) A missing coverage count cannot be used to compute R.
check("9g no coverage -> no R complaint", rev_feed_integrity(38, 0, 38, 0, None), [])

print(f"\n=== {PASS} passed, {FAIL} failed ===")
raise SystemExit(1 if FAIL else 0)
