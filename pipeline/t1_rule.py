"""T1 rule v0 (D006 §7): freeze the rule file from the history study, and score a live event.

    python pipeline/t1_rule.py freeze      # writes registry/T1_rule_v0.json from analysis/history (once)
    python pipeline/t1_rule.py score <season> <TICKER> <YYYY-MM-DD>   # prints T1 for a gated event

Code only; the AI never computes T1 (D005 v2 §7.2). Live factors come from factors.json -> "H" block,
computed at the snapshot by pipeline/history_factors.py, the same code as the history study.
"""
import bisect
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import REGISTRY, ROOT, now_et, registry  # noqa: E402

FACTORS = ["H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "H9", "H10"]
SIGN = {"H1": -1, "H2": -1, "H3": -1, "H4": -1, "H5": 1, "H6": 1, "H7": 1, "H8": 1, "H9": -1, "H10": 1}
MAX_MISSING = 5
RULE_FILE = "T1_rule_v0.json"


def pct(ref, v):
    lo, hi = bisect.bisect_left(ref, v), bisect.bisect_right(ref, v)
    return (lo + 0.5 * (hi - lo)) / len(ref)


def composite(values, ref, factors):
    s, missing = [], 0
    for f in factors:
        v = values.get(f)
        if v is None or not ref.get(f):
            s.append(0.5)
            missing += 1
        else:
            p = pct(ref[f], v)
            s.append(p if SIGN[f] > 0 else 1 - p)
    return sum(s) / len(s), missing


def freeze():
    path = os.path.join(REGISTRY, RULE_FILE)
    if os.path.exists(path):
        raise SystemExit(f"{RULE_FILE} exists - a frozen rule is never rewritten; a change is a new version")
    res = json.load(open(os.path.join(ROOT, "analysis", "history", "study_result.json"), encoding="utf-8"))
    ev = json.load(open(os.path.join(ROOT, "analysis", "history", "events.json"), encoding="utf-8"))["events"]
    q = lambda d: datetime.date.fromisoformat(d).year * 4 + (datetime.date.fromisoformat(d).month - 1) // 3  # noqa: E731
    last = max(q(e["snapshot"]) for e in ev)
    pool = [e for e in ev if last - 3 <= q(e["snapshot"]) <= last]
    ref = {f: sorted(e["factors"][f] for e in pool if e["factors"].get(f) is not None) for f in FACTORS}
    chosen = res["rule_v0"]
    comps = [composite(e["factors"], ref, chosen["factors"]) for e in pool]
    comps = sorted(c for c, m in comps if m <= MAX_MISSING)
    median = comps[len(comps) // 2] if len(comps) % 2 else (comps[len(comps) // 2 - 1] + comps[len(comps) // 2]) / 2
    rule = {
        "id": "T1_rule_v0", "frozen_on_et": now_et().date().isoformat(), "procedure": "D006_history_study_v1",
        "applies_to_seasons": ["seasonA"],
        "status": "FAILED VALIDATION" if chosen["failed_validation"] else "passed validation",
        "rule": chosen["name"], "factors": chosen["factors"], "signs": {f: SIGN[f] for f in chosen["factors"]},
        "decision": "BUY iff composite > reference_median_composite; composite = mean of signed percentile ranks "
                    "against `reference`; a missing factor scores 0.5; > 5 of 10 missing -> T1 null",
        "reference_quarters": f"the four calendar quarters of snapshot sessions ending {last // 4}Q{last % 4 + 1}",
        "reference_n_events": len(pool), "reference_median_composite": median, "reference": ref,
        "history": {k: res[k] for k in ("counts", "R-LIT_train", "R-LIT_validation") if k in res},
        "factor_code": "pipeline/history_factors.py compute()",
    }
    json.dump(rule, open(path, "w", encoding="utf-8", newline="\n"), indent=1)
    print(f"{RULE_FILE}: {chosen['name']} ({rule['status']}), reference {len(pool)} events, median {median:.4f}")


def decide(h_values, season):
    """T1 for one event from its live H factors. Returns the decision.json t1 block."""
    try:
        rule = registry(RULE_FILE)
    except SystemExit:
        return {"decision": None, "note": "rule v0 not frozen"}
    if season not in rule["applies_to_seasons"]:
        return {"decision": None, "note": f"{rule['id']} does not apply to {season}"}
    c, missing = composite(h_values or {}, rule["reference"], rule["factors"])
    if missing > MAX_MISSING:
        return {"decision": None, "rule_version": rule["id"], "note": f"{missing} of 10 factors missing - never guessed"}
    return {"decision": "BUY" if c > rule["reference_median_composite"] else "NO_BUY", "rule_version": rule["id"],
            "composite": c, "threshold": rule["reference_median_composite"], "missing_factors": missing,
            "rule_status": rule["status"]}


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "freeze":
        freeze()
    elif a and a[0] == "score":
        f = json.load(open(os.path.join(ROOT, "events", a[1], f"{a[2].upper()}_{a[3]}", "factors.json"), encoding="utf-8"))
        h = {k: (v or {}).get("value") for k, v in (f.get("factors") or f).items() if k in FACTORS}
        print(json.dumps(decide(h, a[1]), indent=1))
    else:
        raise SystemExit(__doc__)
