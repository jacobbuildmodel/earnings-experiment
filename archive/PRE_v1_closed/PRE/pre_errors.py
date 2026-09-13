"""
PRE ERROR LEDGER — the thing that makes a wrong call cost something.
================================================================================
Built 2026-08-09 on owner instruction. The complaint that produced it, verbatim:

    "for the previous time, I always see when ... your results are wrong, you do nothing."

That observation is CORRECT and it was structural, not laziness. The POSTMORTEM SOP
classifies every miss into A/B/C/D and then says:

    A -> fix it          B -> PATCHING FORBIDDEN
    C -> fix the exit    D -> "Log it. Write nothing."

So three of the four branches terminate in *do nothing*, and the fourth ("fix it") had
no counter attached — it fired on n=1 or never. Both failure modes were live at once:
the model patched instantly off single vivid trades (the FUND-verified gate, then the
guide-freshness gate, 1-for-5 over two weeks), and simultaneously accumulated Type B/D
misses that produced no response of any kind, forever.

THE FIX, and it is deliberately not a loosening of the SOP:
  * Every graded outcome — WINS INCLUDED — writes an observation against an ERROR CLASS.
    A class is a MECHANISM ("washout term fires on names that are cheap for a reason"),
    never a ticker. Tickers recur too rarely to ever accumulate.
  * A class accumulates CONFIRMATIONS until it is RIPE, then it demands a response.
  * The response DEPENDS ON THE TYPE, and for B and D it is explicitly NOT a patch:
        A-mechanical -> FIX NOW at n=1        (a bug is not evidence, it is a bug)
        A-judgment   -> PEND to 3             (a threshold is a belief; 3 confirmations)
        C            -> PEND to 3             (expression/exit only, never the signal)
        B            -> BOUNDARY, escalates at 3 to a BET-SELECTION question
        D            -> VARIANCE,  escalates at 3 to a DISTRIBUTION question
    B and D still may not be patched. But at 3 they stop being silent. "We keep losing
    to forward guides on semis" is not a parameter change — it is a question about
    whether to take that bet at all, and it is now asked automatically.

THE INDEPENDENCE RULE — the part that is easy to get wrong and expensive to get wrong.
Three same-sector names printing the same night are ONE observation, not three. They
share the macro tape, the sector print, and usually the deciding variable. Counting them
as three would let a single semis night fire a permanent model change off n=1 while
displaying "3/3 confirmations" — the exact laundering the SOP exists to prevent, dressed
in a counter. Confirmations are therefore counted over DISTINCT (sector, event_date)
keys. Owner's own reasoning, which is right: same-sector prints "build each other up" —
they corroborate a READ. They do not multiply the EVIDENCE.

NOTHING HERE SHIPS A CHANGE BY ITSELF. Ripeness produces a PROPOSAL that must still pass
the Abstraction Test (both limbs, docs/POSTMORTEM_SOP.md Step 5) and owner sign-off. This
module lowers the cost of noticing, not the bar for changing.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

__version__ = "1.0.0"

ERROR_LOG = Path(__file__).with_name("errors.jsonl")

# ---------------------------------------------------------------------------
# VOCABULARY — all closed enums. An open vocabulary silently becomes a synonym
# farm, and then two spellings of one error class never reach 3 between them.
# ---------------------------------------------------------------------------

# WHAT was wrong. The owner named the first two explicitly: a verdict that pointed the
# wrong way, and a conviction that was miscalibrated even when the direction was right.
AXES = (
    "DIRECTION",    # said UP/BUY, went down (or the reverse). The sign was wrong.
    "CONVICTION",   # sign right, confidence wrong. HIGH on a 0.2% move; COINFLIP on +19%.
    "MAGNITUDE",    # sign right, expected_move wrong by >2x in either direction.
    "EXPRESSION",   # sign right, the entry/exit/instrument captured it wrong. SOP Type C.
    "PROCESS",      # the run itself broke: stale fetch, dead pointer, unlogged outcome.
)

# WHY it was wrong — SOP Step 3, unchanged. This module does not get to invent types.
FAILURE_TYPES = ("A", "B", "C", "D")

# A-mechanical vs A-judgment. This split is the owner's: "if it is just obviously wrong
# for the model, then you change it. But if something is subjective, maybe you pend it."
# The test is REPRODUCIBILITY, not severity: a mechanical error produces a value that is
# wrong against its OWN definition, so anyone re-running the step gets the same verdict
# without an opinion. A judgment error produces a value that is correct against its
# definition and the definition is what is in doubt.
SUBTYPES = (
    "MECHANICAL",   # bug, wrong unit, stale/mis-sourced input, dead citation, off-by-one
    "JUDGMENT",     # threshold, weight, sign, band, tier boundary — a belief, not a bug
    "NA",           # not applicable (types B and D have no fixable substrate)
)

DISPOSITIONS = (
    "FIX_NOW",      # A-mechanical. Fires at n=1.
    "PEND",         # A-judgment and C. Fires at CONFIRMATIONS_REQUIRED.
    "BOUNDARY",     # B. Never patched. Escalates to bet-selection at CONFIRMATIONS_REQUIRED.
    "VARIANCE",     # D. Never patched. Escalates to distribution review at same.
)

STATES = ("OPEN", "RIPE", "PROPOSED", "SHIPPED", "REJECTED", "RETIRED")

# THE THRESHOLD. Owner: "I think maximum three." Three INDEPENDENT confirmations.
# Frozen as a prior, not fitted — there is no sample that could fit it, which is exactly
# why it must never be quietly moved to 2 because a loss feels urgent.
CONFIRMATIONS_REQUIRED = 3

# FIX_NOW bypasses the counter entirely. A mechanical error has nothing to confirm:
# waiting for a bug to recur twice more is not rigour, it is three known-wrong runs.
FIX_NOW_AT = 1

# Surprise budget: over the trailing window, this share of graded outcomes claimed
# SURPRISE. Above it, the problem is bet selection, not luck. Mirrors the SOP's
# "if Type B dominates -> escalate to a structural review", with a number attached
# so it can actually fire instead of waiting for someone to notice a pattern.
SURPRISE_WINDOW = 10
SURPRISE_BUDGET = 0.30


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(s: str) -> str:
    """Error-class slugs are normalised hard. Two spellings of one class never reach 3."""
    s = re.sub(r"[^a-z0-9]+", "-", str(s).strip().lower()).strip("-")
    if not s:
        raise ValueError("error_class cannot be empty — name the MECHANISM, not the ticker")
    return s


def _read(path: Path) -> list[dict]:
    if not Path(path).exists():
        return []
    return [json.loads(l) for l in Path(path).open(encoding="utf-8") if l.strip()]


def _append(rec: dict, path: Path) -> dict:
    from pre_closed import assert_open
    assert_open(path, ERROR_LOG)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, default=str) + "\n")
    return rec


# ---------------------------------------------------------------------------
# THE SURPRISE GATE
# ---------------------------------------------------------------------------
# Owner, and this is the whole design brief for this section:
#
#   "I want this surprise to not be used as a excuse for the model's failure and the
#    model's inability. So maybe you should give a criteria for this surprise."
#
# He is right to distrust it. "Unobservable" is the single most abusable verdict in the
# SOP — it is the one that ends the inquiry, and the model grades itself. The SOP already
# says Type B "is the one that gets misclassified", and names the guide-freshness gate as
# what happened when it was. But it stated that as a warning, and a warning is not a gate.
#
# So SURPRISE is now a CLAIM THAT MUST BE PROVED ON FOUR LIMBS, every one of which is
# recorded, and any one of which failing means it is NOT a surprise — it is a Type A miss
# wearing a better coat.
SURPRISE_LIMBS = ("unobservable", "not_sourceable", "outside_distribution", "not_recurrent")


@dataclass
class SurpriseClaim:
    """A claim that a miss was genuinely unforecastable. Guilty until proven innocent."""
    ticker: str
    event_date: str
    deciding_variable: str          # WHAT moved it. Free text but MANDATORY and specific.
    first_public_at: str            # WHERE/WHEN that variable first became public.
    idio_pct: float                 # realised beta-stripped open gap
    name_worst_gap: Optional[float] = None   # worst |gap| of the name's last 8 prints
    was_a_model_input: bool = False          # is this variable already on our input list?
    sourceable_pre_print: bool = False       # could we have obtained it at T-1, in principle?
    prior_claims: int = 0                    # times SURPRISE was already claimed here

    def evaluate(self) -> dict:
        """Return {limb: bool} + verdict. All four must pass."""
        limbs = {}

        # LIMB 1 — UNOBSERVABLE. The deciding variable must be named, and named
        # specifically. "sentiment", "the guide", "macro" are refused: an unnameable
        # cause is an unexamined one, and this limb is where the inquiry usually stops.
        vague = {"sentiment", "macro", "the guide", "guidance", "the market",
                 "positioning", "unknown", "n/a", "none", ""}
        named = self.deciding_variable.strip().lower() not in vague and \
            len(self.deciding_variable.strip()) >= 12
        limbs["unobservable"] = bool(named and self.first_public_at.strip()
                                     and not self.was_a_model_input)

        # LIMB 2 — NOT SOURCEABLE. If we could have fetched it at T-1 and did not,
        # that is Type A sourcing, which is FIXABLE, and calling it a surprise is the
        # exact excuse being guarded against. Note the asymmetry: this limb is about
        # what was OBTAINABLE, not about what we happened to obtain.
        limbs["not_sourceable"] = not self.sourceable_pre_print

        # LIMB 3 — OUTSIDE THE NAME'S OWN DISTRIBUTION. A -6% gap on a name that gaps
        # 6% every quarter is not a surprise, it is Tuesday. Type D — ordinary variance —
        # is ALSO not an excuse; it is simply "no evidence either way". This limb keeps
        # the two apart. Bar: worse than the name's own worst of its last 8 prints.
        if self.name_worst_gap is None:
            limbs["outside_distribution"] = False   # unknown distribution -> cannot claim
        else:
            limbs["outside_distribution"] = abs(self.idio_pct) > abs(self.name_worst_gap)

        # LIMB 4 — NOT RECURRENT. THIS IS THE ANTI-EXCUSE LIMB AND IT IS THE POINT.
        # The second time the same thing blindsides us it was not unforecastable; it was
        # a known blind spot we declined to close. AMKR's forward guide was called
        # unobservable once, legitimately. A second guide-down on the same mechanism is
        # a Type A sourcing failure and must be worked, not absolved.
        limbs["not_recurrent"] = self.prior_claims == 0

        ok = all(limbs.values())
        return {
            "limbs": limbs,
            "verdict": "SURPRISE" if ok else "NOT_SURPRISE",
            "failed_limbs": [k for k, v in limbs.items() if not v],
            # The consequence of failing, stated at claim time so it cannot be negotiated
            # afterwards. A failed surprise claim is a Type A miss with a PEND disposition.
            "reclassify_to": None if ok else ("A", "JUDGMENT" if limbs["unobservable"] else "MECHANICAL"),
        }


def surprise_rate(path: Path = ERROR_LOG, window: int = SURPRISE_WINDOW) -> dict:
    """Share of the trailing `window` graded observations that claimed SURPRISE.

    Above SURPRISE_BUDGET the model is not unlucky, it is betting on unobservables —
    a bet-SELECTION problem, which no amount of input work fixes. Escalate.
    """
    obs = [r for r in _read(path) if r.get("type") == "observation"]
    tail = obs[-window:]
    if not tail:
        return {"n": 0, "rate": None, "over_budget": False}
    n_surprise = sum(1 for r in tail if r.get("surprise", {}).get("verdict") == "SURPRISE")
    rate = n_surprise / len(tail)
    return {"n": len(tail), "n_surprise": n_surprise, "rate": round(rate, 3),
            "budget": SURPRISE_BUDGET, "over_budget": rate > SURPRISE_BUDGET}


# ---------------------------------------------------------------------------
# OBSERVATIONS
# ---------------------------------------------------------------------------

def _disposition(failure_type: str, subtype: str) -> str:
    if failure_type == "A":
        return "FIX_NOW" if subtype == "MECHANICAL" else "PEND"
    if failure_type == "C":
        return "PEND"
    if failure_type == "B":
        return "BOUNDARY"
    return "VARIANCE"       # D


def observe(ticker: str, event_date: str, sector: str, error_class: str, *,
            axis: str, failure_type: str, subtype: str = "NA",
            deciding_variable: str = "", note: str = "",
            correct: Optional[bool] = None, idio_pct: Optional[float] = None,
            thesis_confirmed: Optional[bool] = None,
            surprise: Optional[dict] = None, path: Path = ERROR_LOG) -> dict:
    """Record one graded event's contribution to an error class.

    WINS ARE RECORDED TOO, with correct=True. Two reasons, both load-bearing:
      1. Limb 2 of the Abstraction Test needs to know which trades a proposed fix would
         BREAK, and that list cannot be reconstructed from a log of failures only.
      2. A ledger that only records losses cannot ever show a class getting better, so
         nothing is ever RETIRED and the gates accumulate forever — which is precisely
         the pathology the SOP's preamble describes.
    """
    if axis not in AXES:
        raise ValueError(f"axis must be one of {AXES}")
    if failure_type not in FAILURE_TYPES:
        raise ValueError(f"failure_type must be one of {FAILURE_TYPES}")
    if subtype not in SUBTYPES:
        raise ValueError(f"subtype must be one of {SUBTYPES}")
    if failure_type == "A" and subtype == "NA":
        raise ValueError("a Type A miss MUST declare MECHANICAL or JUDGMENT — that split "
                         "is what decides whether it ships now or waits for 3")
    if failure_type in ("B", "D") and not deciding_variable.strip():
        raise ValueError(f"Type {failure_type} REFUSED without a named deciding variable. "
                         "'Unobservable' with nothing named is where the inquiry stops "
                         "and the excuse starts (SOP Step 2).")

    cls = _slug(error_class)
    rec = {
        "type": "observation",
        "ts": _now(),
        "ticker": ticker.upper(),
        "event_date": event_date,
        "sector": (sector or "UNKNOWN").upper(),
        "error_class": cls,
        "axis": axis,
        "failure_type": failure_type,
        "subtype": subtype,
        "disposition": _disposition(failure_type, subtype),
        "deciding_variable": deciding_variable,
        "correct": correct,
        # THESIS_CONFIRMED — did it move for the reason we predicted? The SOP has listed
        # this as a MANDATORY ledger field since 2026-07-29 and it has been written on
        # ZERO of 60 outcome rows. It is not "recorded and never consulted"; it was never
        # recorded. Limb 2 is now keyed to it (see dispose), so from here it does real
        # work. None = never attributed, which is NOT the same as False.
        "thesis_confirmed": thesis_confirmed,
        "idio_pct": idio_pct,
        "surprise": surprise or {},
        "note": note,
        # THE INDEPENDENCE KEY. Confirmations are counted over DISTINCT values of this.
        # Three semis on one night share a key and therefore count once.
        "independence_key": f"{(sector or 'UNKNOWN').upper()}|{event_date}",
    }
    rec["id"] = hashlib.sha1(
        f"{cls}|{ticker}|{event_date}|{axis}".encode()).hexdigest()[:10]
    return _append(rec, path)


# ---------------------------------------------------------------------------
# THE PENDING BOARD
# ---------------------------------------------------------------------------

def _class_rows(path: Path = ERROR_LOG) -> dict:
    """Fold the log into per-class state."""
    rows = _read(path)
    # A class is confirmed by a row whose MECHANISM failed, which is NOT the same as a row
    # that lost money. `correct` grades the SIGN; `thesis_confirmed` grades the READ, and
    # the SOP is explicit that this is attribution, not P&L. Gating on `correct` alone meant
    # a mechanism FIRST observed on a WINNING call created no class at all - the row landed
    # in errors.jsonl and was invisible to board/pending/ripe/show. AEO 2026-09-09 is the
    # case: DOWN was correct and the thesis (a tariff-refund basis change in the guide) was
    # never seen. A loop built because "when your results are wrong, you do nothing" was
    # doing nothing when the results were RIGHT and the thesis was wrong.
    # A win with thesis_confirmed True or None (unattributed) stays limb-2 material only.
    def _mechanism_failed(r):
        return r.get("correct") is not True or r.get("thesis_confirmed") is False
    obs = [r for r in rows if r.get("type") == "observation" and _mechanism_failed(r)]
    wins = [r for r in rows if r.get("type") == "observation" and not _mechanism_failed(r)]
    dispo = [r for r in rows if r.get("type") == "disposition"]

    classes: dict = {}
    for r in obs:
        c = classes.setdefault(r["error_class"], {
            "error_class": r["error_class"], "observations": [], "keys": set(),
            "sectors": set(), "tickers": set(), "state": "OPEN", "history": [],
        })
        c["observations"].append(r)
        c["keys"].add(r["independence_key"])
        c["sectors"].add(r["sector"])
        c["tickers"].add(r["ticker"])

    for d in dispo:
        c = classes.get(d.get("error_class"))
        if c:
            c["state"] = d.get("state", c["state"])
            c["history"].append(d)

    for name, c in classes.items():
        latest = c["observations"][-1]
        c["disposition"] = latest["disposition"]
        c["axis"] = latest["axis"]
        c["failure_type"] = latest["failure_type"]
        c["subtype"] = latest["subtype"]
        c["confirmations"] = len(c["keys"])          # INDEPENDENT count
        c["raw_hits"] = len(c["observations"])       # total, for honesty about clustering
        c["required"] = FIX_NOW_AT if c["disposition"] == "FIX_NOW" else CONFIRMATIONS_REQUIRED
        c["wins_touching_class"] = [w for w in wins if w["error_class"] == name]
        if c["state"] in ("OPEN", "RIPE"):
            c["state"] = "RIPE" if c["confirmations"] >= c["required"] else "OPEN"
        # what a RIPE class actually demands — NOT always a patch
        c["required_response"] = {
            "FIX_NOW":  "FIX the input or the scoring now. Abstraction Test still applies.",
            "PEND":     "PROPOSE a change. Must pass BOTH Abstraction Test limbs + sign-off.",
            "BOUNDARY": "DO NOT PATCH. Ask the bet-selection question: should this model "
                        "be taking this bet, on this name/sector, at all?",
            "VARIANCE": "DO NOT PATCH. Ask the distribution question: is the expected-move "
                        "model wrong, or is there genuinely no edge here yet?",
        }[c["disposition"]]
        c["keys"] = sorted(c["keys"])
        c["sectors"] = sorted(c["sectors"])
        c["tickers"] = sorted(c["tickers"])
    return classes


def pending(path: Path = ERROR_LOG) -> list[dict]:
    """Open classes, most-confirmed first. This is the board to read at every /post."""
    cs = [c for c in _class_rows(path).values() if c["state"] == "OPEN"]
    return sorted(cs, key=lambda c: (-c["confirmations"], c["error_class"]))


def ripe(path: Path = ERROR_LOG) -> list[dict]:
    """Classes that have hit their bar and now DEMAND a response."""
    cs = [c for c in _class_rows(path).values() if c["state"] == "RIPE"]
    return sorted(cs, key=lambda c: (-c["confirmations"], c["error_class"]))


def dispose(error_class: str, state: str, *, rationale: str, mechanism: str = "",
            breaks_confirmed: Optional[list] = None,
            repairs_confirmed: Optional[list] = None,
            breaks_unattributed: Optional[list] = None,
            abstraction_limb1: Optional[bool] = None,
            by: str = "", path: Path = ERROR_LOG) -> dict:
    """Move a class to PROPOSED / SHIPPED / REJECTED / RETIRED.

    ================================================================================
    LIMB 2, REWRITTEN v1.0.1 — IT WAS PROTECTING THE WRONG OBJECT.
    ================================================================================
    The old clause vetoed any fix that broke a previously **WINNING** trade. That is
    incoherent inside this system's own epistemology, which states plainly:

        "A winning trade can be a wrong thesis. A losing trade can be a right thesis.
         P&L is not truth; attribution is."

    Limb 2 then turned around and **sanctified P&L wins**. Some fraction of those
    winners were right for the wrong reason, and breaking one of those costs nothing —
    you are removing a coincidence, not an edge.

    So the fix is NOT veto -> disclosure. It is a change of target:

        **Limb 2 protects trades whose thesis was CONFIRMED BY ATTRIBUTION,
        not trades that made money.**

    That loosens the ratchet and makes it principled at the same time. It is not a
    weakening of the test; it is aiming it.

    AND THE MISSING SYMMETRY. The old limb had a veto for BREAKING a winner and no
    credit for REPAIRING a loser, so a change converting three losses to wins and one
    win to a loss was rejected. That is a ratchet toward permanence, not overfitting
    protection. The full flip set is now reported BOTH ways, and the veto fires only
    when a change **breaks a confirmed thesis and repairs nothing.**

    🔴 THE HARD CONSTRAINT, OR THIS BECOMES AN OVERFITTING MACHINE.
    At n~11 THE FLIP SET IS THE TRAINING SET. The net count is evidence about the COST
    of a change. **It is never the reason to ship one.** The mechanism claim stays
    primary: a fix with a good net count and no mechanism is refused here.

    UNATTRIBUTED TRADES. `thesis_confirmed` is None on only SOME rows (it was unwritten
    early on; as of 2026-09-10 the log carries 10 False / 2 True / 2 None). The claim
    that it is "None on every historical row" was true when written and is no longer -
    a moving fact baked into a doc. An unattributed winner gets **disclosure, not
    veto** — you cannot claim protection for a thesis you never recorded. They are
    listed in `breaks_unattributed` so the choice is visible rather than silent.
    """
    if state not in STATES:
        raise ValueError(f"state must be one of {STATES}")
    if state != "SHIPPED":
        return _append({"type": "disposition", "ts": _now(),
                        "error_class": _slug(error_class), "state": state,
                        "rationale": rationale, "by": by}, path)

    breaks_confirmed = list(breaks_confirmed or [])
    repairs_confirmed = list(repairs_confirmed or [])
    breaks_unattributed = list(breaks_unattributed or [])

    if not mechanism.strip():
        raise ValueError(
            "REFUSED: name the MECHANISM this fix corrects. At this sample size the flip "
            "set is the training set, so a favourable net count is never sufficient — "
            "every component must be justifiable by mechanism alone.")
    if not abstraction_limb1:
        raise ValueError(
            "REFUSED: Abstraction Limb 1 — would this have PREVENTED the last failure of "
            "the same type? If no, it is a symptom patch (SOP Step 5).")
    # LIMB 2, aimed at theses rather than P&L.
    if breaks_confirmed and not repairs_confirmed:
        raise ValueError(
            f"REFUSED by Limb 2: this breaks CONFIRMED theses {breaks_confirmed} and "
            f"repairs none. Note this is about ATTRIBUTION, not P&L — a fix that breaks "
            f"only trades that were right for the wrong reason is not blocked here.")
    if not (breaks_confirmed or repairs_confirmed or breaks_unattributed):
        raise ValueError(
            "REFUSED: the flip set is empty, which means it was not computed. Re-score "
            "the ledger under both arithmetics and state what moves — 'none checked' is "
            "not the same as 'none broken'.")
    return _append({"type": "disposition", "ts": _now(),
                    "error_class": _slug(error_class), "state": state,
                    "rationale": rationale, "mechanism": mechanism, "by": by,
                    "abstraction_test": {
                        "limb1_prevents_last_failure": abstraction_limb1,
                        "limb2_target": "CONFIRMED THESES, not P&L winners",
                        "breaks_confirmed": breaks_confirmed,
                        "repairs_confirmed": repairs_confirmed,
                        "breaks_unattributed": breaks_unattributed,
                        "net_note": "COST evidence only — never the reason to ship"}}, path)


def render(path: Path = ERROR_LOG) -> str:
    L = [f"PRE ERROR LEDGER v{__version__}   (independent confirmations required: "
         f"{CONFIRMATIONS_REQUIRED}; mechanical bugs fire at {FIX_NOW_AT})", "=" * 78]
    r = ripe(path)
    if r:
        L.append("\n🔴 RIPE — these demand a response NOW")
        for c in r:
            L.append(f"  {c['error_class']:<38} {c['confirmations']}/{c['required']}  "
                     f"[{c['disposition']}] type {c['failure_type']}/{c['subtype']} "
                     f"axis {c['axis']}")
            L.append(f"      sectors {','.join(c['sectors'])}  names {','.join(c['tickers'])}"
                     + (f"  (raw hits {c['raw_hits']} — clustered)"
                        if c['raw_hits'] > c['confirmations'] else ""))
            L.append(f"      -> {c['required_response']}")
    p = pending(path)
    if p:
        L.append("\n⏳ PENDING — accumulating, no action permitted yet")
        for c in p:
            L.append(f"  {c['error_class']:<38} {c['confirmations']}/{c['required']}  "
                     f"[{c['disposition']}] type {c['failure_type']}/{c['subtype']} "
                     f"axis {c['axis']}  names {','.join(c['tickers'])}"
                     + (f"  (raw {c['raw_hits']}, clustered to {c['confirmations']})"
                        if c['raw_hits'] > c['confirmations'] else ""))
    if not r and not p:
        L.append("\n  (no open error classes)")
    s = surprise_rate(path)
    if s["n"]:
        flag = "  🔴 OVER BUDGET — this is bet SELECTION, not luck" if s["over_budget"] else ""
        L.append(f"\nSURPRISE RATE  {s['n_surprise']}/{s['n']} = {s['rate']:.0%} "
                 f"(budget {SURPRISE_BUDGET:.0%}){flag}")
    return "\n".join(L)


def main(argv=None) -> int:
    # The board is STEP 1 of the /pre runbook ("what is this model currently known to get
    # wrong?"). On a stock Windows console stdout is cp1252 and the PENDING glyph (U+23F3)
    # raised UnicodeEncodeError, so the ONE command that surfaces a RIPE class before a
    # forecast is frozen died on every plain run. A control that cannot print is not a
    # control. errors="replace" so a future glyph degrades instead of killing the board.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    import argparse
    ap = argparse.ArgumentParser(description="PRE error ledger")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("board", help="the full pending + ripe board (default view)")
    sub.add_parser("pending", help="accumulating classes only")
    sub.add_parser("ripe", help="classes that demand a response")
    sh = sub.add_parser("show", help="every observation in one class")
    sh.add_argument("error_class")
    args = ap.parse_args(argv)

    if args.cmd == "show":
        c = _class_rows().get(_slug(args.error_class))
        if not c:
            print(f"no such class: {args.error_class}")
            return 1
        print(f"{c['error_class']}  [{c['state']}]  {c['confirmations']}/{c['required']} "
              f"independent  ({c['raw_hits']} raw)")
        print(f"  -> {c['required_response']}")
        for o in c["observations"]:
            print(f"  {o['event_date']}  {o['ticker']:<6} {o['sector']:<10} "
                  f"{o['axis']:<10} type {o['failure_type']}/{o['subtype']}  "
                  f"{o['deciding_variable'][:60]}")
        for w in c["wins_touching_class"]:
            print(f"  WIN  {w['event_date']}  {w['ticker']:<6} — limb-2 check must not break this")
        return 0
    if args.cmd == "pending":
        for c in pending():
            print(f"{c['error_class']:<38} {c['confirmations']}/{c['required']}")
        return 0
    if args.cmd == "ripe":
        for c in ripe():
            print(f"{c['error_class']:<38} {c['confirmations']}/{c['required']}  "
                  f"{c['required_response']}")
        return 0
    print(render())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
