"""
PRE guidance layer — GG construction with a hard provenance contract.
================================================================================
Built 2026-07-30 to close HANDOFF §9.2.3, the blocking item after §9.1 shipped inert.

THE PROBLEM THIS EXISTS TO SOLVE
`expectations_momentum` is currently REV/4 — one analyst-revisions number divided by four.
GG is the ONLY proposed directional term that is not analyst opinion, and it has been None on
100% of names in every recent batch. Until it exists the model has two signals, one of which
(§9.2) is of contested sign, and the short leg is structurally dead (§9.1 impact: 0/40).

WHY THERE IS NO AUTOMATED FETCH, AND WHY THAT IS NOT A COP-OUT
Checked directly against the live feed on 2026-07-30. Every forward surface yfinance exposes
is ANALYST-DERIVED: `calendar` Earnings/Revenue Average is consensus, `growth_estimates` is
consensus, `earnings_estimate`/`revenue_estimate` are consensus, `eps_trend` is consensus over
time (i.e. revisions again — the very term GG is supposed to be independent of). Company
guidance lives in the IR release / 8-K and nowhere in the free feed.

So GG is a RESEARCH input, and the honest engineering response is not to fake an automated
one — it is to make the researched value auditable and make fabrication mechanically hard.
That is this module. It fetches nothing. It REFUSES things.

THE DEFINITION (the load-bearing decision)
    GG = the direction of the company's OWN most recent guidance for a period,
         measured against the company's OWN PRIOR guidance for THAT SAME period.

        +1  RAISED       company increased its own prior outlook
         0  MAINTAINED   reiterated / restated / range narrowed around the same midpoint
        -1  CUT          company lowered its own prior outlook
      None  UNSOURCED    no company guidance found, or provenance incomplete

**NEVER against consensus.** If a company guides below the street but above its own prior
guide, GG is +1. Comparing to consensus would smuggle analyst opinion back into the one term
that exists to be free of it, and would re-create §9.2 inside its own fix. `comparison` must
be OWN_PRIOR_GUIDANCE and any consensus-flavoured basis is refused by name.

MECHANISM (why this term deserves to exist at all, per the standard in force)
A company revising its OWN outlook is management acting on private information about its own
order book, pricing and cost structure. That is categorically different from analysts guessing
at it: it is the issuer, not an observer, and it is a decision rather than an estimate. It is
the single most information-rich pre-print signal that is legally required to be truthful.
This argument does not depend on any sample, which is the point — §2 of the standard.

RANGE HANDLING is parameter-free by construction. Guidance is issued as a range; compare
MIDPOINTS. Exact equality -> MAINTAINED, any difference -> its sign. This matches how guidance
actually behaves (a company either moves the number or restates it), and it means a narrowed
range around an unchanged midpoint correctly reads as MAINTAINED. NO materiality threshold is
introduced, so this module adds ZERO scoring parameters — like pre_impliedmove, it constructs
an input, it does not score.

FRESHNESS IS COMPUTED, NEVER GATED. A mid-quarter revision is a stronger signal than the
routine guide issued at the last print, and it is flagged as such. It does NOT gate anything:
the freshness gate was shipped once, failed both limbs of the Abstraction Test, and was
reverted (engine v1.5.3 / calc-risk v1.3.0). Do not re-litigate it here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional, Sequence

__version__ = "1.0.0"

# Bases that denote a COMPANY-ISSUED forward statement. `gg_basis` must be one of these.
GG_BASES = ("COMPANY_GUIDANCE", "PRE_ANNOUNCEMENT", "8K_GUIDANCE", "GUIDANCE_WITHDRAWN")

# Bases that are ANALYST opinion wearing a guidance label. Refused by name, loudly, because
# this is the exact failure §9.2 describes and the exact way it would re-enter.
CONTAMINATED_BASES = ("CONSENSUS", "ESTIMATE_REVISIONS", "ANALYST", "STREET",
                      "REVISIONS", "WHISPER", "BUYSIDE")

COMPARISON_REQUIRED = "OWN_PRIOR_GUIDANCE"

# ---------------------------------------------------------------------------
# METRIC POLARITY (added 2026-07-30 after running the module on real filings).
#
# THE BUG THIS FIXES. bucket() originally read "midpoint went up -> +1" for every metric.
# That is right for revenue and wrong for costs. Caught on META's 2026-07-29 release: its
# ONLY same-period full-year guides are TOTAL EXPENSES ($162-169B -> $165-169B) and CAPEX.
# Expenses guided UP is bearish, and the naive rule would have scored META's cost overrun
# as a bullish company raise — the exact class of silent sign error the model keeps finding
# in itself. HOOD is the mirror case: it LOWERED FY26 opex, which is bullish.
#
# Unknown metrics FAIL CLOSED rather than defaulting to +1. Guessing a polarity is how a
# wrong sign enters quietly, and GG exists to be the one term that cannot do that.
# ---------------------------------------------------------------------------
POLARITY = {
    # higher is better for the issuer
    "REVENUE": +1, "EPS": +1, "NET_INCOME": +1, "OPERATING_INCOME": +1,
    "BILLINGS": +1, "GROSS_MARGIN": +1, "OPERATING_MARGIN": +1, "FCF": +1,
    "BOOKINGS": +1, "BACKLOG": +1,
    # higher is worse for the issuer
    "EXPENSES": -1, "OPEX": -1, "COSTS": -1, "TAX_RATE": -1, "SHARE_COUNT": -1,
}

# Genuinely two-sided: raised capex reads bullish as a demand signal and bearish for free
# cash flow, and which one the tape takes is not knowable from the guide itself. Excluded
# from GG with a stated reason rather than forced into a sign.
AMBIGUOUS_METRICS = {"CAPEX", "CAPITAL_EXPENDITURES"}


@dataclass
class GuidanceRecord:
    """One company-issued guidance observation, with the provenance needed to audit it.

    Every field below is mandatory for a USABLE record. A record missing any of them yields
    GG = None (UNSOURCED) rather than a guess — fail closed, as everywhere else in PRE.
    """
    ticker: str
    metric: str                      # "REVENUE" | "EPS" | "OTHER" — what was guided
    period: str                      # the guided period, e.g. "FQ4-2026". Both sides must match.
    new_low: Optional[float] = None
    new_high: Optional[float] = None
    prior_low: Optional[float] = None
    prior_high: Optional[float] = None
    basis: Optional[str] = None      # must be in GG_BASES
    comparison: Optional[str] = None  # must be COMPARISON_REQUIRED
    source_url: Optional[str] = None  # primary source: IR release / 8-K / filing
    source_date: Optional[str] = None  # ISO date the guidance was ISSUED
    quote: Optional[str] = None       # the actual guidance language, verbatim
    prior_quote: Optional[str] = None  # the prior guidance language, verbatim
    withdrawn: bool = False           # company pulled guidance entirely


def _mid(lo, hi):
    if lo is None and hi is None:
        return None
    if lo is None:
        return hi
    if hi is None:
        return lo
    return (lo + hi) / 2.0


def verify(r: GuidanceRecord, last_earnings_date: Optional[str] = None,
           event_date: Optional[str] = None) -> list:
    """Return a list of provenance failures. Empty list = the record may be used.

    This is the whole point of the module. Each rule refuses a specific way a GG could be
    wrong or fabricated; none of them is a judgement call.
    """
    bad = []
    b = (r.basis or "").upper()

    # 1. The contamination guard — the failure mode this module exists to prevent.
    if b in CONTAMINATED_BASES:
        bad.append(f"GG basis {r.basis!r} is ANALYST opinion, not company guidance. GG exists "
                   f"precisely to be independent of the analyst channel that already feeds REV; "
                   f"sourcing it from consensus would rebuild §9.2 inside its own fix.")
    elif b not in GG_BASES:
        bad.append(f"GG basis {r.basis!r} is not a company-issued basis "
                   f"({'/'.join(GG_BASES)})")

    # 2. The comparison must be company-vs-its-own-prior, never company-vs-street.
    if (r.comparison or "").upper() != COMPARISON_REQUIRED:
        bad.append(f"comparison {r.comparison!r} must be {COMPARISON_REQUIRED} — a guide that "
                   f"is 'below consensus' but above the company's own prior guide is a RAISE")

    # 3. Primary-source citation. No citation, no input.
    if not r.source_url:
        bad.append("no source_url — a GG without a primary source is an assertion")
    if not r.quote:
        bad.append("no quote — the guidance language must be recorded verbatim")
    if not r.withdrawn and not r.prior_quote:
        bad.append("no prior_quote — the comparison baseline must be recorded verbatim")

    # 4. Dating. Guidance must belong to THIS cycle and must predate the print.
    if not r.source_date:
        bad.append("no source_date")
    else:
        try:
            sd = date.fromisoformat(r.source_date)
        except ValueError:
            bad.append(f"source_date {r.source_date!r} is not an ISO date"); sd = None
        if sd is not None:
            if event_date:
                try:
                    ed = date.fromisoformat(event_date)
                    if sd >= ed:
                        bad.append(f"source_date {r.source_date} is not BEFORE the event "
                                   f"{event_date} — that is a retro input, not a forecast")
                except ValueError:
                    pass
            if last_earnings_date:
                try:
                    led = date.fromisoformat(last_earnings_date)
                    if sd < led:
                        bad.append(f"source_date {r.source_date} predates the last print "
                                   f"{last_earnings_date} — that guidance is superseded/stale")
                except ValueError:
                    pass

    # 5. The numbers must actually support a comparison.
    if not r.withdrawn:
        if _mid(r.new_low, r.new_high) is None:
            bad.append("no new guidance value")
        if _mid(r.prior_low, r.prior_high) is None:
            bad.append("no prior guidance value")

    # 6. Period identity — comparing FQ4 guidance against FQ3 guidance is not a revision.
    if not r.period:
        bad.append("no period — both sides of the comparison must name the SAME period")

    # 7. Polarity must be KNOWN. See the POLARITY table for why this fails closed.
    met = (r.metric or "").upper()
    if met in AMBIGUOUS_METRICS:
        bad.append(f"metric {r.metric!r} is two-sided (a raised capex guide is bullish as a "
                   f"demand signal and bearish for FCF) — excluded from GG rather than "
                   f"forced into a sign")
    elif met not in POLARITY:
        bad.append(f"metric {r.metric!r} has no declared polarity — refusing rather than "
                   f"assuming higher-is-better (guessing polarity is how a wrong sign enters "
                   f"quietly). Known: {', '.join(sorted(POLARITY))}")
    return bad


def bucket(r: GuidanceRecord, last_earnings_date: Optional[str] = None,
           event_date: Optional[str] = None) -> dict:
    """Turn one verified GuidanceRecord into a GG bucket plus its audit trail.

    Returns {"GG", "gg_basis", "status", "fresh", "reasons", "detail"}.
    GG is None whenever the record cannot be trusted — never a fallback guess.
    """
    problems = verify(r, last_earnings_date, event_date)
    if problems:
        return {"GG": None, "gg_basis": None, "status": "UNSOURCED", "fresh": None,
                "reasons": problems, "detail": None}

    # A withdrawal is a real, company-issued, unambiguously negative act.
    if r.withdrawn:
        gg, how = -1, "guidance WITHDRAWN by the company"
    else:
        pol = POLARITY[(r.metric or "").upper()]
        new_m = _mid(r.new_low, r.new_high)
        old_m = _mid(r.prior_low, r.prior_high)
        direction = 1 if new_m > old_m else (-1 if new_m < old_m else 0)
        gg = direction * pol           # <- the polarity fix; see POLARITY
        word = {1: "RAISED", -1: "LOWERED", 0: "MAINTAINED"}[direction]
        if direction == 0:
            how = f"MAINTAINED: {r.metric} midpoint unchanged at {new_m:,.4g}"
        else:
            how = (f"{word}: {r.metric} midpoint {old_m:,.4g} -> {new_m:,.4g} "
                   f"(higher is {'better' if pol > 0 else 'WORSE'} -> GG {gg:+d})")

    # FRESHNESS — computed, logged, NEVER gated. See the module docstring.
    fresh = None
    if r.source_date and last_earnings_date:
        try:
            fresh = date.fromisoformat(r.source_date) > date.fromisoformat(last_earnings_date)
        except ValueError:
            fresh = None

    return {"GG": gg, "gg_basis": r.basis.upper(), "status": "VERIFIED", "fresh": fresh,
            "reasons": [], "detail": {"how": how, "metric": r.metric, "period": r.period,
                                      "source_url": r.source_url, "source_date": r.source_date,
                                      "quote": r.quote, "prior_quote": r.prior_quote}}


def combine(records: Sequence[GuidanceRecord], last_earnings_date: Optional[str] = None,
            event_date: Optional[str] = None) -> dict:
    """Fold several guided metrics (revenue AND EPS, say) into one GG.

    Rule: take the SIGN OF THE SUM of the verified buckets, and where they DISAGREE resolve to
    0 rather than picking a favourite. A company that raises revenue while cutting EPS is not
    sending a clean directional signal, and pretending otherwise is exactly the kind of
    silent tie-break that hides a judgement call inside a number.
    """
    verified, rejected = [], []
    for r in records:
        b = bucket(r, last_earnings_date, event_date)
        (verified if b["status"] == "VERIFIED" else rejected).append((r, b))
    if not verified:
        return {"GG": None, "gg_basis": None, "status": "UNSOURCED", "fresh": None,
                "reasons": [m for _, b in rejected for m in b["reasons"]], "detail": None,
                "n_verified": 0, "n_rejected": len(rejected)}
    vals = [b["GG"] for _, b in verified]
    if any(v > 0 for v in vals) and any(v < 0 for v in vals):
        gg, how = 0, "CONFLICTED: metrics guided in opposite directions -> no clean read"
    else:
        s = sum(vals)
        gg = 1 if s > 0 else (-1 if s < 0 else 0)
        how = "; ".join(b["detail"]["how"] for _, b in verified)
    fresh = any(bool(b["fresh"]) for _, b in verified)
    return {"GG": gg, "gg_basis": verified[0][1]["gg_basis"], "status": "VERIFIED",
            "fresh": fresh, "reasons": [m for _, b in rejected for m in b["reasons"]],
            "detail": {"how": how,
                       "sources": [b["detail"]["source_url"] for _, b in verified],
                       "periods": sorted({b["detail"]["period"] for _, b in verified})},
            "n_verified": len(verified), "n_rejected": len(rejected)}


def render(res: dict) -> str:
    """One-screen audit trail for a GG, so a run file can print WHY it holds the view."""
    if res["status"] != "VERIFIED":
        L = [f"GG UNSOURCED ({res.get('n_rejected', 1)} record(s) refused)"]
        return "\n".join(L + [f"      x {m}" for m in res["reasons"]])
    d = res["detail"]
    L = [f"GG {res['GG']:+d} [{res['gg_basis']}]"
         f"{'  FRESH (mid-quarter revision)' if res.get('fresh') else ''}",
         f"      {d['how']}"]
    seen = set()
    for s in (d.get("sources") or [d.get("source_url")]):
        if s and s not in seen:      # several metrics usually share one filing
            seen.add(s)
            L.append(f"      src {s}")
    if res.get("reasons"):
        L.append(f"      ! {len(res['reasons'])} companion record(s) refused")
    return "\n".join(L)
