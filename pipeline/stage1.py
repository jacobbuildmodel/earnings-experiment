"""Stage 1 review - registry/D017_stage1_review_v1.md. Code only, no AI. INTERIM and descriptive: it uses only the
words D017 §3 fixes and decides nothing (D017 §5).

    python pipeline/stage1.py [SEASON] [--cut YYYY-MM-DD] [--write]

It assembles what is already computed - report.run (D005), shadow.report_ (D009), the D011 report views
(paper_options_report_v2.build) and gate1.health (CHARTER §6) - on the data cut: every event whose exit-A open falls
on or before the cut (D017 §2). Its one new statistic is the excess over SPY: the event's raw exit-A return minus
SPY's open-to-open return (dividends added) over the same entry -> exit-A window, SPY's daily opens from yfinance.

Never shown (D017 §4): C1, any T2-confidence-vs-outcome view (H-T2C's slope, Brier, AUC, calibration), the
confirmatory block, per-name outcomes. report.run and shadow.report_ print their full tables, so their stdout is
swallowed, only the fields named below are read, and guard() refuses an output that carries a banned key.
--write saves outcomes/reports/stage1_<cut>.md and .json; a later run never replaces them (D017 §2), it writes _r2.
--write refuses while any event in the cut is neither graded nor VOID (bug fix 2026-11-03: the first run missed the
10-30 exits, which were not graded yet).
Every input comes through sources(), so tests/test_stage1.py runs the same compute() on synthetic data.
"""
import contextlib
import datetime
import glob
import io
import json
import math
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, now_et, write_json  # noqa: E402

CUT = "2026-10-30"
COST = 0.002             # the 0.20% round trip (D006, D008 §2)
HIST_NET = 0.0065        # D006's net mean: the CONTRADICTS HISTORY line (D017 §3)
MIN_EVENTS, MIN_SESSIONS = 30, 10
BANKED = ("D006", "D007", "D010", "D014")
T2_TRACKS = ("T2", "T2G", "T2R", "T2O")
BANNED = ("probability", "confidence", "brier", "auc", "calibration", "confirmatory", "h-t2c")


# ---------------------------------------------------------------- helpers

@contextlib.contextmanager
def patched(mod, **attrs):
    old = {k: getattr(mod, k) for k in attrs}
    for k, v in attrs.items():
        setattr(mod, k, v)
    try:
        yield
    finally:
        for k, v in old.items():
            setattr(mod, k, v)


def quiet(fn, *a, **kw):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a, **kw)


def mean(xs):
    return float(np.mean(xs)) if len(xs) else None


def ok(x):
    return x is not None and isinstance(x, (int, float)) and not (isinstance(x, float) and math.isnan(x))


def pct(x, d=2, sign=True):
    return (f"{x * 100:+.{d}f}%" if sign else f"{x * 100:.{d}f}%") if ok(x) else "-"


def guard(obj, path=""):
    """D017 §4: no key of the output may name a banned view."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            kl = str(k).lower()
            if any(b in kl for b in BANNED) or kl.startswith(("c1", "h-c1")):
                raise SystemExit(f"D017 §4: {path}/{k} may not be shown at Stage 1")
            guard(v, f"{path}/{k}")
    elif isinstance(obj, list):
        for v in obj:
            guard(v, path)


# ---------------------------------------------------------------- the data cut and the inputs

def load_rows_cut(season, cut):
    """report.load_rows on the cut. A graded event counts when its exit-A open is on or before the cut; a VOID or
    pending one by its exit-A session when it has one, else by its entry session."""
    rows, voids, pending, ineligible = [], {}, 0, 0
    for p in sorted(glob.glob(os.path.join(ROOT, "outcomes", season, "*.json"))):
        o = json.load(open(p, encoding="utf-8"))
        a = (o.get("exits") or {}).get("exit_A") or {}
        if (a.get("exit_session") or o.get("entry_session") or "9999") > cut:
            continue
        if o.get("gate_status") != "PASS":
            ineligible += 1
        elif o.get("void"):
            voids[o["void"]] = voids.get(o["void"], 0) + 1
        elif o.get("graded"):
            rows.append(o)
        else:
            pending += 1
    return rows, voids, pending, ineligible


def shadow_in_cut(e, cut):
    return (((e.get("timing") or {}).get("exit_A") or {}).get("session") or "9999") <= cut


def spy_history(start, end):
    """SPY's daily opens and dividends, yfinance, auto_adjust=False (the prices grade.py uses)."""
    import yfinance as yf
    h = yf.Ticker("SPY").history(start=start, end=end, auto_adjust=False, actions=True)
    opens = {d.strftime("%Y-%m-%d"): float(o) for d, o in zip(h.index, h["Open"])}
    divs = {d.strftime("%Y-%m-%d"): float(v) for d, v in zip(h.index, h["Dividends"]) if v}
    return opens, divs


def spy_return(opens, divs, entry, exit_):
    if entry not in opens or exit_ not in opens:
        return None
    return (opens[exit_] + sum(v for d, v in divs.items() if entry < d <= exit_)) / opens[entry] - 1


def decisions(season, events):
    """The shadow T2 decisions (T2R, T2O) and the recorded cost of every T2 decision, per event. Decisions and
    costs only: no outcome is read here."""
    out = {}
    for ev in events:
        d = {"cost": {}}
        for tr, name, key in (("T2", "decision.json", "t2"), ("T2G", "t2g.json", "t2"), ("T2R", "t2r.json", "t2"),
                              ("T2O", "t2o.json", "t2")):
            p = os.path.join(ROOT, "events", season, ev, name)
            if not os.path.exists(p):
                continue
            blk = json.load(open(p, encoding="utf-8")).get(key) or {}
            if tr in ("T2R", "T2O"):
                d[tr] = blk.get("decision")
            if ok(blk.get("cost_usd_equiv")):
                d["cost"][tr] = float(blk["cost_usd_equiv"])
        out[ev] = d
    return out


def check_py():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "check.py")], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in r.stdout.splitlines()]
    return {"result": next((ln for ln in reversed(lines) if ln.startswith(("PASS", "FAIL"))), "unreadable"),
            "timestamps_line": next((ln for ln in lines if "timestamps:" in ln), "")}


def banked():
    """HYPOTHESES §3 (closed studies): the lines that name each banked decision. Text only, no computation."""
    sec, on = [], False
    for ln in open(os.path.join(ROOT, "HYPOTHESES.md"), encoding="utf-8").read().splitlines():
        if ln.startswith("## "):
            on = ln[3:].lstrip().startswith("3")
        elif on and ln.strip():
            sec.append(ln.strip())
    return {d: [ln for ln in sec if d in ln] for d in BANKED}


def git_head():
    r = subprocess.run(["git", "-C", ROOT, "log", "-1", "--format=%h %cd", "--date=iso", "--", "pipeline/stage1.py"],
                       capture_output=True, text=True)
    return r.stdout.strip() or "uncommitted"


def sources(season, cut):
    """The real inputs, each a plain value or function so a test can pass synthetic ones."""
    import gate1
    import paper
    import paper_options_report_v2 as v2
    outcomes = load_rows_cut(season, cut)
    sp = os.path.join(ROOT, "outcomes", "shadow", season, "graded.json")
    shadow_events = ([e for e in json.load(open(sp, encoding="utf-8"))["events"] if shadow_in_cut(e, cut)]
                     if os.path.exists(sp) else [])
    days = [r["entry_session"] for r in outcomes[0]] + [e["timing"]["entry"]["session"] for e in shadow_events
                                                         if e.get("timing")]
    start = (min(days) if days else cut)
    end = (datetime.date.fromisoformat(cut) + datetime.timedelta(days=7)).isoformat()
    return {"outcomes": outcomes, "shadow": shadow_events, "spy": spy_history(start, end),
            "options_ledgers": {s: v2.load(os.path.join(ROOT, rel)) for s, rel in v2.LEDGERS.items()},
            "shx": v2.shx_rows(season), "recheck": lambda se, cid: v2.recheck.load_cached(se, cid),
            "shares_ledger": json.load(open(os.path.join(ROOT, "paper", "ledger.json"), encoding="utf-8")),
            "official_open": paper.official_open,
            "decisions": decisions(season, [r["event"] for r in outcomes[0]]),
            "health": gate1.health(season), "check": check_py(), "banked": banked(), "code": git_head()}


# ---------------------------------------------------------------- P2: the premium, live

def read(evs):
    """evs: [{"ret", "win", "entry", "exit", "spy"}]. D017 §3: n, sessions, raw and net mean, win rate, excess over
    SPY, a CR1 standard error clustered by entry session and a 95% interval on the net mean."""
    import report
    g = np.array([e["entry"] for e in evs])
    out = {"n": len(evs), "sessions": int(len(set(g)))}
    if not evs:
        return out
    raw = np.array([e["ret"] for e in evs], float)
    net = raw - COST
    exc = [e["ret"] - e["spy"] for e in evs if e.get("spy") is not None]
    out.update({"raw_mean": float(raw.mean()), "net_mean": float(net.mean()),
                "win_rate": float(np.mean([1.0 if e["win"] else 0.0 for e in evs])),
                "excess_spy_mean": mean(exc), "excess_spy_net_mean": mean(exc) - COST if exc else None,
                "excess_spy_n": len(exc)})
    se = float("nan")
    if len(evs) >= 3 and len(set(g)) >= 2:
        _, se, _ = report.ols_k(net, np.ones((len(net), 1)), g, 0)
    out["se_cluster_session"] = se
    out["ci95_net"] = [out["net_mean"] - 1.96 * se, out["net_mean"] + 1.96 * se] if ok(se) else None
    return out


def word(r):
    """D017 §3, in the table's order."""
    if r["n"] < MIN_EVENTS or r["sessions"] < MIN_SESSIONS:
        return "INSUFFICIENT"
    if r.get("ci95_net") and r["ci95_net"][1] < HIST_NET:
        return "CONTRADICTS HISTORY"
    if r["net_mean"] > 0 and ok(r.get("excess_spy_mean")) and r["excess_spy_mean"] > 0:
        return "ALIVE"
    return "NOT YET VISIBLE"


def supports(p1_pass, primary_word):
    """D017 §5: what the evidence supports. The decision is Jacob's."""
    if not p1_pass:
        return "repair first: no new money until the record is clean"
    if primary_word == "CONTRADICTS HISTORY":
        return "no new money: finish Season A on current means and decide at Gate 1"
    return "fund to Gate 1 and Season B: the record is sound and nothing contradicts the premium"


# ---------------------------------------------------------------- P4: execution

def shares_view(ledger, rows, cut, official_open):
    """The median absolute paper fill against the official open, in bp, over real fills of trades closed by the cut.
    The official open is grade.py's exit-A entry price where the event is graded, else paper.official_open."""
    px = {(r["ticker"], (r["exits"]["exit_A"].get("entry_session") or r["entry_session"])): r["exits"]["exit_A"].get("entry")
          for r in rows}
    trades = ledger.get("trades") or {}
    trades = trades.values() if isinstance(trades, dict) else trades
    bps, no_real_fill, unread = [], 0, 0
    for t in trades:
        if (t.get("exit_session") or "9999") > cut:
            continue
        fill = (t.get("buy") or {}).get("filled_avg_price")
        if (t.get("simulated") or {}).get("buy") or fill in (None, ""):
            no_real_fill += 1
            continue
        off = px.get((t.get("ticker"), t.get("entry_session"))) or official_open(t.get("ticker"), t.get("entry_session"))
        if not off:
            unread += 1
            continue
        bps.append(abs(float(fill) / float(off) - 1) * 1e4)
    return {"n": len(bps), "median_abs_bp": float(np.median(bps)) if bps else None, "mean_abs_bp": mean(bps),
            "no_real_fill (simulated or unfilled)": no_real_fill, "official_open_unreadable": unread}


def options_view(season, cut, src):
    import paper_options_report_v2 as v2
    led = {s: ({**lg, "trades": {k: t for k, t in (lg.get("trades") or {}).items()
                                 if (t.get("reaction_session") or "9999") <= cut}} if lg else None)
           for s, lg in src["options_ledgers"].items()}
    vr = v2.build(led, src["shx"], season, now_et(), src["recheck"])
    out = {}
    for s in v2.LEDGERS:
        a = vr.get(s) or {}
        if "by_subset" not in a:
            out[s] = {"note": a.get("note", "no ledger")}
            continue
        trig = a["open_fill_trigger_v1"]
        out[s] = {"trades_in_cut": a["records"],
                  "open_fill_trigger_v1": {"counted": trig.get("counted"), "state": trig.get("state"),
                                           "counts": trig.get("counts")},
                  "pnl_per_spot": {sub: {"real round trips": b["pnl"]["real"]["all"]["common_set"],
                                         "all with a result (simulated legs labelled)":
                                             b["pnl"]["all_with_result (simulated legs labelled)"]["all"]["common_set"]}
                                   for sub, b in a["by_subset"].items() if sub in ("all", "without_DPZ")}}
    return out


# ---------------------------------------------------------------- the review

def compute(season, cut, src):
    import report
    import shadow
    rows, voids, pending, ineligible = src["outcomes"]
    # report.run on the cut. Stage 1 reads none of the factor findings, so they are not computed.
    with patched(report, load_rows=lambda s: src["outcomes"], factor_table=lambda s, r: {}):
        rep = quiet(report.run, season, write=False)
    with patched(shadow, load=lambda p: {"events": src["shadow"]}):
        shrep = quiet(shadow.report_, season, write=False)

    # P1 - truthful record
    n_void = sum(voids.values())
    void_rate = n_void / (len(rows) + n_void) if (rows or n_void) else None
    late = 0 if src["check"]["timestamps_line"].startswith("[ok]") else None
    h = src["health"]
    p1 = {"check_py": src["check"]["result"], "late_freezes": late, "late_freezes_source": src["check"]["timestamps_line"],
          "graded_in_cut": len(rows), "void_in_cut": n_void, "void_reasons": voids, "void_rate": void_rate,
          "pending_in_cut": pending, "ineligible_in_cut": ineligible,
          "season_to_date (CHARTER §6)": {k: h.get(k) for k in ("missed_windows", "t2_missing", "frozen_pass",
                                                               "t2_missing_rate", "single_source", "fence_breaches")}}
    p1["pass"] = bool(p1["check_py"].startswith("PASS") and late == 0 and ok(void_rate) and void_rate < 0.05)
    p1["word"] = "PASS" if p1["pass"] else "FAIL"

    # P2 - the premium, live
    opens, divs = src["spy"]
    s0 = [{"ret": r["exits"]["exit_A"]["raw_return"], "win": r["exits"]["exit_A"]["WIN_raw"],
           "entry": r["exits"]["exit_A"].get("entry_session") or r["entry_session"],
           "exit": r["exits"]["exit_A"]["exit_session"]} for r in rows if "raw_return" in r["exits"]["exit_A"]]
    sh = {tr: [{"ret": e["exit_A"]["raw_return"], "win": e["exit_A"]["WIN_raw"], "entry": e["timing"]["entry"]["session"],
                "exit": e["timing"]["exit_A"]["session"], "spy_stored": e["exit_A"].get("spy_return")}
               for e in src["shadow"] if e.get("graded") and e["track"] == tr] for tr in ("SH-W", "SH-M")}
    for e in s0 + sh["SH-W"] + sh["SH-M"]:
        e["spy"] = spy_return(opens, divs, e["entry"], e["exit"])
    p2 = {"SH-W": {**read(sh["SH-W"]), "role": "primary (T0-wide, RQ1's universe)"},
          "S0 gated": {**read(s0), "role": "secondary (H-S0's statistic)"},
          "SH-M": {**read(sh["SH-M"]), "role": "secondary (market-wide)"}}
    p2["SH-W"]["word"] = word(p2["SH-W"])
    # Inside the cut but neither graded nor VOID: D017 §2's sample is not all there yet. The first run (1537ceb) read
    # the shadow grade of Fri 21:52 ET, while a Friday exit settles at 06:00 ET the next day (shadow.settled) and the
    # grader fires on weekday evenings only, so the 10-30 exits were missing from it unnoticed.
    p2["pending_in_cut"] = {"SH-W": sum(1 for e in src["shadow"] if e["track"] == "SH-W" and not e.get("graded")
                                        and not e.get("void")),
                            "S0 gated": pending,
                            "SH-M": sum(1 for e in src["shadow"] if e["track"] == "SH-M" and not e.get("graded")
                                        and not e.get("void"))}
    p2["cut_complete"] = not any(p2["pending_in_cut"].values())
    diffs =[abs(e["spy"] - e["spy_stored"]) for e in sh["SH-W"] + sh["SH-M"]
             if e.get("spy") is not None and e.get("spy_stored") is not None]
    shw = (shrep.get("descriptive") or {}).get("SH-W net mean (descriptive, D009 §5)") or {}
    p2["consistency"] = {
        "S0 net mean: stage1 / report.run H_S0": [p2["S0 gated"].get("net_mean"), rep["H_S0"].get("net_mean")],
        "S0 n: stage1 / report.run H_S0": [p2["S0 gated"]["n"], rep["H_S0"].get("n")],
        "SH-W net mean: stage1 / shadow.report_": [p2["SH-W"].get("net_mean"), shw.get("mean")],
        "SH-W n: stage1 / shadow.report_": [p2["SH-W"]["n"], shw.get("n")],
        "SPY return: max |stage1 - shadow's stored|, n": [max(diffs) if diffs else None, len(diffs)]}

    # P3 - selection over buy-all (exploratory, D005 v2)
    p3 = {}
    for tr in ("T1", "T2"):
        e = (rep["tracks"].get(tr) or {}).get("all") or {}
        buys = [r for r in rows if r["decisions"].get(tr) == "BUY"]
        bs = len({r["entry_session"] for r in buys})
        p3[tr] = {"events_with_a_decision": e.get("n", 0), "sessions": e.get("event_dates"), "buys": len(buys),
                  "buy_sessions": bs, "win_rate_all (T0)": e.get("T0_hit_rate"), "win_rate_buys": e.get("BUY_hit_rate"),
                  "mean_return_all (T0)": e.get("T0_mean_return"), "mean_return_buys": e.get("BUY_mean_return"),
                  "word": "INSUFFICIENT" if len(buys) < MIN_EVENTS or bs < MIN_SESSIONS else "EXPLORATORY"}
    agree = {}
    for tr in ("T2G", "T2R", "T2O"):
        same = []
        for r in rows:
            a = r["decisions"].get("T2")
            b = r["decisions"].get(tr) or (src["decisions"].get(r["event"]) or {}).get(tr)
            if a in ("BUY", "NO_BUY") and b in ("BUY", "NO_BUY"):
                same.append(a == b)
        agree[tr] = {"n": len(same), "agreement_with_T2": mean([1.0 if s else 0.0 for s in same])}
    p3["decision_agreement_with_T2"] = agree

    # P4 - execution
    p4 = {"paper_shares_fill_vs_official_open": shares_view(src["shares_ledger"], rows, cut, src["official_open"]),
          "paper_options": options_view(season, cut, src)}

    # P5 - knowledge banked (HYPOTHESES §3, no new computation)
    p5 = src["banked"]

    # P6 - cost and capacity
    costs = {tr: [d["cost"][tr] for d in src["decisions"].values() if tr in d["cost"]] for tr in T2_TRACKS}
    p6 = {"t2_missing_in_cut": sum(1 for r in rows if r["decisions"].get("T2") is None), "graded_in_cut": len(rows),
          "t2_missing_season_to_date": [h.get("t2_missing"), h.get("frozen_pass")],
          "recorded_cost_usd_equiv_per_decision": {tr: {"n": len(v), "mean": mean(v), "total": float(sum(v))}
                                                   for tr, v in costs.items()},
          "not_computed_here": "the weekly allowance's path and the tracks competing for it: ops records "
                               "(STATE Log, JOURNAL), cited in the deck"}

    out = {"season": season, "cut": cut, "rule": "registry/D017_stage1_review_v1.md", "label": "INTERIM - descriptive",
           "run_et": now_et().isoformat(timespec="seconds"), "code": src["code"],
           "report_run_implementation": rep.get("implementation"),
           "P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5, "P6": p6,
           "supports": supports(p1["pass"], p2["SH-W"]["word"])}
    guard(out)
    return out


# ---------------------------------------------------------------- markdown

def markdown(r):
    p1, p2, p3, p4, p6 = r["P1"], r["P2"], r["P3"], r["P4"], r["P6"]
    L = [f"# Stage 1 review - {r['season']} - data cut {r['cut']} - INTERIM", "",
         f"Computed by `pipeline/stage1.py` ({r['code']}) at {r['run_et'][:16]} ET under "
         "`registry/D017_stage1_review_v1.md`. Descriptive: no verdict word beyond D017 §3's, and it decides nothing "
         "(D017 §5). Never shown here (D017 §4): C1, any T2-confidence-vs-outcome view, per-name outcomes.", "",
         f"**What the evidence supports (D017 §5):** P1 {p1['word']} · P2 primary {p2['SH-W']['word']} -> "
         f"**{r['supports']}**. The decision is Jacob's.", "",
         f"## P1 · Truthful record - {p1['word']}", "",
         "| item | value |", "|---|---|",
         f"| check.py at the run | {p1['check_py']} |",
         f"| decisions frozen after their entry open | {p1['late_freezes'] if p1['late_freezes'] is not None else 'see check.py'} "
         f"(`{p1['late_freezes_source']}`) |",
         f"| graded / VOID / pending in the cut | {p1['graded_in_cut']} / {p1['void_in_cut']} / {p1['pending_in_cut']} |",
         f"| VOID rate (target < 5%) | {pct(p1['void_rate'], 1, False)} {json.dumps(p1['void_reasons'])} |"]
    s = p1["season_to_date (CHARTER §6)"]
    L += [f"| season to date: missed windows | {s.get('missed_windows')} |",
          f"| season to date: T2 missing | {s.get('t2_missing')} of {s.get('frozen_pass')} frozen PASS "
          f"({pct(s.get('t2_missing_rate'), 1, False)}) |",
          f"| season to date: single_source / fence breaches | {s.get('single_source')} / {s.get('fence_breaches')} |",
          "", "A missed window or missing T2 decision caused by the allowance or the refused token is a capacity "
          "finding (P6), not a truthfulness failure (D017 §3).", "",
          "## P2 · The premium, live", "",
          "| read | role | n | sessions | raw mean | net mean | win rate | excess over SPY | excess net of cost | "
          "cluster SE | 95% interval (net) | word |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k in ("SH-W", "S0 gated", "SH-M"):
        x = p2[k]
        ci = x.get("ci95_net")
        L.append(f"| {k} | {x['role']} | {x['n']} | {x['sessions']} | {pct(x.get('raw_mean'))} | {pct(x.get('net_mean'))} | "
                 f"{pct(x.get('win_rate'), 1, False)} | {pct(x.get('excess_spy_mean'))} (n {x.get('excess_spy_n', 0)}) | "
                 f"{pct(x.get('excess_spy_net_mean'))} | {pct(x.get('se_cluster_session'), 2, False)} | "
                 f"{'[' + pct(ci[0]) + ', ' + pct(ci[1]) + ']' if ci else '-'} | {x.get('word', '(secondary: no word)')} |")
    pc = p2["pending_in_cut"]
    L += ["", f"Pending in the cut (neither graded nor VOID): SH-W {pc['SH-W']} · S0 gated {pc['S0 gated']} · "
          f"SH-M {pc['SH-M']} - " + ("the cut is complete." if p2["cut_complete"] else
                                       "**the cut is INCOMPLETE: these events are in D017 §2's sample and missing "
                                       "from the reads above.**")]
    L += ["", f"D017 words, primary only: INSUFFICIENT under {MIN_EVENTS} events or {MIN_SESSIONS} sessions; "
          f"CONTRADICTS HISTORY if the upper bound is below {pct(HIST_NET)}; ALIVE if the net mean and the excess over "
          "SPY are both > 0; else NOT YET VISIBLE. Power (D017 §1): a real premium shows t of about 0.087 x sqrt(n).", "",
          "Consistency with the registered code:", ""]
    L += [f"- {k}: {v}" for k, v in p2["consistency"].items()]
    L += ["", "## P3 · Selection over buy-all (exploratory, D005 v2)", "",
          "| track | events with a decision | sessions | BUYs | BUY sessions | win rate, all | win rate, BUYs | "
          "mean return, all | mean return, BUYs | word |", "|---|---|---|---|---|---|---|---|---|---|"]
    for tr in ("T1", "T2"):
        x = p3[tr]
        L.append(f"| {tr} | {x['events_with_a_decision']} | {x['sessions']} | {x['buys']} | {x['buy_sessions']} | "
                 f"{pct(x['win_rate_all (T0)'], 1, False)} | {pct(x['win_rate_buys'], 1, False)} | "
                 f"{pct(x['mean_return_all (T0)'])} | {pct(x['mean_return_buys'])} | {x['word']} |")
    L += ["", "| shadow track | events with both decisions | agreement with T2 |", "|---|---|---|"]
    L += [f"| {tr} | {v['n']} | {pct(v['agreement_with_T2'], 1, False)} |" for tr, v in p3["decision_agreement_with_T2"].items()]
    sv = p4["paper_shares_fill_vs_official_open"]
    L += ["", "## P4 · Execution", "",
          f"Paper shares, real fills of trades closed by the cut: n {sv['n']}, median |fill - official open| "
          f"{sv['median_abs_bp']:.1f} bp, mean {sv['mean_abs_bp']:.1f} bp; no real fill (simulated or unfilled) "
          f"{sv['no_real_fill (simulated or unfilled)']}; official open unreadable {sv['official_open_unreadable']}."
          if sv["n"] else f"Paper shares: no real fill in the cut ({sv})", "",
          "Paper options, P&L per $1 of spot, trades whose reaction session is on or before the cut; the common set "
          "(priced at all four):", "",
          "| account | subset | sample | n | entry dates | fill | mid | halfway | natural | $ at fill | status |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    trig = []
    for s, a in p4["paper_options"].items():
        if "pnl_per_spot" not in a:
            L.append(f"| {s} | - | {a.get('note')} | | | | | | | | |")
            continue
        for sub, blks in a["pnl_per_spot"].items():
            for samp, b in blks.items():
                f0 = b.get("fill") or {}
                cells = " | ".join(pct((b.get(p) or {}).get("mean_pnl_on_spot"), 3) for p in ("fill", "mid", "halfway", "natural"))
                L.append(f"| {s} | {sub} | {samp} | {f0.get('n')} | {f0.get('entry_dates')} | {cells} | "
                         f"{f0.get('pnl_usd')} | {f0.get('status')} |")
        t = a["open_fill_trigger_v1"]
        trig.append(f"- {s}: open-fill trigger v1 counted {t['counted']} of 6, state {t['state']}, counts {t['counts']}")
    L += ["", "Open-fill trigger (registry/D011_open_fill_trigger_v1.md):", ""] + trig
    L += ["", "## P5 · Knowledge already banked (HYPOTHESES §3, no new computation)", ""]
    for d, lines in r["P5"].items():
        L += [f"- **{d}**: " + (" / ".join(lines) if lines else "see HYPOTHESES.md §3")]
    c = p6["recorded_cost_usd_equiv_per_decision"]
    L += ["", "## P6 · Cost and capacity", "",
          f"- T2 missing in the cut: {p6['t2_missing_in_cut']} of {p6['graded_in_cut']} graded; season to date "
          f"{p6['t2_missing_season_to_date'][0]} of {p6['t2_missing_season_to_date'][1]} frozen PASS.",
          "- Recorded cost per decision (`cost_usd_equiv`, events in the cut): "
          + "; ".join(f"{tr} n {v['n']}, mean ${v['mean']:.3f}, total ${v['total']:.2f}" if v["n"] else f"{tr} none recorded"
                      for tr, v in c.items()) + ".",
          f"- Not computed here: {p6['not_computed_here']}.", ""]
    return "\n".join(L) + "\n"


def out_base(cut):
    base = os.path.join(ROOT, "outcomes", "reports", f"stage1_{cut}")
    if not os.path.exists(base + ".md"):
        return base
    i = 2
    while os.path.exists(f"{base}_r{i}.md"):
        i += 1
    return f"{base}_r{i}"


def main(argv):
    cut = argv[argv.index("--cut") + 1] if "--cut" in argv else CUT
    a = [x for x in argv if not x.startswith("--") and x != cut]
    season = a[0] if a else "seasonA"
    r = compute(season, cut, sources(season, cut))
    md = markdown(r)
    print(md)
    if "--write" in argv:
        if not r["P2"]["cut_complete"]:
            raise SystemExit(f"D017 §2: the cut is incomplete {r['P2']['pending_in_cut']} - not written; "
                             "run again once every event in it is graded or VOID")
        base = out_base(cut)
        write_json(base + ".json", r)
        with open(base + ".md", "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        print(f"wrote {os.path.relpath(base, ROOT)}.md and .json")
    return r


if __name__ == "__main__":
    main(sys.argv[1:])
