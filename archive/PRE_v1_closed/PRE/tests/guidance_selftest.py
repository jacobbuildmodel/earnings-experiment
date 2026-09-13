"""
PRE guidance self-test — assertions for pre_guidance.py (GG construction, §9.2.3).
Run: PYTHONPATH=. python tests/guidance_selftest.py

Each block pins a specific way a GG could be wrong or fabricated. The contamination guard
(block 2) is the one that matters most: it is the mechanism by which §9.2 would rebuild
itself inside its own fix.
"""
from pre_guidance import (GuidanceRecord, bucket, combine, verify, render,
                          GG_BASES, CONTAMINATED_BASES, COMPARISON_REQUIRED)

PASS, FAIL = 0, 0


def check(name, got, want):
    global PASS, FAIL
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: got {got!r}, want {want!r}")
    PASS += ok
    FAIL += (not ok)


def rec(**kw):
    """A fully-provenanced RAISE, which individual tests then break in one specific way."""
    base = dict(ticker="TEST", metric="REVENUE", period="FQ4-2026",
                new_low=11.0, new_high=12.0, prior_low=10.0, prior_high=11.0,
                basis="COMPANY_GUIDANCE", comparison="OWN_PRIOR_GUIDANCE",
                source_url="https://investor.example.com/q3-2026-results",
                source_date="2026-05-01",
                quote="We now expect FQ4 revenue of $11.0-12.0B",
                prior_quote="We expect FQ4 revenue of $10.0-11.0B")
    base.update(kw)
    return GuidanceRecord(**base)


LED, EVT = "2026-04-28", "2026-07-30"      # last print, upcoming print

# ---------------------------------------------------------------------------
print("1) the three buckets, from midpoints, parameter-free")
check("1a raise -> +1", bucket(rec(), LED, EVT)["GG"], +1)
check("1b cut -> -1", bucket(rec(new_low=9.0, new_high=10.0), LED, EVT)["GG"], -1)
check("1c reiterate -> 0",
      bucket(rec(new_low=10.0, new_high=11.0), LED, EVT)["GG"], 0)
# The case a naive rule gets wrong: narrowing the range without moving the midpoint.
check("1d NARROWED range, same midpoint -> 0 (not a raise)",
      bucket(rec(new_low=10.25, new_high=10.75), LED, EVT)["GG"], 0)
# Raising only the floor IS a raise — the midpoint moves.
check("1e floor raised only -> +1",
      bucket(rec(new_low=10.5, new_high=11.0), LED, EVT)["GG"], +1)
check("1f withdrawal is a company act and is bearish",
      bucket(rec(withdrawn=True, prior_quote=None), LED, EVT)["GG"], -1)
check("1g verified records carry an audit trail",
      bucket(rec(), LED, EVT)["detail"]["source_url"].startswith("https://"), True)

# ---------------------------------------------------------------------------
print("\n2) THE CONTAMINATION GUARD — GG may never be sourced from analyst opinion")
for b in CONTAMINATED_BASES:
    r = bucket(rec(basis=b), LED, EVT)
    check(f"2 basis {b} refused", r["GG"], None)
check("2 and the refusal explains WHY, by mechanism",
      any("independent of the analyst channel" in m
          for m in bucket(rec(basis="CONSENSUS"), LED, EVT)["reasons"]), True)
# Comparing to the street is the same error wearing a valid basis.
check("2 comparison vs CONSENSUS refused even with a valid basis",
      bucket(rec(comparison="CONSENSUS"), LED, EVT)["GG"], None)
check("2 'below street but above own prior guide' is still a RAISE",
      bucket(rec(comparison=COMPARISON_REQUIRED), LED, EVT)["GG"], +1)

# ---------------------------------------------------------------------------
print("\n3) provenance is mandatory — an unsourced GG is an assertion")
check("3a no url -> UNSOURCED", bucket(rec(source_url=None), LED, EVT)["status"], "UNSOURCED")
check("3b no quote -> UNSOURCED", bucket(rec(quote=None), LED, EVT)["status"], "UNSOURCED")
check("3c no prior_quote -> UNSOURCED",
      bucket(rec(prior_quote=None), LED, EVT)["status"], "UNSOURCED")
check("3d no period -> UNSOURCED", bucket(rec(period=""), LED, EVT)["status"], "UNSOURCED")
check("3e no prior value -> UNSOURCED",
      bucket(rec(prior_low=None, prior_high=None), LED, EVT)["status"], "UNSOURCED")
check("3f UNSOURCED yields GG None, never a fallback guess",
      bucket(rec(source_url=None), LED, EVT)["GG"], None)

# ---------------------------------------------------------------------------
print("\n4) dating — this cycle only, and strictly before the print")
check("4a guidance dated AFTER the event is a retro input",
      bucket(rec(source_date="2026-07-31"), LED, EVT)["GG"], None)
check("4b guidance dated ON the event is refused too",
      bucket(rec(source_date=EVT), LED, EVT)["GG"], None)
check("4c guidance predating the last print is stale/superseded",
      bucket(rec(source_date="2026-01-15"), LED, EVT)["GG"], None)
check("4d guidance issued AT the last print is the normal case, accepted",
      bucket(rec(source_date=LED), LED, EVT)["GG"], +1)
check("4e malformed date refused", bucket(rec(source_date="May 1"), LED, EVT)["GG"], None)

# ---------------------------------------------------------------------------
print("\n5) freshness is COMPUTED but must never gate (the reverted patch stays reverted)")
at_print = bucket(rec(source_date=LED), LED, EVT)
mid_qtr = bucket(rec(source_date="2026-06-15"), LED, EVT)
check("5a routine guide at the last print is not fresh", at_print["fresh"], False)
check("5b a mid-quarter revision IS fresh", mid_qtr["fresh"], True)
check("5c freshness does NOT change the bucket", at_print["GG"], mid_qtr["GG"])
check("5d nor the status", at_print["status"], mid_qtr["status"])

# ---------------------------------------------------------------------------
print("\n6) combining metrics — disagreement resolves to 0, never to a silent tie-break")
rev_up = rec(metric="REVENUE")
eps_up = rec(metric="EPS", new_low=2.2, new_high=2.4, prior_low=2.0, prior_high=2.2)
eps_dn = rec(metric="EPS", new_low=1.8, new_high=2.0, prior_low=2.0, prior_high=2.2)
check("6a both raised -> +1", combine([rev_up, eps_up], LED, EVT)["GG"], +1)
check("6b revenue up, EPS down -> 0 (conflicted)",
      combine([rev_up, eps_dn], LED, EVT)["GG"], 0)
check("6c and the conflict is named, not hidden",
      "CONFLICTED" in combine([rev_up, eps_dn], LED, EVT)["detail"]["how"], True)
check("6d one good + one refused still yields the good one",
      combine([rev_up, rec(metric="EPS", basis="CONSENSUS")], LED, EVT)["GG"], +1)
check("6e ...and reports the refusal rather than swallowing it",
      combine([rev_up, rec(metric="EPS", basis="CONSENSUS")], LED, EVT)["n_rejected"], 1)
check("6f all refused -> UNSOURCED",
      combine([rec(basis="ANALYST"), rec(basis="STREET")], LED, EVT)["status"], "UNSOURCED")
check("6g empty input -> UNSOURCED", combine([], LED, EVT)["status"], "UNSOURCED")

# ---------------------------------------------------------------------------
print("\n7) the engine contract — a verified GG is legal input, an unsourced one is absent")
from pre_engine import Judgment, Market, Truth, EngineConfig, evaluate
CFG = EngineConfig(fasttrack=True, watch=False, react_in_ds=False)
MKT = Market(price=100.0, avg_abs_open=5.0, confirmed_quarters=10,
             dollar_vol_20d=500_000_000, share_vol_20d=5_000_000, capital=18_000)


def judged(gg_res):
    return Judgment(up_revisions_30d=2, down_revisions_30d=0, covering_analysts=10,
                    rev_basis="ESTIMATE_REVISIONS",
                    GG=gg_res["GG"], gg_basis=gg_res["gg_basis"], VEL=None,
                    REACT=None, FLAG=0, CBR="CLEAN", G0="CONFIRMED",
                    stock_pct_since_last_earnings=0.0, sector_etf_pct_same_window=0.0,
                    pct_below_52w_high=30.0)


good = bucket(rec(), LED, EVT)
r_good = evaluate(judged(good), MKT, cfg=CFG)
check("7a a verified GG lands in the components", r_good.components["GG"], +1)
check("7b and counts as VERIFIED for completeness", "GG" in r_good.verified, True)
bad_gg = bucket(rec(basis="CONSENSUS"), LED, EVT)
r_bad = evaluate(judged(bad_gg), MKT, cfg=CFG)
check("7c a refused GG is ABSENT, not zero-with-credit", "GG" in r_bad.verified, False)
check("7d and widens the worst-case band", "GG" in r_bad.unavailable, True)
check("7e GG basis is accepted by C12 strict sourcing",
      "GG" in evaluate(judged(good), MKT,
                       cfg=EngineConfig(fasttrack=True, strict_sourcing=True)).verified, True)

# ---------------------------------------------------------------------------
print("\n8) the audit trail renders")
check("8a verified render names the direction", "GG +1" in render(good), True)
check("8b and cites the source", "investor.example.com" in render(good), True)
check("8c refused render says UNSOURCED", "UNSOURCED" in render(bad_gg), True)

# ---------------------------------------------------------------------------
# 9) EDGAR locator rules (pre_edgar). PURE ONLY — no network in the suite, so these stay
#    deterministic and offline. Every filename below is a REAL one observed on 2026-07-30.
# ---------------------------------------------------------------------------
print("\n9) EDGAR exhibit locator — the naming variants that actually occur")
from pre_edgar import EX99_RE, RELEASE_RE, PRIMARY_RE, NOT_RELEASE_RE, REVISION_RE, _plain

REAL_EX99 = ["msft-ex99_1.htm",                 # Microsoft
             "exhibit991erq32026.htm",          # FICO   — no separator after 'exhibit'
             "qcom062826erex991.htm",           # QCOM   — 'ex' buried mid-name
             "lrcx_exhibitx991xq4x2026.htm"]    # LRCX   — 'x' used as the separator
for f in REAL_EX99:
    check(f"9a {f} recognised", bool(EX99_RE.search(f)), True)
check("9b the naive r'ex-?99' would have MISSED two of the four",
      sum(bool(__import__('re').search(r'ex-?99', f, 2)) for f in REAL_EX99), 2)

check("9c XBRL viewer fragments are never the release",
      all(bool(NOT_RELEASE_RE.match(f)) for f in ["R1.htm", "R24.htm", "FilingSummary.xml"]), True)
check("9d a real exhibit is not caught by that filter",
      bool(NOT_RELEASE_RE.match("exhibit991erq32026.htm")), False)
check("9e foreign-issuer primary doc is the last-resort candidate",
      bool(PRIMARY_RE.match("arm-20260630.htm")), True)
check("9f ...but the primary pattern must not swallow an exhibit",
      bool(PRIMARY_RE.match("lrcx_exhibitx991xq4x2026.htm")), False)
check("9g release-word fallback works", bool(RELEASE_RE.search("q3-earnings-release.htm")), True)

print("\n9h) revision language — the high-signal phrase detector")
check("9h1 'raising our full year guidance' detected",
      bool(REVISION_RE.search("we are raising our full year guidance")), True)
check("9h2 'lowering its fiscal 2026 outlook' detected",
      bool(REVISION_RE.search("the company is lowering its fiscal 2026 outlook")), True)
check("9h3 'reiterated full-year guidance' detected",
      bool(REVISION_RE.search("management reiterated full-year guidance")), True)
check("9h4 plain narrative is not a revision",
      bool(REVISION_RE.search("revenue grew 12% year over year")), False)

print("\n9i) html -> text")
check("9i1 tags stripped", _plain("<p>Revenue <b>$10</b>B</p>"), "Revenue $10 B")
check("9i2 entities decoded", _plain("$9.7B &#8211; $10.5B"), "$9.7B - $10.5B")
check("9i3 script/style dropped",
      _plain("<style>p{color:red}</style><p>Outlook</p>"), "Outlook")

# ---------------------------------------------------------------------------
# 10) METRIC POLARITY. Found by running the module on real filings on 2026-07-30: the
#     original rule read "midpoint up -> +1" for EVERY metric, which is right for revenue
#     and backwards for costs. Both cases below are REAL.
# ---------------------------------------------------------------------------
print("\n10) metric polarity — a raised COST guide is bearish")
from pre_guidance import POLARITY, AMBIGUOUS_METRICS

# META 2026-07-29 (real): FY26 total expenses $162-169B -> $165-169B. Expenses UP = bearish.
meta_exp = rec(metric="EXPENSES", period="FY2026",
               prior_low=162.0, prior_high=169.0, new_low=165.0, new_high=169.0,
               quote="We now expect full year 2026 total expenses to be in the range of "
                     "$165-169 billion",
               prior_quote="We expect full year 2026 total expenses to be in the range of "
                           "$162-169 billion, unchanged from our prior outlook")
check("10a META raised its FY26 EXPENSE guide -> GG -1",
      bucket(meta_exp, LED, EVT)["GG"], -1)
check("10b ...and the naive higher-is-better rule would have said +1",
      _mid_up := (165.0 + 169.0) / 2 > (162.0 + 169.0) / 2, True)
check("10c the audit trail flags the inverted polarity",
      "higher is WORSE" in bucket(meta_exp, LED, EVT)["detail"]["how"], True)

# HOOD 2026-07-29 (real): FY26 adj. opex+SBC $2.700-2.825B -> $2.675-2.775B. Costs DOWN = bullish.
hood_exp = rec(metric="OPEX", period="FY2026",
               prior_low=2.700, prior_high=2.825, new_low=2.675, new_high=2.775,
               quote="we are lowering and tightening our 2026 outlook for Adjusted Operating "
                     "Expenses and SBC to a range of $2.675 to $2.775 billion",
               prior_quote="our updated outlook for 2026 Adjusted Operating Expenses and SBC "
                           "is $2.7 billion to $2.825 billion")
check("10d HOOD lowered its FY26 OPEX guide -> GG +1", bucket(hood_exp, LED, EVT)["GG"], +1)

# Revenue polarity is unchanged — the fix must not invert the normal case.
check("10e REVENUE raised is still +1", bucket(rec(metric="REVENUE"), LED, EVT)["GG"], +1)
check("10f MARGIN raised is +1", bucket(rec(metric="OPERATING_MARGIN"), LED, EVT)["GG"], +1)
check("10g TAX_RATE raised is -1", bucket(rec(metric="TAX_RATE"), LED, EVT)["GG"], -1)

# Fail closed on anything whose polarity is not declared.
check("10h unknown metric refused", bucket(rec(metric="WIDGETS"), LED, EVT)["GG"], None)
check("10i ...with a reason that names the danger",
      any("guessing polarity" in m for m in bucket(rec(metric="WIDGETS"), LED, EVT)["reasons"]),
      True)
check("10j CAPEX is two-sided and excluded, not forced",
      bucket(rec(metric="CAPEX"), LED, EVT)["GG"], None)
check("10k ...and says why", any("two-sided" in m
                                 for m in bucket(rec(metric="CAPEX"), LED, EVT)["reasons"]), True)

# Mixed polarity through combine(): revenue up AND expenses up = conflicted, not bullish.
check("10l revenue raised + expenses raised -> CONFLICTED 0",
      combine([rec(metric="REVENUE"), meta_exp], LED, EVT)["GG"], 0)

print(f"\n=== {PASS} passed, {FAIL} failed ===")
raise SystemExit(1 if FAIL else 0)
