"""
PRE DOSSIER — the per-name memory that makes the next look better than the last.
================================================================================
Built 2026-08-09 on owner instruction:

    "I want, like, ... they support each other. After each session, it's not just a
     one time off thing. It's a recurring thing. They can build up to each other.
     So I want you to keep building building building until this model is good."

WHAT WAS ACTUALLY MISSING. PRE had two records and neither compounds per NAME:
  * ledger.jsonl    — rows keyed by entry id, read in aggregate for the scorecard
  * forecasts.jsonl — the same shape for the prediction layer
Both are event logs optimised for scoring the MODEL. Nothing was optimised for the
question actually asked at T-1 of the next print: **what do we already know about how
THIS company behaves into earnings?** So every quarter started from zero, and the same
name could be blindsided by the same mechanism twice without anything noticing. AMKR's
forward guide is the worked example: it was called unobservable once, correctly — and
nothing existed that would have made the SECOND one observable.

THE DOSSIER IS READ AT /pre AND WRITTEN AT /post.
It carries no portfolio data of any kind — only PRE's own history for that ticker — so
reading it inside the BLIND chat is safe by construction. That is deliberate: it is the
one form of memory the blind half is allowed to have.

RETENTION — owner's rule, implemented literally:

    "last five. So last five earnings you keep as a backlog. If past five, you delete
     automatically. Make it permanent. Make it a system thing."

`MAX_EVENTS = 5`, enforced on every write, permanently and without asking. The sixth
event pushes the oldest out.

ONE DELIBERATE DEVIATION, and it is flagged rather than assumed. A purged event does not
vanish — its COUNTERS are folded into a `rollup` block first: how many events, how many
called right, mean |gap|, and the recurring deciding variables. About 200 bytes, fixed
size forever, versus ~2KB for a full event. The reason is that the whole point of this
file is to catch a mechanism that keeps recurring, and a hard delete would make a blind
spot invisible at exactly the moment it became provable — the sixth occurrence would read
as the first. Detail is deleted; the fact that it happened is not. If the owner wants
that gone too, delete the two rollup lines and nothing else changes.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

__version__ = "1.0.0"

DOSSIER_DIR = Path(__file__).with_name("dossiers")

# THE RETENTION RULE. Owner-set, permanent, enforced on every write.
MAX_EVENTS = 5


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def path_for(ticker: str, root: Path = DOSSIER_DIR) -> Path:
    t = re.sub(r"[^A-Z0-9.\-]", "", ticker.upper())
    if not t:
        raise ValueError("bad ticker")
    return Path(root) / f"{t}.json"


def load(ticker: str, root: Path = DOSSIER_DIR) -> dict:
    p = path_for(ticker, root)
    if not p.exists():
        return {"ticker": ticker.upper(), "version": __version__, "events": [],
                "rollup": {"purged_events": 0, "purged_correct": 0,
                           "purged_abs_gap_sum": 0.0, "recurring_variables": {}},
                "standing_notes": []}
    return json.loads(p.read_text(encoding="utf-8"))


def _fold_into_rollup(d: dict, ev: dict) -> None:
    """Compress a purged event to counters. See the module docstring for why."""
    r = d["rollup"]
    r["purged_events"] += 1
    if ev.get("forecast_correct") is True:
        r["purged_correct"] += 1
    if ev.get("idio_pct") is not None:
        r["purged_abs_gap_sum"] = round(r["purged_abs_gap_sum"] + abs(ev["idio_pct"]), 3)
    dv = (ev.get("deciding_variable") or "").strip().lower()[:60]
    if dv:
        r["recurring_variables"][dv] = r["recurring_variables"].get(dv, 0) + 1


def record(ticker: str, event_date: str, *, sector: str = "",
           forecast_direction: str = "", forecast_conviction: str = "",
           forecast_basis: str = "", regime: str = "", trade_stance: str = "",
           expected_move: Optional[float] = None, idio_pct: Optional[float] = None,
           forecast_correct: Optional[bool] = None, failure_type: str = "",
           deciding_variable: str = "", surprise: bool = False,
           error_classes: Optional[list] = None, lesson: str = "",
           root: Path = DOSSIER_DIR) -> dict:
    """Append one graded event to a name's dossier and enforce the 5-event cap.

    IDEMPOTENT on event_date: re-running /post does not duplicate the quarter.
    """
    d = load(ticker, root)
    ev = {
        "event_date": event_date,
        "logged_at": _now(),
        "sector": (sector or "").upper(),
        "forecast": {"direction": forecast_direction, "conviction": forecast_conviction,
                     "basis": forecast_basis, "regime": regime,
                     "expected_move": expected_move},
        "trade_stance": trade_stance,
        "idio_pct": idio_pct,
        "forecast_correct": forecast_correct,
        "failure_type": failure_type,
        "deciding_variable": deciding_variable,
        "surprise": surprise,
        "error_classes": error_classes or [],
        # ONE LINE, and it must be about the NAME, not the model. "This company guides
        # conservatively and beats" is dossier material. "The washout term is too loud"
        # is an error class and belongs in errors.jsonl.
        "lesson": lesson,
    }
    d["events"] = [e for e in d["events"] if e.get("event_date") != event_date]
    d["events"].append(ev)
    d["events"].sort(key=lambda e: e.get("event_date") or "")

    while len(d["events"]) > MAX_EVENTS:
        _fold_into_rollup(d, d["events"].pop(0))

    d["last_updated"] = _now()
    d["version"] = __version__
    p = path_for(ticker, root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, indent=2, default=str), encoding="utf-8")
    return d


def add_standing_note(ticker: str, note: str, root: Path = DOSSIER_DIR) -> dict:
    """A durable behavioural fact about the company that outlives any single quarter.

    NOT capped by MAX_EVENTS — that cap is on event detail. "Reports FY guide with Q4,
    not Q3" is true until the company changes practice, and losing it after five
    quarters would recreate the exact amnesia this file exists to end. Keep these few
    and keep them falsifiable.
    """
    d = load(ticker, root)
    if note not in d["standing_notes"]:
        d["standing_notes"].append(note)
    d["last_updated"] = _now()
    p = path_for(ticker, root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, indent=2, default=str), encoding="utf-8")
    return d


def brief(ticker: str, root: Path = DOSSIER_DIR) -> str:
    """The T-1 read. Called at the TOP of /pre, before any forecast is formed.

    Deliberately short. This is prior context, not a second opinion — it must not
    become a channel through which the last quarter's outcome anchors this quarter's
    call. It states what happened; it does not recommend.
    """
    d = load(ticker, root)
    evs, r = d["events"], d["rollup"]
    if not evs and not r["purged_events"]:
        return f"{ticker.upper()}: no PRE history. FIRST LOOK — no prior to lean on."

    L = [f"{ticker.upper()} — PRE dossier ({len(evs)} kept"
         + (f", {r['purged_events']} purged to counters" if r["purged_events"] else "") + ")"]
    n_ok = sum(1 for e in evs if e.get("forecast_correct") is True)
    n_graded = sum(1 for e in evs if e.get("forecast_correct") is not None)
    if n_graded:
        L.append(f"  forecast record on this name: {n_ok}/{n_graded} kept"
                 + (f"  (+{r['purged_correct']}/{r['purged_events']} purged)"
                    if r["purged_events"] else ""))
    for e in evs:
        f = e["forecast"]
        got = f"{e['idio_pct']:+.2f}%" if e.get("idio_pct") is not None else "ungraded"
        mark = {True: "HIT", False: "MISS", None: "  ?"}[e.get("forecast_correct")]
        L.append(f"  {e['event_date']}  said {f.get('direction','?'):<4} "
                 f"{f.get('conviction','?'):<8} -> {got:>9}  {mark}"
                 + (f"  [{e['failure_type']}]" if e.get("failure_type") else "")
                 + ("  SURPRISE" if e.get("surprise") else ""))
        if e.get("deciding_variable"):
            L.append(f"        moved on: {e['deciding_variable']}")
        if e.get("lesson"):
            L.append(f"        lesson: {e['lesson']}")
    rec = {k: v for k, v in r["recurring_variables"].items() if v >= 2}
    if rec:
        L.append("  RECURRING deciding variables (>=2, incl. purged): "
                 + "; ".join(f"{k} x{v}" for k, v in sorted(rec.items(), key=lambda kv: -kv[1])))
    for n in d["standing_notes"]:
        L.append(f"  STANDING: {n}")
    return "\n".join(L)


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="PRE per-name dossier")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("brief", help="the T-1 read for one name")
    b.add_argument("ticker")
    sub.add_parser("list", help="every name with a dossier")
    args = ap.parse_args(argv)
    if args.cmd == "brief":
        print(brief(args.ticker))
        return 0
    if not DOSSIER_DIR.exists():
        print("(no dossiers yet)")
        return 0
    for p in sorted(DOSSIER_DIR.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        print(f"{d['ticker']:<8} {len(d['events'])} kept  "
              f"{d['rollup']['purged_events']} purged  "
              f"updated {str(d.get('last_updated',''))[:10]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
