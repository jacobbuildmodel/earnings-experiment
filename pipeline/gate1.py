"""Gate 1 report builder - code only, no AI, no new statistic. It ASSEMBLES what is already registered and
computed: D005 (T1, T2, the T2 confidence test, calibration), D008 H-S0, the D009 shadow report, and the
CHARTER §6 health numbers; then lists the decisions Gate 1 must make. It decides nothing.

    python pipeline/gate1.py <season> [--date YYYY-MM-DD] [--out PATH]

Reads outcomes/ (the newest saved outcomes/reports/<season>_*.json and outcomes/shadow/reports/<season>_*.json;
when a season has none saved, the same report is computed in memory by report.run / shadow.report_ and
NOT written), universe/<season>/event_status.json, events/<season>/*/manifest.json and logs/actions/.
Writes only outcomes/reports/gate1_<date>.md (or --out). Like every outcomes/ file it is fenced from T2.
"""
import contextlib
import datetime
import glob
import io
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, now_et  # noqa: E402

MDE_Z = 2.487   # (1.645 + 0.842): one-sided 5%, 80% power - D009 §5, used for H-S0 too (descriptive)
HEALTH = [      # CHARTER §6: (key, label, target text, passes(value) -> bool)
    ("missed_windows", "missed windows", "= 0", lambda v: v == 0),
    ("t2_missing_rate", "T2 missing", "< 5%", lambda v: v < 0.05),
    ("void_rate", "VOID", "< 5%", lambda v: v < 0.05),
    ("single_source", "`single_source` (once the key is live)", "= 0", lambda v: v == 0),
    ("fence_breaches", "fence breaches", "= 0", lambda v: v == 0),
]


# ---------------------------------------------------------------- formatting

def num(x):
    return x is not None and isinstance(x, (int, float)) and not (isinstance(x, float) and math.isnan(x))


def pct(x, d=1):
    return f"{x * 100:.{d}f}%" if num(x) else "–"


def pts(x, d=1):
    return f"{x * 100:+.{d}f}" if num(x) else "–"


def f(x, d=2):
    return f"{x:.{d}f}" if num(x) else "–"


def p3(x):
    return f"{x:.3f}" if num(x) else "–"


# ---------------------------------------------------------------- inputs

def newest(pattern):
    paths = sorted(glob.glob(pattern))
    return paths[-1] if paths else None


def load_d005(season):
    p = newest(os.path.join(ROOT, "outcomes", "reports", f"{season}_*.json"))
    if p:
        return json.load(open(p, encoding="utf-8")), os.path.relpath(p, ROOT).replace(os.sep, "/")
    import report
    with contextlib.redirect_stdout(io.StringIO()):
        rep = report.run(season, write=False)
    return rep, f"computed in memory by report.run at {rep['computed_et']} (no saved report)"


def load_d009(season):
    p = newest(os.path.join(ROOT, "outcomes", "shadow", "reports", f"{season}_*.json"))
    if p:
        return json.load(open(p, encoding="utf-8")), os.path.relpath(p, ROOT).replace(os.sep, "/")
    if not os.path.exists(os.path.join(ROOT, "outcomes", "shadow", season, "graded.json")):
        return None, "no shadow grade for this season"
    import shadow
    with contextlib.redirect_stdout(io.StringIO()):
        rep = shadow.report_(season, write=False)
    return rep, f"computed in memory by shadow.report_ at {rep['run_et']} (no saved report)"


def health(season, window=None):
    """CHARTER §6. Denominators: frozen PASS events (manifest status PASS) for T2 missing and VOID."""
    st = os.path.join(ROOT, "universe", season, "event_status.json")
    evs = json.load(open(st, encoding="utf-8"))["events"] if os.path.exists(st) else {}
    evs = evs.values() if isinstance(evs, dict) else evs
    missed = sum(1 for e in evs if e.get("reason") == "missed_window")
    passed, t2_missing = 0, 0
    for mp in glob.glob(os.path.join(ROOT, "events", season, "*", "manifest.json")):
        m = json.load(open(mp, encoding="utf-8"))
        if m.get("status") != "PASS" or m.get("dry"):
            continue
        passed += 1
        if any("T2 frozen as MISSING" in str(n) for n in m.get("notes") or []):
            t2_missing += 1
    voids, single, graded_or_void = 0, 0, 0
    for op in glob.glob(os.path.join(ROOT, "outcomes", season, "*.json")):
        o = json.load(open(op, encoding="utf-8"))
        if o.get("gate_status") != "PASS":
            continue
        if o.get("void"):
            voids += 1
        if o.get("void") or o.get("graded"):
            graded_or_void += 1
        fl = list(o.get("flags") or []) + list(((o.get("exits") or {}).get("exit_A") or {}).get("flags") or [])
        if o.get("graded") and "single_source" in fl:
            single += 1
    breaches, logs, listed = 0, 0, []
    for lp in sorted(glob.glob(os.path.join(ROOT, "logs", "actions", "*.json"))):
        stamp = os.path.basename(lp)[:10]
        if window and not (window[0] <= stamp <= window[1]):
            continue
        logs += 1
        fb = json.load(open(lp, encoding="utf-8")).get("fence_breaches") or []   # runlog.py: a list of breaches
        fb = fb if isinstance(fb, list) else [{}] * int(fb)
        breaches += len(fb)
        listed += [{"log": os.path.basename(lp), "fence": b.get("fence"), "tool": b.get("tool")} for b in fb]
    return {"missed_windows": missed, "t2_missing": t2_missing, "frozen_pass": passed,
            "t2_missing_rate": t2_missing / passed if passed else None,
            "void": voids, "graded_or_void": graded_or_void, "void_rate": voids / graded_or_void if graded_or_void else None,
            "single_source": single, "fence_breaches": breaches, "action_logs": logs, "breach_list": listed}


def season_window(season):
    try:
        from common import rule_for
        lo, hi = rule_for("D003_universe_screen", season)["seasons"][season]["window"]
    except (SystemExit, KeyError):
        return None
    lo = (datetime.date.fromisoformat(lo) - datetime.timedelta(days=21)).isoformat()   # screen + S1 runs
    hi = (datetime.date.fromisoformat(hi) + datetime.timedelta(days=10)).isoformat()   # timing checks final
    return lo, hi


# ---------------------------------------------------------------- sections

def d005_section(rep):
    out = ["## 1. D005 — the scored tracks (T1 rule, T2 AI) against buy-everything (T0)", ""]
    c = rep.get("counts", {})
    out += [f"- Label: **{rep.get('label')}** · implementation: {rep.get('implementation')}",
            f"- Graded {c.get('graded', 0)} on {c.get('event_dates', 0)} entry sessions · VOID {sum((c.get('void') or {}).values())} "
            f"{c.get('void') or ''} · pending {c.get('pending', 0)} · gated out (never graded) {c.get('ineligible_never_graded', 0)}", ""]
    out += ["| track | n | sessions | BUY share | T0 hit | BUY hit | lift, pts | p (one-sided) | return lift, pts | verdict |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for tr in ("T1", "T2"):
        a = (rep.get("tracks", {}).get(tr) or {}).get("all") or {}
        out.append(f"| {tr} | {a.get('n', 0)} | {a.get('event_dates', '–')} | {pct(a.get('buy_share'), 0)} | {pct(a.get('T0_hit_rate'))} | "
                   f"{pct(a.get('BUY_hit_rate'))} | {pts(a.get('lift'))} | {p3(a.get('p_one_sided'))} | {pts(a.get('return_lift'), 2)} | "
                   f"{a.get('verdict', '–')} |")
    out += ["", "Robustness cuts (descriptive, no verdict):", "",
            "| track | cut | n | lift, pts | p |", "|---|---|---|---|---|"]
    for tr in ("T1", "T2"):
        for v in ("excl_price_dispute", "excl_timing_unverified", "excl_confound_8k"):
            a = (rep.get("tracks", {}).get(tr) or {}).get(v) or {}
            out.append(f"| {tr} | {v} | {a.get('n', 0)} | {pts(a.get('lift'))} | {p3(a.get('p_one_sided'))} |")
    s = rep.get("T2_vs_T1") or {}
    out += ["", f"**T2 vs T1 (stacked, D005 §3):** n {s.get('n_events', 0)} on {s.get('event_dates', 0)} sessions · "
            f"delta {pts(s.get('delta'))} pts · p {p3(s.get('p_one_sided'))} · {s.get('verdict', '–')}", ""]
    t2 = ((rep.get("tracks", {}).get("T2") or {}).get("all") or {})
    pr = t2.get("probability")
    out += ["### T2 probabilities — the confidence test and calibration", ""]
    if not pr:
        out += [f"No T2 probabilities to score (T2 decisions: {t2.get('n', 0)}; confidence missing: "
                f"{t2.get('t2_confidence_missing', '–')}).", ""]
    else:
        ct = pr.get("confidence_test") or {}
        out += [f"- n {pr['n']} (confidence missing {t2.get('t2_confidence_missing', 0)}) · Brier {f(pr.get('brier'), 3)} "
                f"vs base-rate reference {f(pr.get('brier_reference_in_sample_base_rate'), 3)} → **Brier skill "
                f"{f(pr.get('brier_skill'), 3)}** · log loss {f(pr.get('log_loss'), 3)} · AUC {f(pr.get('auc'), 3)} "
                f"(90% cluster CI {pr.get('auc_ci90_cluster') and ' – '.join(f(x, 3) for x in pr['auc_ci90_cluster']) or '–'})",
                f"- Share of confidences in 0.45–0.55 (coin-flip calls): {pct(pr.get('share_conf_0.45_0.55'), 0)}",
                "- **Confidence test (D005 v2, WIN = a + b·confidence):** "
                + (f"slope {f(ct.get('slope'), 3)}, se {f(ct.get('se_cr1'), 3)}, t {f(ct.get('t_cr1'))}, one-sided p {p3(ct.get('p_one_sided'))}"
                   if ct else "not run (under the rule 7 minimum, or no spread in confidence)"), "",
                "| confidence bin | n | mean confidence | hit rate |", "|---|---|---|---|"]
        out += [f"| {b['bin']} | {b['n']} | {f(b.get('mean_conf'), 3)} | {pct(b.get('hit_rate'))} |" for b in pr.get("calibration", [])]
        out.append("")
    cf = rep.get("confirmatory") or {}
    out += [f"**Confirmatory:** {'registered — ' + json.dumps(cf.get('verdicts')) if cf.get('registered') else cf.get('note', 'none')}", ""]
    return out


def h_s0_section(rep):
    h = rep.get("H_S0") or {}
    mde = MDE_Z * h["se"] if num(h.get("se")) else None
    return ["## 2. D008 — H-S0, the premium harvest (S0 buys every PASS event)", "",
            "| n | sessions | net mean | se | t | p (one-sided) | MDE (descriptive) | verdict |", "|---|---|---|---|---|---|---|---|",
            f"| {h.get('n', 0)} | {h.get('dates', 0)} | {pct(h.get('net_mean'), 2)} | {pct(h.get('se'), 2)} | {f(h.get('t'))} | "
            f"{p3(h.get('p_one_sided'))} | {pct(mde, 2)} | {h.get('verdict', '–')} |", "",
            "The registered H-S0 test pools Seasons A + B (D008 §2). This is one season: monitoring, not the verdict.", ""]


def d009_section(rep, source):
    out = ["## 3. D009 — shadow tracks (secondary; never a scored track)", "", f"Source: {source}", ""]
    if not rep:
        return out + ["No shadow report for this season.", ""]
    out += [f"Label: **{rep.get('label')}**", "",
            "| test | n | sessions | estimate | t | p (one-sided) | Holm p (m = 3) | MDE | status |", "|---|---|---|---|---|---|---|---|---|"]
    for k in ("H-M", "H-X", "H-VOL"):
        r = (rep.get("tests") or {}).get(k) or {}
        est = r.get("mean", r.get("diff"))
        out.append(f"| {k} | {r.get('n', 0)} | {r.get('dates') or 0} | {pct(est, 2)} | {f(r.get('t'))} | {p3(r.get('p_one_sided'))} | "
                   f"{p3(r.get('p_holm'))} | {pct(r.get('mde'), 2)} | {r.get('status', r.get('note', '–'))} |")
    out += ["", "Without `timing_unverified` / `late_8k` events:", "", "| test | n | mean | p |", "|---|---|---|---|"]
    for k, r in (rep.get("sensitivity") or {}).items():
        out.append(f"| {k} | {r.get('n', 0)} | {pct(r.get('mean'), 2)} | {p3(r.get('p_one_sided'))} |")
    d = rep.get("descriptive") or {}
    w = d.get("SH-W net mean (descriptive, D009 §5)") or {}
    out += ["", f"- SH-W (T0-wide, descriptive): n {w.get('n', 0)} on {w.get('dates', 0)} sessions, net mean {pct(w.get('mean'), 2)}, "
            f"t {f(w.get('t'))}, hit {pct(d.get('SH-W hit'))}; over SPY {pct(d.get('SH-W mean excess over SPY (net)'), 2)}",
            f"- SH-M hit {pct(d.get('SH-M hit'))}, over SPY {pct(d.get('SH-M mean excess over SPY (net)'), 2)} · "
            f"SH-X realised/implied {f(d.get('SH-X mean realised/implied'))}"]
    for tr, e in (d.get("events") or {}).items():
        out.append(f"- {tr}: {e.get('total', 0)} events, {e.get('graded', 0)} graded, VOID {e.get('void') or {}}")
    out += ["", "Season A's result is an interim reported to Gate 1. The registered D009 verdict is on A + B pooled "
            "(`python pipeline/shadow.py report-pooled seasonA seasonB --final`, at Season B's end).", ""]
    return out


def health_section(h):
    out = ["## 4. Health numbers (CHARTER §6)", "", "| measure | value | target | met |", "|---|---|---|---|"]
    shown = {"missed_windows": str(h["missed_windows"]),
             "t2_missing_rate": f"{pct(h['t2_missing_rate'])} ({h['t2_missing']} of {h['frozen_pass']} frozen PASS)",
             "void_rate": f"{pct(h['void_rate'])} ({h['void']} of {h['graded_or_void']} settled PASS)",
             "single_source": f"{h['single_source']} graded events",
             "fence_breaches": f"{h['fence_breaches']} in {h['action_logs']} AI-step logs"}
    for key, label, target, ok in HEALTH:
        v = h.get(key)
        met = "–" if v is None else ("yes" if ok(v) else "**NO**")
        out.append(f"| {label} | {shown[key]} | {target} | {met} |")
    if h.get("breach_list"):
        out += ["", "Fence breaches as flagged by `runlog.py` (pattern matches; each needs a human look, some are false positives):", ""]
        out += [f"- `{b['log']}`: {b['fence']} via {b['tool']}" for b in h["breach_list"]]
    return out + [""]


def decisions_section(d005, d009):
    h = d005.get("H_S0") or {}
    m = ((d009 or {}).get("tests") or {}).get("H-M") or {}
    hs0_mde = MDE_Z * h["se"] if num(h.get("se")) else None
    out = ["## 5. Decisions Gate 1 must make (listed, not taken — the laptop session and Jacob decide)", "",
           "1. **CHARTER I12 — does D008 v2 pool SH-W / SH-M evidence for Gate 2?** D008's H-S0 runs on gated "
           f"events only: this season n {h.get('n', 0)} on {h.get('dates', 0)} sessions, MDE {pct(hs0_mde, 2)}. "
           f"SH-M's H-M: n {m.get('n', 0)} on {m.get('dates') or 0} sessions, MDE {pct(m.get('mde'), 2)}. "
           "A pooled D008 v2 must be registered before Season B's screen date, as a new version with its own clock (rule 5).",
           "2. **Promote a D009 hypothesis to confirmatory for Season B?** (D009 §5: the only thing a shadow result can do.) "
           "Status of each this season:"]
    for k in ("H-M", "H-X", "H-VOL"):
        r = ((d009 or {}).get("tests") or {}).get(k) or {}
        out.append(f"   - {k}: {r.get('status', 'no report')}, Holm p {p3(r.get('p_holm'))}, n {r.get('n', 0)}")
    out += ["   A promoted hypothesis is written into `D005_confirmatory_seasonB.json` (or a D009 v-next) and frozen before "
            "Season B's screen; it is then tested only on Season B's data (rule 6).",
            "3. **Register Season B's confirmatory family** (`registry/D005_confirmatory_seasonB.json`, RESEARCH_PLAN Gate 1): "
            "T0 premium, the best conditioner, T2 confidence, the best option signal — fixed before the Season B screen.",
            "4. **CHARTER I1 — widen the universe?** Decide from Season A's event *count* (not outcomes) before the Season B screen.",
            "5. **D009 v2 (year-round SH-M)** — frozen or not; if frozen, its off-season window `off_seasonA` is already running.",
            ""]
    return out


def build(season, d005, d005_src, d009, d009_src, h, built=None):
    built = built or now_et().isoformat(timespec="minutes")
    head = [f"# Gate 1 report — {season}", "",
            f"> Built {built} ET by `pipeline/gate1.py` (code only; it assembles registered statistics and decides nothing).",
            f"> D005 / D008 source: {d005_src}.",
            "> Season A is exploratory; every number here is interim to the A + B pooled verdicts. "
            "Under 30 events or 10 sessions a result is \"insufficient\" (rule 7)."
            + (" **PILOT: bugs, not findings.**" if season.lower().startswith("pilot") else ""), ""]
    body = d005_section(d005) + h_s0_section(d005) + d009_section(d009, d009_src) + health_section(h) + decisions_section(d005, d009)
    return "\n".join(head + body).rstrip() + "\n"


def main(season, date=None, out=None):
    d005, d005_src = load_d005(season)
    d009, d009_src = load_d009(season)
    h = health(season, season_window(season))
    md = build(season, d005, d005_src, d009, d009_src, h)
    date = date or now_et().strftime("%Y-%m-%d")
    path = out or os.path.join(ROOT, "outcomes", "reports", f"gate1_{date}.md")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(md)
    print(f"wrote {os.path.relpath(path, ROOT) if path.startswith(ROOT) else path}")
    return path


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0].startswith("--"):
        raise SystemExit(__doc__)
    opt = lambda k: a[a.index(k) + 1] if k in a else None  # noqa: E731
    main(a[0], date=opt("--date"), out=opt("--out"))
