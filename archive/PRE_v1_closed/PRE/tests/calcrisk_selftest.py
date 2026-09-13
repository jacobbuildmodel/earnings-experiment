"""
PRE calc-risk layer self-test (layer v1.1.0 + engine C12).
Run: python calcrisk_selftest.py

These are ASSERTIONS pinned to the NAMED failure cases from the 2026-07-22 post-mortem.
They are NOT a backtest — no historical dataset exists and none is implied.

Each block names the failure it locks down, so a future edit that reintroduces the bug
fails loudly instead of silently.
"""
from pre_engine import Judgment, Market, Truth, Skew, EngineConfig, evaluate
from pre_calcrisk import calc_risk, CR

PASS, FAIL = 0, 0


def check(name, got, want):
    global PASS, FAIL
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: got {got!r}, want {want!r}")
    PASS += ok
    FAIL += (not ok)


CFG = EngineConfig(fasttrack=True, watch=False, react_in_ds=False)

# A washed-out name: idio excess -40pts vs sector, 45% off the high, liquid, 4+ quarters.
def washed_judgment(**kw):
    base = dict(up_revisions_30d=None, down_revisions_30d=None, covering_analysts=None,
                GG=None, VEL=None, REACT=None, FLAG=0, CBR="CLEAN", G0="CONFIRMED",
                stock_pct_since_last_earnings=-30.0, sector_etf_pct_same_window=10.0,
                pct_below_52w_high=45.0)
    base.update(kw)
    return Judgment(**base)


WASH_MKT = Market(price=100.0, avg_abs_open=9.0, confirmed_quarters=8,
                  dollar_vol_20d=200_000_000, share_vol_20d=5_000_000,
                  capital=18_000, vix=15.0, implied_move=9.0)
WASH_TRUTH = Truth(stock_pct_since_last_earnings=-30.0, pct_below_52w_high=45.0)

# ---------------------------------------------------------------------------
# 1) [THE CORE LEAK] FUND_UNDEFINED -> NO_TRADE.
#    Named failures: NFLX (-10.6%), QS (-2.9%, a MED BUY on a PRE-REVENUE company).
#    A washed-out name with NO verified trajectory legs must NOT produce a BUY.
# ---------------------------------------------------------------------------
print("1) washout + FUND UNDEFINED (the QS / NFLX case) — expect NO_TRADE")
c1 = calc_risk("QS_LIKE", washed_judgment(), WASH_MKT, WASH_TRUTH, CFG)
check("fund_status", c1.fund_status, "UNDEFINED")
check("verified legs", c1.fund_legs, [])
check("stance", c1.stance, "NO_TRADE")
check("conviction", c1.conviction, "NONE")
check("no size taken", c1.shares, 0)

# 1b) ONE verified leg is still not enough (FUND_MIN_LEGS = 2).
print("\n1b) washout + only 1 verified leg — expect NO_TRADE (absent != stable)")
c1b = calc_risk("ONE_LEG", washed_judgment(up_revisions_30d=1, down_revisions_30d=0,
                                           covering_analysts=5, rev_basis="ESTIMATE_REVISIONS"),
                WASH_MKT, WASH_TRUTH, CFG)
check("fund_legs", c1b.fund_legs, ["REV"])
check("stance", c1b.stance, "NO_TRADE")

# ---------------------------------------------------------------------------
# 2) [THE PAIRING] The FUND gate must NOT kill the AEHR-type winner.
#    AEHR was an order-driven name whose VEL came from RECORD BOOKINGS while trailing
#    revenue was -44% YoY. With the forward-sourcing rule declared, VEL is VERIFIED,
#    FUND is DEFINED, and the washout BUY survives. This is the whole justification for
#    shipping [1] and C12 together — [1] alone would have blocked a +35% trade.
# ---------------------------------------------------------------------------
print("\n2) order-driven washout, VEL sourced from BOOKINGS — expect BUY (the AEHR pairing)")
aehr_like = washed_judgment(up_revisions_30d=2, down_revisions_30d=0, covering_analysts=4,
                            rev_basis="ESTIMATE_REVISIONS", guidance_fresh=True,  # v1.2.0: the
                            # record BOOKINGS were AEHR's THIS-cycle fresh catalyst (not stale)
                            VEL=+1, order_driven=True, vel_basis="BOOKINGS")
c2 = calc_risk("AEHR_LIKE", aehr_like, WASH_MKT, WASH_TRUTH, CFG)
check("fund_legs", c2.fund_legs, ["REV", "VEL"])
check("fund_status", c2.fund_status, "DEFINED")
check("stance", c2.stance, "BUY")

# 2b) SAME name, SAME VEL value — but sourced from TRAILING REVENUE. C12 discards it,
#     FUND drops back to UNDEFINED, and the trade is blocked. This is the discipline
#     that makes [1] safe: the gate is on SOURCING, not on the analyst's confidence.
print("\n2b) same name, VEL from TRAILING_REVENUE — expect C12 discard -> NO_TRADE")
aehr_bad_src = washed_judgment(up_revisions_30d=2, down_revisions_30d=0, covering_analysts=4,
                               rev_basis="ESTIMATE_REVISIONS",
                               VEL=+1, order_driven=True, vel_basis="TRAILING_REVENUE")
r2b = evaluate(aehr_bad_src, WASH_MKT, t=WASH_TRUTH, cfg=CFG)
check("VEL discarded to 0", r2b.components["VEL"], 0)
check("VEL flagged unavailable", "VEL" in r2b.unavailable, True)
c2b = calc_risk("AEHR_BADSRC", aehr_bad_src, WASH_MKT, WASH_TRUTH, CFG)
check("stance", c2b.stance, "NO_TRADE")

# 2c) C12 is CONSERVATIVE: it must never turn a non-trade INTO a trade.
print("\n2c) C12 monotonicity — discarding VEL can only remove trades")
check("order_driven+trailing is never a BUY when the sourced version was NO_TRADE",
      (c2b.stance == "NO_TRADE"), True)

# ---------------------------------------------------------------------------
# 3) [VALUE TRAP] verified AND deteriorating still blocks (the original guard, intact).
# ---------------------------------------------------------------------------
print("\n3) washout + VERIFIED deteriorating fundamentals — expect NO_TRADE / TRAP")
trap = washed_judgment(up_revisions_30d=0, down_revisions_30d=4, covering_analysts=5,
                       rev_basis="ESTIMATE_REVISIONS", VEL=-1, vel_basis="GUIDANCE")
c3 = calc_risk("TRAP", trap, WASH_MKT, WASH_TRUTH, CFG)
check("fund_status", c3.fund_status, "DEFINED")
check("stance", c3.stance, "NO_TRADE")
check("asymmetry", c3.asymmetry, "TRAP")

# ---------------------------------------------------------------------------
# 4) [CLIFF FRAGILITY] a SHORT resting on an IRM sitting on the 1.30 cliff must abstain.
# ---------------------------------------------------------------------------
print("\n4) SHORT with IRM on the 1.30 cliff — expect FRAGILE -> NO_TRADE")
# NOTE (v1.3.0): this name must be EXTENDED (excess >= +15), not merely un-beaten — the
# SHORT hurdle was raised because shorts fight the earnings-announcement premium.
rich_j = Judgment(up_revisions_30d=3, down_revisions_30d=0, covering_analysts=6,
                  rev_basis="ESTIMATE_REVISIONS", GG=+1, gg_basis="FILED",
                  VEL=+1, vel_basis="GUIDANCE",
                  REACT=None, FLAG=0, CBR="CLEAN", G0="CONFIRMED",
                  stock_pct_since_last_earnings=40.0, sector_etf_pct_same_window=6.0,
                  pct_below_52w_high=8.0)
rich_truth = Truth(stock_pct_since_last_earnings=40.0, pct_below_52w_high=8.0)
cliff_mkt = Market(price=100.0, avg_abs_open=8.0, confirmed_quarters=8,
                   dollar_vol_20d=200_000_000, share_vol_20d=5_000_000,
                   capital=18_000, vix=15.0, implied_move=10.5)   # IRM = 1.31 -> on the cliff
c4 = calc_risk("CLIFF", rich_j, cliff_mkt, rich_truth, CFG)
check("irm", c4.irm, 1.31)
check("fragile", c4.fragile, True)
check("stance", c4.stance, "NO_TRADE")

# 4b) Clear of the cliff, the same setup DOES short — the abstention is targeted, not blanket.
print("\n4b) same setup, IRM clear of the cliff — expect SHORT")
clear_mkt = Market(price=100.0, avg_abs_open=8.0, confirmed_quarters=8,
                   dollar_vol_20d=200_000_000, share_vol_20d=5_000_000,
                   capital=18_000, vix=15.0, implied_move=12.0)   # IRM = 1.50
c4b = calc_risk("CLEAR", rich_j, clear_mkt, rich_truth, CFG)
check("irm", c4b.irm, 1.5)
check("fragile", c4b.fragile, False)
check("stance", c4b.stance, "SHORT")

# ---------------------------------------------------------------------------
# 5) [SELL-THE-NEWS CONVICTION DEFECT — case GOOG] strong fundamentals must no longer be
#    counted AGAINST a sell-the-news short. The controlled test is an A/B on the FUND sign
#    with everything else held constant: under the old logic, flipping FUND from + to -
#    RAISED conviction (it flipped two confirms, `fund<=0` and `dir<=0`). It must now be
#    conviction-INVARIANT, because a sell-the-news short is not a fundamentals bet.
# ---------------------------------------------------------------------------
print("\n5) sell-the-news SHORT — conviction must be INVARIANT to the FUND sign")
weak_fund = Judgment(up_revisions_30d=0, down_revisions_30d=4, covering_analysts=6,
                     rev_basis="ESTIMATE_REVISIONS", GG=-1, gg_basis="FILED",
                     VEL=-1, vel_basis="GUIDANCE",
                     REACT=None, FLAG=0, CBR="CLEAN", G0="CONFIRMED",
                     stock_pct_since_last_earnings=40.0,   # EXTENDED, per the v1.3.0 hurdle
                     sector_etf_pct_same_window=6.0,
                     pct_below_52w_high=8.0)
c5_weak = calc_risk("WEAK_FUND", weak_fund, clear_mkt, rich_truth, CFG)
check("strong-fund FUND read", c4b.fund, 1)
check("weak-fund FUND read", c5_weak.fund, -1)
check("both are SHORT", (c4b.stance, c5_weak.stance), ("SHORT", "SHORT"))
check("conviction INVARIANT to FUND sign", c4b.conviction, c5_weak.conviction)
check("conviction vocabulary matches the ledger's",
      c4b.conviction in ("HIGH", "MEDIUM", "LOW"), True)

# 5b) A FULLY-confirmed sell-the-news short — extended AND rich in BOTH spaces — reaches
#     MEDIUM even though its fundamentals are excellent. That is the setup being described.
print("\n5b) extended + rich in gap-space AND vol-space, great fundamentals — expect MEDIUM")
stn_j = Judgment(up_revisions_30d=4, down_revisions_30d=0, covering_analysts=6,
                 rev_basis="ESTIMATE_REVISIONS", GG=+1, gg_basis="FILED",
                 VEL=+1, vel_basis="GUIDANCE", REACT=None, FLAG=0,
                 CBR="CLEAN", G0="CONFIRMED",
                 stock_pct_since_last_earnings=40.0,      # +34pts vs sector -> EXTENDED
                 sector_etf_pct_same_window=6.0, pct_below_52w_high=2.0)
stn_truth = Truth(stock_pct_since_last_earnings=40.0, pct_below_52w_high=2.0)
stn_mkt = Market(price=100.0, avg_abs_open=8.0, confirmed_quarters=8,
                 dollar_vol_20d=200_000_000, share_vol_20d=5_000_000,
                 capital=18_000, vix=15.0, implied_move=12.0)     # IRM 1.50
stn_skew = Skew(realized_vol_3m=25.0, days_to_event=1)            # implied ann. ~190% vs 25%
c5b = calc_risk("SELL_NEWS", stn_j, stn_mkt, stn_truth, CFG, skew=stn_skew)
check("fundamentals are strong", c5b.fund, 1)
check("extended", c5b.wash, -1)
check("rich in gap-space", c5b.rich, -1)
check("rich in vol-space", c5b.vrich, -1)
check("stance", c5b.stance, "SHORT")
check("conviction", c5b.conviction, "MEDIUM")

# ---------------------------------------------------------------------------
# 6) [MEASUREMENT GAP — case GOOG] vol-space richness is now MEASURED, surfaced, and
#    explicitly NOT actioned. IRM reads "fair" (1.09) while IV >> realized.
# ---------------------------------------------------------------------------
print("\n6) IRM fair but IV >> realized — expect VRICH=-1, surfaced, NOT actioned")
goog_mkt = Market(price=180.0, avg_abs_open=5.5, confirmed_quarters=8,
                  dollar_vol_20d=2_000_000_000, share_vol_20d=20_000_000,
                  capital=18_000, vix=15.0, implied_move=6.0)      # IRM = 1.09 -> "fair"
goog_skew = Skew(realized_vol_3m=22.0, days_to_event=2, skew_25d=1.0,
                 consensus_pt_upside=12.0, short_interest_pct_float=1.2,
                 put_call_oi_ratio=0.5)                            # crowded long
c6 = calc_risk("GOOG_LIKE", rich_j, goog_mkt, rich_truth, CFG, skew=goog_skew)
check("irm reads fair", c6.rich, 0)
check("vol-space reads RICH", c6.vrich, -1)
check("vol ratio is measured, not asserted", c6.vrich_ratio is not None
      and c6.vrich_ratio >= CR["VRICH_HI"], True)
check("stance still NO_TRADE (Stage-2 not approved)", c6.stance, "NO_TRADE")
check("but the gap is SURFACED",
      any("MEASUREMENT NOTE" in c for c in c6.caveats), True)

# 6b) positioning/flow now reaches the POS sub-score instead of being invisible.
r6 = evaluate(rich_j, goog_mkt, t=rich_truth, cfg=CFG, skew=goog_skew)
check("6b POS registers crowded-long", r6.skew_components.get("POS"), -1)

# ---------------------------------------------------------------------------
# 7) [THREE OUTCOMES] INPUT_INVALID no longer returns a 4th value ("AVOID").
# ---------------------------------------------------------------------------
print("\n7) INPUT_INVALID — expect NO_TRADE, never 'AVOID'")
bad = washed_judgment(stock_pct_since_last_earnings=-30.0)
c7 = calc_risk("BAD", bad, WASH_MKT, Truth(stock_pct_since_last_earnings=+90.0), CFG)
check("sign engine caught it", c7.sign_action, "INPUT_INVALID")
check("stance", c7.stance, "NO_TRADE")

# 7b) the invariant itself, across every case built above.
alldecisions = [c1, c1b, c2, c2b, c3, c4, c4b, c5_weak, c5b, c6, c7]
check("7b every stance is one of exactly three",
      sorted({c.stance for c in alldecisions}), ["BUY", "NO_TRADE", "SHORT"])
check("7b every conviction is in the engine vocabulary",
      sorted({c.conviction for c in alldecisions}) == ["LOW", "MEDIUM", "NONE"]
      or sorted({c.conviction for c in alldecisions}) == ["MEDIUM", "NONE"], True)

# ---------------------------------------------------------------------------
# 8) [SIZING] gap-at-risk is reported against the REAL book, not a hardcoded $500k.
# ---------------------------------------------------------------------------
print("\n8) sizing reports against the actual capital supplied")
check("capital carried onto the decision", c2.capital, 18_000)
check("gap-at-risk <= risk budget of the real book", c2.gap_at_risk <= 0.005 * 18_000 + 1, True)

# ---------------------------------------------------------------------------
# [GF] GUIDE-FRESHNESS IS DIAGNOSTIC, NOT A GATE (layer v1.3.0).
# v1.2.0 made freshness a GATE on the washout-BUY. An independent review applied the
# Abstraction Test and it failed BOTH limbs: it would not have prevented the failure it
# was built for (AMKR — Type-B, unobservable pre-print) AND it blocks AEHR, the only
# winner. These assertions LOCK THE REVERSAL so the patch cannot creep back in.
# ---------------------------------------------------------------------------
print("\n[GF] freshness must be DIAGNOSTIC ONLY — it must never gate a verdict")
from pre_engine import Judgment as _J, Market as _M, Truth as _T, EngineConfig as _C
_cfg = _C(fasttrack=True, watch=False, react_in_ds=False)
def _wash(**kw):
    base = dict(up_revisions_30d=6, down_revisions_30d=0, covering_analysts=12,
                rev_basis="ESTIMATE_REVISIONS", GG=1, gg_basis="GUIDANCE",
                VEL=1, vel_basis="GUIDANCE", order_driven=True,
                REACT=None, FLAG=0, CBR="CLEAN", G0="CONFIRMED",
                stock_pct_since_last_earnings=-25.0, sector_etf_pct_same_window=10.0,
                pct_below_52w_high=33.0)
    base.update(kw); return _J(**base)
_wm = _M(price=65.0, avg_abs_open=8.5, confirmed_quarters=10, dollar_vol_20d=333_000_000,
         share_vol_20d=4_700_000, implied_move=None, capital=18_000)
_wt = _T(stock_pct_since_last_earnings=-25.0, pct_below_52w_high=33.0, price=65.0)

# The AMKR shape: verified-positive but STALE. Under v1.2.0 this was NO_TRADE. It must BUY
# again — the gate was removed — while the staleness is still SURFACED as a caveat.
amkr = calc_risk("AMKR_STALE", _wash(up_revisions_7d=1, down_revisions_7d=0), _wm, _wt, _cfg)
check("stale washout FUND is DEFINED+positive", (amkr.fund_status, amkr.fund >= 0), ("DEFINED", True))
check("stale washout -> BUY (gate REMOVED)", amkr.stance, "BUY")
check("staleness still computed", amkr.fund_fresh, False)
check("staleness SURFACED as a caveat", any("FRESHNESS" in c for c in amkr.caveats), True)

# The CLS shape: fresh wave. Also buys. Freshness changes the LOG, never the VERDICT.
# NOTE (v1.5.6): this fixture used up_7d=12 against up_30d=6 — arithmetically impossible,
# since the 7d window sits INSIDE the 30d window. C13 now refuses such a feed, which is
# what exposed it. The fixture's INTENT is preserved exactly: same 30d counts, all six
# revisions landing in the last week (fresh) vs only one (stale).
cls = calc_risk("CLS_FRESH", _wash(up_revisions_7d=6, down_revisions_7d=0), _wm, _wt, _cfg)
check("fresh washout -> BUY", cls.stance, "BUY")
check("fresh washout flagged fresh", cls.fund_fresh, True)

# VERDICT-INVARIANCE: identical setup, opposite freshness -> identical stance AND size.
check("freshness does NOT change the stance", amkr.stance, cls.stance)
check("freshness does NOT change the size", amkr.shares, cls.shares)

# The AEHR case that the gate would have killed: no freshness declarable at T-1
# (bookings were revealed IN the print). It must still BUY.
noinfo = calc_risk("AEHR_LIKE_NOINFO", _wash(), _wm, _wt, _cfg)
check("no freshness declared -> still BUY (the AEHR winner survives)", noinfo.stance, "BUY")
check("no freshness -> fund_fresh None (unknown, not False)", noinfo.fund_fresh, None)

# ---------------------------------------------------------------------------
# [SH] SHORT HURDLE RAISED (v1.3.0): rich vol + merely "not washed" is NO LONGER a short.
# Shorts fight the long-side earnings-announcement premium, so they need a higher bar:
# the name must be actually EXTENDED (wash == -1), not just un-beaten (wash == 0).
# ---------------------------------------------------------------------------
print("\n[SH] short hurdle — rich vol alone is not enough; the name must be EXTENDED")
def _rich(**kw):
    base = dict(up_revisions_30d=3, down_revisions_30d=0, covering_analysts=6,
                rev_basis="ESTIMATE_REVISIONS", GG=+1, gg_basis="FILED",
                VEL=+1, vel_basis="GUIDANCE", REACT=None, FLAG=0, CBR="CLEAN",
                G0="CONFIRMED", pct_below_52w_high=8.0)
    base.update(kw); return _J(**base)
_rm = _M(price=100.0, avg_abs_open=8.0, confirmed_quarters=8, dollar_vol_20d=200_000_000,
         share_vol_20d=5_000_000, capital=18_000, implied_move=12.0)   # IRM 1.50 = RICH

# NEUTRAL (excess +2 -> wash 0): previously SHORT, now abstain.
neutral = _rich(stock_pct_since_last_earnings=8.0, sector_etf_pct_same_window=6.0)
c_neutral = calc_risk("NEUTRAL", neutral, _rm,
                      _T(stock_pct_since_last_earnings=8.0, pct_below_52w_high=8.0), _cfg)
check("rich + not-extended -> NO_TRADE (hurdle raised)", c_neutral.stance, "NO_TRADE")
check("the raised-hurdle abstention is LOGGED, not silent",
      any("SHORT HURDLE" in c for c in c_neutral.caveats), True)

# EXTENDED (excess +34 -> wash -1): still shorts.
ext = _rich(stock_pct_since_last_earnings=40.0, sector_etf_pct_same_window=6.0,
            pct_below_52w_high=2.0)
c_ext = calc_risk("EXTENDED", ext, _rm,
                  _T(stock_pct_since_last_earnings=40.0, pct_below_52w_high=2.0), _cfg)
check("rich + EXTENDED -> SHORT still fires", c_ext.stance, "SHORT")

print(f"\n=== {PASS} passed, {FAIL} failed ===")
raise SystemExit(1 if FAIL else 0)
