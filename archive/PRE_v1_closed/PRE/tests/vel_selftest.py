"""
PRE VEL self-test — pre_vel.py (forward-book velocity from SEC XBRL).
Run: PYTHONPATH=. python tests/vel_selftest.py

PURE only: every case feeds a synthetic point series into vel_from_points, so the suite is
deterministic and offline. The two guards (retro, staleness) are the important ones — both
were added because the first real run got them wrong.
"""
from pre_vel import (vel_from_points, vel_for, render, PRIMARY_CONCEPT, PROXY_CONCEPTS,
                     STALE_DAYS, MIN_POINTS, CONCEPT_MEANING_WARNING)
from pre_engine import PARAMS

PASS, FAIL = 0, 0
EVT = "2026-10-27"
C = PRIMARY_CONCEPT


def check(name, got, want):
    global PASS, FAIL
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: got {got!r}, want {want!r}")
    PASS += ok
    FAIL += (not ok)


def series(vals, ends=None, filed="2026-08-01"):
    """Six quarter-ends ending 2026-09-30, oldest first."""
    ends = ends or ["2025-06-30", "2025-09-30", "2025-12-31",
                    "2026-03-31", "2026-06-30", "2026-09-30"]
    return [(e, v, filed) for e, v in zip(ends, vals)]


# ---------------------------------------------------------------------------
print("1) bucketing is ACCELERATION of the forward book, against the existing +/-400bp band")
# flat 10% YoY every quarter -> no acceleration -> 0
flat = series([100, 100, 100, 110, 110, 110])
check("1a steady growth -> VEL 0", vel_from_points("T", flat, EVT, C).VEL, 0)

# YoY jumps from +10% to +30% -> +2000bp -> +1
accel = series([100, 100, 100, 110, 110, 130])
r_acc = vel_from_points("T", accel, EVT, C)
check("1b accelerating book -> VEL +1", r_acc.VEL, +1)
check("1c ...and the delta is reported in bp", round(r_acc.delta_bps), 2000)

# YoY falls from +10% to -10% -> -2000bp -> -1
decel = series([100, 100, 100, 110, 110, 90])
check("1d decelerating book -> VEL -1", vel_from_points("T", decel, EVT, C).VEL, -1)

# Just inside the band must NOT fire: +10% -> +13% is +300bp.
near = series([100, 100, 100, 110, 110, 113])
check("1e +300bp is inside the band -> 0", vel_from_points("T", near, EVT, C).VEL, 0)
check("1f the band is the EXISTING VEL param, not a new one",
      (PARAMS["VEL_UP_BPS"], PARAMS["VEL_DN_BPS"]), (400.0, -400.0))

# A book can accelerate while SHRINKING — the AEHR lesson: trajectory, not level.
shrink = series([200, 200, 200, 100, 100, 140])
r_sh = vel_from_points("T", shrink, EVT, C)
check("1g book still down YoY but decline is easing -> VEL +1", r_sh.VEL, +1)
check("1h ...level is negative, trajectory is positive", r_sh.g_now < 0, True)

# ---------------------------------------------------------------------------
print("\n2) RETRO GUARD — a fact filed on/after the event cannot inform the decision")
late = series([100, 100, 100, 110, 110, 130], filed="2026-10-27")   # filed ON the event
r_late = vel_from_points("T", late, EVT, C)
check("2a everything filed on the event date is dropped", r_late.status, "UNSOURCED")
check("2b ...and the drop is reported, not silent",
      any("retro guard dropped" in m for m in r_late.reasons), True)

mixed = (series([100, 100, 100, 110, 110], filed="2026-08-01")
         + [("2026-09-30", 130, "2026-11-05")])          # newest filed AFTER the event
r_mix = vel_from_points("T", mixed, EVT, C)
check("2c a late-filed newest point is excluded", r_mix.status, "UNSOURCED")
check("2d ...because only 5 remain and the pair needs its year-ago comparables",
      any("retro guard" in m for m in r_mix.reasons), True)

# The normal case: the 10-Q lags the 8-K, so pre-print the newest book is the PRIOR quarter's.
ok_lag = series([100, 100, 100, 110, 110, 130], filed="2026-08-10")
check("2e a normally-lagged filing is usable", vel_from_points("T", ok_lag, EVT, C).status,
      "VERIFIED")

# ---------------------------------------------------------------------------
print("\n3) STALENESS GUARD — a dead series returns its last value forever")
# QUALCOMM, real: last RPO period end 2022-12-25, ~1400 days before the event.
dead = series([100, 100, 100, 110, 110, 130],
              ends=["2021-09-25", "2021-12-26", "2022-03-27",
                    "2022-06-26", "2022-09-25", "2022-12-25"],
              filed="2023-02-02")
r_dead = vel_from_points("QCOM", dead, EVT, C)
check("3a a 4-year-old series is refused", r_dead.status, "UNSOURCED")
check("3b ...and is named as DEAD, not as a slow book",
      any("series is DEAD" in m for m in r_dead.reasons), True)
check("3c the limit is two quarters plus filing lag", STALE_DAYS, 183 + 60)
# Just inside the limit must still work.
fresh = series([100, 100, 100, 110, 110, 130],
               ends=["2024-12-31", "2025-03-31", "2025-06-30",
                     "2025-09-30", "2025-12-31", "2026-03-31"], filed="2026-05-01")
check("3d a normally-lagged (~210d) series is still VERIFIED",
      vel_from_points("T", fresh, EVT, C).status, "VERIFIED")

# ---------------------------------------------------------------------------
print("\n4) CONCEPT WHITELIST — availability is not meaning")
check("4a RPO is the only default-trusted concept", PRIMARY_CONCEPT,
      "RevenueRemainingPerformanceObligation")
check("4b customer-liability tags are proxies, not defaults",
      "ContractWithCustomerLiabilityCurrent" in PROXY_CONCEPTS, True)
check("4c the warning names the broker trap", "CUSTOMER MONEY" in CONCEPT_MEANING_WARNING, True)
# A proxy without a stated reason is refused (network is never reached — it returns first).
r_np = vel_for("HOOD", EVT, cik="0001783879",
               allow_concept="ContractWithCustomerLiabilityCurrent", allow_reason="")
check("4d proxy concept WITHOUT a reason is refused", r_np.status, "UNSOURCED")
check("4e ...and the refusal explains the danger",
      any("CUSTOMER MONEY" in m for m in r_np.reasons), True)
r_bad = vel_for("T", EVT, cik="0000000001", allow_concept="TotallyMadeUpConcept",
                allow_reason="because")
check("4f a non-whitelisted concept is refused", r_bad.status, "UNSOURCED")

# No RPO at all -> UNSOURCED naming the opt-in path (META/HOOD, real).
r_none = vel_from_points("META", [], EVT, C)
check("4g no RPO -> UNSOURCED", r_none.status, "UNSOURCED")
check("4h ...and points at the explicit opt-in",
      any("opted into" in m for m in r_none.reasons), True)

# ---------------------------------------------------------------------------
print("\n5) insufficient history fails closed rather than guessing")
short = series([100, 110])[:2]
r_short = vel_from_points("T", short, EVT, C)
check("5a too few points -> UNSOURCED", r_short.status, "UNSOURCED")
check("5b ...and says how many are needed",
      any(str(MIN_POINTS) in m for m in r_short.reasons), True)
# Present but with no year-ago comparable inside tolerance.
gappy = [("2024-03-31", 100, "2024-05-01"), ("2024-06-30", 100, "2024-08-01"),
         ("2026-03-31", 110, "2026-05-01"), ("2026-06-30", 110, "2026-08-01"),
         ("2026-09-30", 130, "2026-10-01")]
check("5c no year-ago comparable -> UNSOURCED",
      vel_from_points("T", gappy, EVT, C).status, "UNSOURCED")
# A zero year-ago book makes growth undefined; must not divide by it.
zero = series([0, 0, 0, 110, 110, 130])
check("5d non-positive year-ago book -> UNSOURCED",
      vel_from_points("T", zero, EVT, C).status, "UNSOURCED")

# ---------------------------------------------------------------------------
print("\n6) the engine contract")
from pre_engine import Judgment, Market, EngineConfig, evaluate
MKT = Market(price=100.0, avg_abs_open=5.0, confirmed_quarters=10,
             dollar_vol_20d=5e8, share_vol_20d=5e6, capital=18_000)
good = vel_from_points("T", accel, EVT, C)
j = Judgment(up_revisions_30d=2, down_revisions_30d=0, covering_analysts=10,
             rev_basis="ESTIMATE_REVISIONS", GG=None, VEL=good.VEL, vel_basis=good.vel_basis,
             REACT=None, FLAG=0, CBR="CLEAN", G0="CONFIRMED",
             stock_pct_since_last_earnings=0.0, sector_etf_pct_same_window=0.0,
             pct_below_52w_high=30.0)
r = evaluate(j, MKT, cfg=EngineConfig(fasttrack=True, watch=False, react_in_ds=False))
check("6a VEL lands in the components", r.components["VEL"], +1)
check("6b and counts as VERIFIED", "VEL" in r.verified, True)
check("6c the basis is a FORWARD one C12 accepts", good.vel_basis, "BACKLOG")
from pre_engine import FORWARD_VEL_BASES
check("6d ...and REVISIONS is still not in that list",
      "REVISIONS" in FORWARD_VEL_BASES, False)
# C12: an order-driven name with this basis must NOT be discarded.
j.order_driven = True
r_od = evaluate(j, MKT, cfg=EngineConfig(fasttrack=True, watch=False, react_in_ds=False))
check("6e order-driven name keeps a BACKLOG-sourced VEL", r_od.components["VEL"], +1)

print("\n7) render")
check("7a verified render names the basis", "BACKLOG" in render(good), True)
check("7b unsourced render says so", "UNSOURCED" in render(r_dead), True)

print(f"\n=== {PASS} passed, {FAIL} failed ===")
raise SystemExit(1 if FAIL else 0)
