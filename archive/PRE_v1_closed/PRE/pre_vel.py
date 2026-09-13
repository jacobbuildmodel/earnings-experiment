"""
PRE VEL layer — forward-book velocity from SEC XBRL.
================================================================================
Built 2026-07-30 to close the last unsourced leg (HANDOFF §16.4). With REV from revisions and
GG from EDGAR guidance, VEL is the only thing between the model and 4/4 completeness.

WHY THIS ONE CAN BE AUTOMATED WHEN GG COULD NOT
GG lives in press-release PROSE, so it needs a human read (pre_guidance). VEL lives in the
company's own XBRL FACTS — structured, typed, dated, and filed with the SEC. There is no
parsing ambiguity to hide a fabrication in, so this module fetches AND buckets end to end.

WHAT VEL MEASURES
    VEL = the ACCELERATION of the company's contracted forward book.

        g_now   = RPO(t)   / RPO(t-4q) - 1        <- latest YoY growth
        g_prev  = RPO(t-1) / RPO(t-5q) - 1        <- the YoY growth one quarter earlier
        delta   = (g_now - g_prev) in basis points
        +1 if delta >= +VEL_UP_BPS · -1 if delta <= VEL_DN_BPS · 0 otherwise

Acceleration, not level, because the ±400bp band in PARAMS is a band on a CHANGE in growth,
and because the AEHR lesson was precisely that a book can be accelerating while trailing
revenue collapses. Reuses VEL_UP_BPS / VEL_DN_BPS — **zero new parameters.**

THE CONCEPT-MEANING TRAP (found on the first real run, and the reason for the whitelist)
Availability is not meaning. `ContractWithCustomerLiabilityCurrent` resolves for ROBINHOOD at
**$12-16 BILLION** — those are broker customer balances, not a forward revenue book. Feeding
that in as "deferred revenue" would have produced a confident, enormous, meaningless VEL.

So only ONE concept is trusted by default:

    RevenueRemainingPerformanceObligation  (RPO, ASC 606)

RPO is *defined* as consideration on contracts not yet recognised — it IS the contracted
forward book, and it means the same thing for every filer. Deferred-revenue variants are a
weaker proxy that is valid ONLY for subscription/contract businesses and meaningless for
brokers, insurers and banks; they are available but must be opted into per name with a stated
reason (`allow_concept=`). Everything else fails closed.

THE RETRO GUARD
Every XBRL fact carries the date it was FILED. A 10-Q lands days to weeks AFTER the 8-K, so at
pre-print time the newest available RPO is the PRIOR quarter's — which is correct and genuinely
pre-print. Any fact FILED on or after the event date is discarded, so a run can never reach
forward into a filing that did not exist when the decision was made.
"""
from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from datetime import date
from typing import Optional

from pre_engine import PARAMS

__version__ = "1.0.0"

UA = {"User-Agent": "PRE-research jacobong999@gmail.com"}

# The one concept whose meaning is unambiguous across filers. See the trap note above.
PRIMARY_CONCEPT = "RevenueRemainingPerformanceObligation"

# Weaker proxies. Valid only for subscription/contract businesses; MEANINGLESS for brokers,
# insurers and banks, where the same tag holds customer money. Opt-in per name only.
PROXY_CONCEPTS = ("ContractWithCustomerLiability", "ContractWithCustomerLiabilityCurrent",
                  "DeferredRevenueCurrent")

# Businesses where a customer-liability tag is NOT a forward revenue book, at all.
CONCEPT_MEANING_WARNING = (
    "a customer-liability tag on a broker/bank/insurer holds CUSTOMER MONEY, not deferred "
    "revenue (ROBINHOOD reports $12-16B under this tag). Only opt in for a subscription or "
    "contract business, and say why.")

YOY_DAYS, YOY_TOL = 365, 45          # a 'year ago' point, with fiscal-calendar tolerance
MIN_POINTS = 5                        # need t, t-1, t-4, t-5 to compute two YoY growths

# STALENESS GUARD. Derived, not tuned: a quarterly filer that still reports a concept will
# have a period end within TWO fiscal quarters (~183d) of the event, plus filing lag. Beyond
# that the issuer has STOPPED reporting it and the series is dead.
#
# Caught on the first real run: QUALCOMM's last RPO filing is 2022-12-25 — nearly four years
# before the event — and the module cheerfully computed a VEL from it. A dead series does not
# announce itself; it just keeps returning its final value forever.
STALE_DAYS = 183 + 60


@dataclass
class VelResult:
    ticker: str
    VEL: Optional[int]
    vel_basis: Optional[str]
    status: str                       # VERIFIED / UNSOURCED
    concept: Optional[str] = None
    g_now: Optional[float] = None
    g_prev: Optional[float] = None
    delta_bps: Optional[float] = None
    points: Optional[list] = None
    reasons: Optional[list] = None


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def fetch_concept(cik: str, concept: str) -> list:
    """Return [(end_date, value, filed_date)] for a us-gaap concept, oldest first.

    De-duplicated by `end`, keeping the EARLIEST filing that reported each period. Later
    amendments restate history, and using a restated figure would mean scoring a decision on
    information that did not exist at the time.
    """
    url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{concept}.json"
    try:
        d = _get(url)
    except Exception:
        return []
    units = d.get("units", {})
    key = next((k for k in units if k.startswith("USD")), None)
    if not key:
        return []
    best: dict = {}
    for r in units[key]:
        end, val, filed = r.get("end"), r.get("val"), r.get("filed")
        if not (end and filed) or val is None:
            continue
        if end not in best or filed < best[end][1]:
            best[end] = (val, filed)
    return sorted((e, v, f) for e, (v, f) in best.items())


def _pick(points, target: date):
    """The point closest to `target`, within tolerance. Fiscal quarters drift; exact
    date arithmetic would drop most filers."""
    best, bd = None, None
    for e, v, f in points:
        try:
            d = date.fromisoformat(e)
        except ValueError:
            continue
        gap = abs((d - target).days)
        if gap <= YOY_TOL and (bd is None or gap < bd):
            best, bd = (e, v, f), gap
    return best


def vel_for(ticker: str, event_date: str, cik: Optional[str] = None,
            allow_concept: Optional[str] = None, allow_reason: str = "") -> VelResult:
    """Compute VEL for one name, fail-closed at every step."""
    from pre_edgar import cik_of
    reasons = []
    cik = cik or cik_of(ticker)
    if not cik:
        return VelResult(ticker, None, None, "UNSOURCED", reasons=["no CIK for ticker"])

    concept = PRIMARY_CONCEPT
    if allow_concept and allow_concept != PRIMARY_CONCEPT:
        if allow_concept not in PROXY_CONCEPTS:
            return VelResult(ticker, None, None, "UNSOURCED",
                             reasons=[f"concept {allow_concept!r} is not whitelisted"])
        if not allow_reason:
            return VelResult(ticker, None, None, "UNSOURCED",
                             reasons=[f"proxy concept {allow_concept!r} needs a stated reason: "
                                      + CONCEPT_MEANING_WARNING])
        concept = allow_concept
        reasons.append(f"PROXY concept {concept} used: {allow_reason}")

    pts = fetch_concept(cik, concept)
    return vel_from_points(ticker, pts, event_date, concept, reasons)


def vel_from_points(ticker: str, pts: list, event_date: str, concept: str,
                    reasons: Optional[list] = None) -> VelResult:
    """The PURE core: [(end, value, filed)] -> VEL. No network, so it is unit-testable."""
    reasons = list(reasons or [])
    if not pts and concept == PRIMARY_CONCEPT:
        return VelResult(ticker, None, None, "UNSOURCED", concept=concept,
                         reasons=reasons + [
                             f"{ticker} does not report RPO ({PRIMARY_CONCEPT}). A "
                             f"deferred-revenue proxy exists but must be opted into "
                             f"explicitly: " + CONCEPT_MEANING_WARNING])

    # RETRO GUARD — nothing filed on or after the event may inform the decision.
    usable = [p for p in pts if p[2] < event_date]
    dropped = len(pts) - len(usable)
    if dropped:
        reasons.append(f"retro guard dropped {dropped} fact(s) filed on/after {event_date}")
    if len(usable) < MIN_POINTS:
        return VelResult(ticker, None, None, "UNSOURCED", concept=concept, points=usable[-6:],
                         reasons=reasons + [f"only {len(usable)} usable filings; need "
                                            f"{MIN_POINTS} to compute two YoY growth rates"])

    t0, t1 = usable[-1], usable[-2]
    try:
        d0, d1 = date.fromisoformat(t0[0]), date.fromisoformat(t1[0])
    except ValueError:
        return VelResult(ticker, None, None, "UNSOURCED", concept=concept,
                         reasons=reasons + ["unparseable period end"])

    # STALENESS — a dead series keeps returning its last value forever. See STALE_DAYS.
    age = (date.fromisoformat(event_date) - d0).days
    if age > STALE_DAYS:
        return VelResult(ticker, None, None, "UNSOURCED", concept=concept, points=usable[-3:],
                         reasons=reasons + [
                             f"series is DEAD: newest {concept} period ends {t0[0]}, "
                             f"{age} days before the event (limit {STALE_DAYS}). The issuer "
                             f"has stopped reporting this concept — it is not a slow book."])
    y0 = _pick(usable, d0.replace(year=d0.year - 1))
    y1 = _pick(usable, d1.replace(year=d1.year - 1))
    if not y0 or not y1:
        return VelResult(ticker, None, None, "UNSOURCED", concept=concept, points=usable[-6:],
                         reasons=reasons + ["no year-ago comparable within tolerance "
                                            f"(+/-{YOY_TOL}d) for both quarters"])
    if y0[1] <= 0 or y1[1] <= 0:
        return VelResult(ticker, None, None, "UNSOURCED", concept=concept,
                         reasons=reasons + ["non-positive year-ago book; growth undefined"])

    g_now = t0[1] / y0[1] - 1.0
    g_prev = t1[1] / y1[1] - 1.0
    delta = (g_now - g_prev) * 10_000.0
    if delta >= PARAMS["VEL_UP_BPS"]:
        vel = +1
    elif delta <= PARAMS["VEL_DN_BPS"]:
        vel = -1
    else:
        vel = 0
    return VelResult(ticker, vel, "BACKLOG" if concept == PRIMARY_CONCEPT else "BOOKINGS",
                     "VERIFIED", concept=concept, g_now=g_now, g_prev=g_prev, delta_bps=delta,
                     points=[t0, t1, y0, y1], reasons=reasons)


def render(r: VelResult) -> str:
    if r.status != "VERIFIED":
        return "\n".join([f"VEL UNSOURCED ({r.concept or 'no concept'})"]
                         + [f"      x {m}" for m in (r.reasons or [])])
    L = [f"VEL {r.VEL:+d} [{r.vel_basis} / {r.concept}]",
         f"      forward book YoY {r.g_prev:+.1%} -> {r.g_now:+.1%} "
         f"= {r.delta_bps:+,.0f}bp vs the +/-{PARAMS['VEL_UP_BPS']:.0f}bp band"]
    for e, v, f in (r.points or [])[:2]:
        L.append(f"      {e}: ${v/1e9:,.2f}B (filed {f})")
    for m in (r.reasons or []):
        L.append(f"      ! {m}")
    return "\n".join(L)


if __name__ == "__main__":
    import sys
    ev = "2026-10-27"
    for t in sys.argv[1:] or ["MSFT", "FTNT", "LRCX", "FICO", "QCOM", "META", "HOOD", "ARM"]:
        print(f"\n{t}")
        print("  " + render(vel_for(t, ev)).replace("\n", "\n  "))
