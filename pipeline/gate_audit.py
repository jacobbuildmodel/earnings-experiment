"""D016 v1 - the Season A gate audit, counts only (registry/D016_gate_audit_v1.md).

    python pipeline/gate_audit.py seasonA              # interim run: analysis/d016/gate_audit_seasonA_interim_<date>.*
    python pipeline/gate_audit.py seasonA --decision   # the decision run, at or after Fri 2026-10-23 16:00 ET, once

It reads events/<season>/*/gate.json and option_chain.json and nothing else: every read goes through read_json(),
which refuses any other file name and anything under outcomes/ or paper/ (tests/test_gate_audit.py proves it).
No standard-library module here opens a file behind its back. It imports nothing from pipeline/ on purpose:
common.registry() opens registry files.
"""
import datetime
import glob
import json
import os
import statistics
import sys
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ET = ZoneInfo("America/New_York")
ALLOWED = {"gate.json", "option_chain.json"}
FENCED = {"outcomes", "paper", "shadow"}
DECISION_FROM = datetime.datetime(2026, 10, 23, 16, 0, tzinfo=ET)

# D003 v4 s2, copied (D016 §2): the audit never reads the registry, so it cannot drift with it unseen
IM_MIN, LEG_CAP, OI_MIN, OI_BAND, FLOOR = 0.04, 0.10, 500, 0.02, 0.10
PRE_CHAIN = ("unconfirmed", "outside_window", "printed_before_entry", "no_expiry", "chain_error")
CHECKS = ("no_quote", "low_implied_move", "wide_spread", "thin_oi")  # D003 v4 order
ALTS = ("A0", "A1", "A2", "A3", "A4")
SENS = [("leg", 0.125), ("leg", 0.15), ("leg", 0.20), ("straddle", 0.125), ("straddle", 0.15)]
SIMPLER = ("A2", "A1", "A3", "A4")  # D016 §5.3 tie order


def read_json(path):
    """The only door to the disk. D016 §1: gate.json and option_chain.json, never outcomes/, paper/ or shadow/."""
    parts = set(os.path.normpath(os.path.abspath(path)).split(os.sep))
    if os.path.basename(path) not in ALLOWED or parts & FENCED:
        raise PermissionError(f"D016 reads only {sorted(ALLOWED)}; refused {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def quoted(leg):
    return leg is not None and (leg.get("bid") or 0) > 0 and (leg.get("ask") or 0) > (leg.get("bid") or 0)


def mid(leg):
    return (leg["bid"] + leg["ask"]) / 2


def leg_at(rows, strike):
    for r in rows:
        if r.get("strike") == strike:
            return r
    return None


def oi_band(chain, spot, keep):
    """D003 v4: call + put open interest within +-2% of spot, always including the strikes in `keep`."""
    total = 0.0
    for r in chain["calls"] + chain["puts"]:
        if abs(r["strike"] / spot - 1) <= OI_BAND or r["strike"] in keep:
            oi = r.get("openInterest")
            total += 0 if oi is None or oi != oi else oi  # NaN counts as 0, as pandas fillna(0) did
    return total


def reading(chain, spot, strike, oi_keep):
    """Every number a check needs, at one strike."""
    c, p = leg_at(chain["calls"], strike), leg_at(chain["puts"], strike)
    r = {"strike": strike, "quoted": quoted(c) and quoted(p), "oi_sum": oi_band(chain, spot, oi_keep)}
    if r["quoted"]:
        sc, sp = c["ask"] - c["bid"], p["ask"] - p["bid"]
        r.update(implied_move=(mid(c) + mid(p)) / spot, leg_spread={"call": sc / mid(c), "put": sp / mid(p)},
                 leg_dollar={"call": sc, "put": sp}, straddle_spread=(sc + sp) / (mid(c) + mid(p)))
    return r


def spread_ok(r, test, cap=LEG_CAP):
    if test == "straddle":
        return r["straddle_spread"] <= cap
    floor = FLOOR if test == "floor" else None
    return all(r["leg_spread"][k] <= cap or (floor is not None and r["leg_dollar"][k] <= floor) for k in ("call", "put"))


def failures(r, test="leg", cap=LEG_CAP):
    """Every failing check at this reading, in D003 v4 order (D016 §2: all of them, not only the first)."""
    if not r["quoted"]:
        return ["no_quote"] + (["thin_oi"] if r["oi_sum"] < OI_MIN else [])
    out = []
    if r["implied_move"] < IM_MIN:
        out.append("low_implied_move")
    if not spread_ok(r, test, cap):
        out.append("wide_spread")
    if r["oi_sum"] < OI_MIN:
        out.append("thin_oi")
    return out


def two_nearest(chain, spot):
    both = sorted({r["strike"] for r in chain["calls"]} & {r["strike"] for r in chain["puts"]})
    return sorted(both, key=lambda k: (abs(k - spot), k))[:2]


def evaluate(gate, chain):
    """One event under A0-A4 and the sensitivity caps."""
    o = gate["options"]
    spot, strike = o["spot"], o["strike"]
    base = reading(chain, spot, strike, {strike})
    row = {"ticker": gate["ticker"], "report_date": gate["report_date"], "spot": spot, "expiry": o.get("expiry"),
           "expiry_gap": o.get("expiry_sessions_after_reaction"), "stored": [gate["status"], gate.get("reason")],
           "reading": base, "fails": failures(base)}
    expect = ("INELIGIBLE", row["fails"][0]) if row["fails"] else ("PASS", None)
    row["reproduced"] = expect == tuple(row["stored"])
    pick = {"A0": (base, "leg"), "A2": (base, "floor"), "A3": (base, "straddle")}
    alt = {k: {"pass": not failures(r, t), "strike": r["strike"]} for k, (r, t) in pick.items()}
    near = [reading(chain, spot, k, {strike, k}) for k in two_nearest(chain, spot)]
    for k, test in (("A1", "leg"), ("A4", "straddle")):
        ok = [r for r in near if not failures(r, test)]
        best = min(ok, key=lambda r: max(r["leg_spread"].values())) if ok else None
        alt[k] = {"pass": best is not None, "strike": best["strike"] if best else None,
                  "reading": best if best and best["strike"] != strike else None}
    row["alt"] = {k: alt[k] for k in ALTS}
    row["sens"] = {f"{t}_{c}": not failures(base, t, c) for t, c in SENS}
    return row


def bucket_price(spot):
    return "< $100" if spot < 100 else ("$100-<$300" if spot < 300 else ">= $300")


def bucket_gap(gap):
    return "unknown" if gap is None else ("<= 5 sessions" if gap <= 5 else "> 5 sessions (monthly)")


def friction(rows, key):
    """Median and max straddle spread, and max leg spread, over the PASS events of one alternative."""
    rs = [r["alt"][key].get("reading") or r["reading"] for r in rows if r["alt"][key]["pass"]] if key in ALTS else rows
    if not rs:
        return {"median_straddle_spread": None, "max_straddle_spread": None, "max_leg_spread": None}
    return {"median_straddle_spread": round(statistics.median(r["straddle_spread"] for r in rs), 4),
            "max_straddle_spread": round(max(r["straddle_spread"] for r in rs), 4),
            "max_leg_spread": round(max(max(r["leg_spread"].values()) for r in rs), 4)}


def decide(rows):
    """D016 §5: counts to a D003 v5 proposal."""
    p = {k: sum(r["alt"][k]["pass"] for r in rows) for k in ALTS}
    gain = {k: p[k] - p["A0"] for k in ALTS}
    cands = [k for k in SIMPLER if gain[k] >= 2]
    if not cands:
        return {"recommend": "keep D003 v4 for Season B", "alternative": None, "pass": p, "gain": gain,
                "why": "no alternative among A1-A4 gains 2 or more PASS over A0 (D016 §5.2)"}
    med = {k: friction(rows, k)["median_straddle_spread"] for k in cands}
    best = sorted(cands, key=lambda k: (-p[k], med[k], SIMPLER.index(k)))[0]
    return {"recommend": f"D003 v5 = {best} from the Season B screen (Jacob's call)", "alternative": best, "pass": p,
            "gain": gain, "why": f"{best} has the most PASS ({p[best]} vs A0 {p['A0']}); ties by median straddle "
                                 "spread, then A2, A1, A3, A4 (D016 §5.3)"}


def audit(season, root=None):
    root = root or ROOT
    rows, pre, skipped = [], [], []
    for gpath in sorted(glob.glob(os.path.join(root, "events", season, "*", "gate.json"))):
        gate = read_json(gpath)
        if gate.get("dry") or not gate.get("in_s2_window"):
            skipped.append(os.path.basename(os.path.dirname(gpath)))
            continue
        o = gate.get("options") or {}
        if gate.get("reason") in PRE_CHAIN or o.get("spot") is None or o.get("strike") is None:
            pre.append({"ticker": gate["ticker"], "report_date": gate["report_date"], "reason": gate.get("reason")})
            continue
        rows.append(evaluate(gate, read_json(os.path.join(os.path.dirname(gpath), "option_chain.json"))))
    return rows, pre, skipped


def summarise(season, rows, pre, skipped, label, now):
    n = len(rows)
    combos = {}
    for r in rows:
        combos[" + ".join(r["fails"]) or "PASS"] = combos.get(" + ".join(r["fails"]) or "PASS", 0) + 1
    cascade = {c: {"failing": sum(c in r["fails"] for r in rows),
                   "only_failing_check": sum(r["fails"] == [c] for r in rows)} for c in CHECKS}
    buckets = {}
    for name, fn in (("share_price", lambda r: bucket_price(r["spot"])), ("expiry_gap", lambda r: bucket_gap(r["expiry_gap"]))):
        b = {}
        for r in rows:
            e = b.setdefault(fn(r), {"events": 0, "PASS": 0, **{c: 0 for c in CHECKS}})
            e["events"] += 1
            e["PASS"] += not r["fails"]
            for c in r["fails"]:
                e[c] += 1
        buckets[name] = b
    alts = {}
    for k in ALTS:
        alts[k] = {"PASS": sum(r["alt"][k]["pass"] for r in rows),
                   "adds": [r["ticker"] for r in rows if r["alt"][k]["pass"] and r["fails"]],
                   "drops": [r["ticker"] for r in rows if not r["alt"][k]["pass"] and not r["fails"]],
                   **friction(rows, k)}
    sens = {}
    for t, c in SENS:
        key = f"{t}_{c}"
        hit = [r for r in rows if r["sens"][key]]
        sens[key] = {"PASS": len(hit), "adds": [r["ticker"] for r in hit if r["fails"]], **friction([r["reading"] for r in hit], None)}
    return {"rule": "registry/D016_gate_audit_v1.md", "season": season, "label": label, "run_et": now.isoformat(),
            "reads_only": sorted(ALLOWED), "events_with_chain": n, "pre_chain": pre, "skipped_not_live": skipped,
            "reproduced": sum(r["reproduced"] for r in rows), "not_reproduced": [r["ticker"] for r in rows if not r["reproduced"]],
            "cascade": cascade, "combinations": combos, "buckets": buckets, "alternatives": alts, "sensitivity": sens,
            "decision": decide(rows) if rows else None, "events": rows}


def pct(x):
    return "-" if x is None else f"{100 * x:.1f}%"


def markdown(s):
    n = s["events_with_chain"]
    out = [f"# D016 gate audit - {s['season']} - {s['label']}", "",
           f"Run {s['run_et'][:16]} ET by `pipeline/gate_audit.py` under `{s['rule']}`. Counts only: it read "
           f"`gate.json` and `option_chain.json` and nothing else. No outcome, P&L, grade or shadow figure is here.", "",
           f"- Events with a chain reading: **{n}**. Failed before the chain: {len(s['pre_chain'])}. "
           f"Not live (dry or outside the window), skipped: {len(s['skipped_not_live'])}.",
           f"- Reproduction of the stored gate: {s['reproduced']} of {n}"
           + (f"; NOT reproduced: {', '.join(s['not_reproduced'])}" if s["not_reproduced"] else "") + ".", "",
           "## A. Every check on every event (D003 v4)", "", "| check | events failing | the only failing check |",
           "|---|---|---|"]
    out += [f"| `{c}` | {v['failing']} | {v['only_failing_check']} |" for c, v in s["cascade"].items()]
    out += ["", "| combination | events |", "|---|---|"]
    out += [f"| {k} | {v} |" for k, v in sorted(s["combinations"].items(), key=lambda kv: -kv[1])]
    for name, title in (("share_price", "share price"), ("expiry_gap", "expiry gap after the reaction day")):
        out += ["", f"## B. Pass rate by {title}", "", "| bucket | events | PASS | rate | " + " | ".join(f"`{c}`" for c in CHECKS) + " |",
                "|---|---|---|---|" + "---|" * len(CHECKS)]
        for b, e in s["buckets"][name].items():
            out.append(f"| {b} | {e['events']} | {e['PASS']} | {pct(e['PASS'] / e['events'])} | "
                       + " | ".join(str(e[c]) for c in CHECKS) + " |")
    names = {"A0": "D003 v4 as run", "A1": "better of the two nearest strikes", "A2": "dollar floor $0.10 a leg",
             "A3": "straddle spread <= 10%", "A4": "A1 + A3"}
    out += ["", "## C. Alternatives the stored chains support", "",
            "| id | rule | PASS | adds | drops | median straddle spread | max straddle spread | max leg spread |",
            "|---|---|---|---|---|---|---|---|"]
    for k, a in s["alternatives"].items():
        out.append(f"| {k} | {names[k]} | {a['PASS']} of {n} | {', '.join(a['adds']) or '-'} | {', '.join(a['drops']) or '-'} | "
                   f"{pct(a['median_straddle_spread'])} | {pct(a['max_straddle_spread'])} | {pct(a['max_leg_spread'])} |")
    out += ["", "Sensitivity (raises the friction ceiling; never recommended by §5):", "",
            "| cap | PASS | adds | median straddle spread | max leg spread |", "|---|---|---|---|---|"]
    for k, a in s["sensitivity"].items():
        out.append(f"| {k.replace('_', ' ')} | {a['PASS']} of {n} | {', '.join(a['adds']) or '-'} | "
                   f"{pct(a['median_straddle_spread'])} | {pct(a['max_leg_spread'])} |")
    d = s["decision"]
    if d:
        out += ["", "## D. The §5 decision rule", "", f"**{d['recommend']}.** {d['why']}.",
                "", "Gains over A0: " + ", ".join(f"{k} {v:+d}" for k, v in d["gain"].items() if k != "A0") + "."]
        if s["label"].startswith("interim"):
            out += ["", "_Interim: this decides nothing. The decision run is the first at or after Fri 2026-10-23 16:00 ET._"]
    out += ["", "## Events", "", "| event | spot | expiry gap | stored | all failing checks | straddle spread | A1 | A2 | A3 | A4 |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for r in s["events"]:
        st = r["stored"][1] or r["stored"][0]
        out.append(f"| {r['ticker']} {r['report_date']} | {r['spot']:.2f} | {r['expiry_gap']} | {st} | "
                   f"{', '.join(r['fails']) or 'PASS'} | {pct(r['reading'].get('straddle_spread'))} | "
                   + " | ".join("PASS" if r["alt"][k]["pass"] else "-" for k in ("A1", "A2", "A3", "A4")) + " |")
    return "\n".join(out) + "\n"


def main(argv):
    season = argv[0]
    now = datetime.datetime.now(ET)
    decision = "--decision" in argv
    if decision and now < DECISION_FROM:
        raise SystemExit(f"the decision run is at or after {DECISION_FROM:%a %Y-%m-%d %H:%M} ET (D016 §6)")
    label = "decision" if decision else f"interim_{now:%Y-%m-%d}"
    rows, pre, skipped = audit(season)
    s = summarise(season, rows, pre, skipped, label, now)
    outdir = os.path.join(ROOT, "analysis", "d016")
    os.makedirs(outdir, exist_ok=True)
    base = os.path.join(outdir, f"gate_audit_{season}_{label}")
    if decision and (os.path.exists(base + ".json") or os.path.exists(base + ".md")):
        raise SystemExit(f"{base}.json already exists: the decision run is write-once (D016 §6)")
    with open(base + ".json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(s, f, indent=1)
    with open(base + ".md", "w", encoding="utf-8", newline="\n") as f:
        f.write(markdown(s))
    print(markdown(s))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
