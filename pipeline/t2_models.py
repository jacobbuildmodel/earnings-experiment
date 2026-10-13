"""D013: more Claude decision tracks on every T2 dossier - SHADOWS, never scored as T2. Code only (the model
decides; code grades). Rules: registry/D013_t2_model_shadows_v1.md.

    python pipeline/t2_models.py run [--backend opus|sonnet_r|all]   # the shadow queue (cloud routine earnings-t2-models)
    python pipeline/t2_models.py list [--backend ...]
    python pipeline/t2_models.py report SEASON [--write]              # T2O / T2R / T2M statistics on graded events

Tracks:
  T2O - Claude Opus 5.5 (claude-opus-5-5)
  T2R - a second, independent Claude Sonnet 5.5 run (T2's own model): T2's run-to-run noise
  T2M - the mean confidence of T2, T2R and T2O on events where all three froze; BUY <=> > 0.50
Each of T2O and T2R is EXACTLY D004 v4's stage 2: the same leak probe, system prompt, dossier, isolation checks,
attempt limit, deadline (entry open - 15 min) and freeze (own manifest + RFC 3161 tokens + commit). It is done by
running pipeline/t2_stage2.py's own functions - that file is not edited - with two extra backends registered at
run time and their calls routed to `claude -p --model <model>`.
T2 comes first: a shadow run does nothing while any T2 decision is still waiting in T2's own queue.
Budget (code-enforced, D013 §3): per run at most RUN_CAP new decisions per backend, and at most WEEK_CAP per
backend over the trailing 7 days (counted from the shadow's own "decided" logs). Over budget = the event's
shadow is missing; nothing is logged as an attempt. Order: sonnet_r before opus (the cheaper replicate first).
Model check: a reply whose CLI init model differs from the requested model is rejected (never frozen), and the
report counts a shadow only if its frozen file names the registered model.
Drift check: run refuses, and report says so, if t2_models.py or t2_stage2.py differ from
registry/D013_implementation_v1.sha256.
Claude Fable 5.1 is not a track: on 2026-10-13 the account refused it ("requires usage credits").
"""
import datetime
import glob
import hashlib
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2_stage2 as ts  # noqa: E402
from common import ROOT, now_et, write_json  # noqa: E402

# sonnet_r's model is T2's own (rule["t2_model"]) by construction; listed in run order (sonnet_r first)
MODELS = {"sonnet_r": {"track": "T2R", "model": None, "file": "t2r.json", "thesis": "t2r_thesis.md",
                       "manifest": "manifest_t2r.json"},
          "opus": {"track": "T2O", "model": "claude-opus-5-5", "file": "t2o.json", "thesis": "t2o_thesis.md",
                   "manifest": "manifest_t2o.json"}}
RUN_CAP = 12          # new shadow decisions per backend per run
WEEK_CAP = 80         # new shadow decisions per backend over the trailing 7 days
IMPL = os.path.join("registry", "D013_implementation_v1.sha256")
PINNED = ("pipeline/t2_models.py", "pipeline/t2_stage2.py")
_ORIG_CALL = ts.call


def model_of(backend, rule):
    return MODELS[backend]["model"] or rule["t2_model"]


def drift():
    """[] if t2_models.py and t2_stage2.py match the registered D013 implementation, else the problems."""
    p = os.path.join(ROOT, IMPL)
    if not os.path.exists(p):
        return [f"{IMPL} missing"]
    want = {ln.split()[1]: ln.split()[0] for ln in open(p, encoding="utf-8") if ln.strip() and not ln.startswith("#")}
    out = []
    for f in PINNED:
        got = hashlib.sha256(open(os.path.join(ROOT, f), "rb").read().replace(b"\r\n", b"\n")).hexdigest()
        if want.get(f) != got:
            out.append(f"{f} differs from {IMPL}")
    return out


def decided_last_7d(backend, now):
    n = 0
    for lp in glob.glob(os.path.join(ROOT, "logs", "t2", f"*_{backend}_*.json")):
        try:
            e = json.load(open(lp, encoding="utf-8"))
        except ValueError:
            continue
        if e.get("outcome") == "decided" and e.get("called_et") and \
                now - datetime.datetime.fromisoformat(e["called_et"]) < datetime.timedelta(days=7):
            n += 1
    return n


def configure():
    """Register the shadow backends in t2_stage2 and route their calls to the CLI with their own model."""
    for b, m in MODELS.items():
        ts.BACKENDS[b] = {k: m[k] for k in ("track", "file", "thesis", "manifest")}

    def call(backend, rule, sys_prompt, user, json_mode=True):
        if backend in MODELS:
            want = model_of(backend, rule)
            res = ts.call_claude({**rule, "t2_model": want}, sys_prompt, user)
            served = (res.get("isolation") or {}).get("model") or res.get("model")
            if res.get("ok") and served != want:
                return {"ok": False, "limited": False, "isolation": res.get("isolation"),
                        "error": f"model check failed: asked for {want}, the CLI served {served} - reply not used"}
            return res
        return _ORIG_CALL(backend, rule, sys_prompt, user, json_mode)
    ts.call = call


def run(backends):
    problems = drift()
    if problems:
        raise SystemExit(f"D013 implementation drift - refusing to run: {problems}")
    configure()
    t2_waiting = ts.waiting("claude")
    if t2_waiting:
        print(f"T2 first: {len(t2_waiting)} T2 decision(s) still waiting - the shadows do nothing this run")
        return
    now = now_et()
    real_waiting = ts.waiting
    for b in [m for m in MODELS if m in backends]:            # registered order: sonnet_r, then opus
        room = max(0, min(RUN_CAP, WEEK_CAP - decided_last_7d(b, now)))
        todo = real_waiting(b)
        if len(todo) > room:
            print(f"{b}: {len(todo)} waiting, budget allows {room} this run (D013 §3) - the rest stay missing for now")
        ts.waiting = lambda backend, _t=todo[:room]: _t
        try:
            ts.run([b])
        finally:
            ts.waiting = real_waiting


# ---------------------------------------------------------------- report (D013 §5)
def frozen_before_entry(edir, mname, entry_open):
    """The track's own manifest, committed before the entry open (rule 1) - grade.py's test for T2/T2G."""
    mp = os.path.join(edir, mname)
    if not os.path.exists(mp):
        return False
    when = subprocess.run(["git", "log", "--diff-filter=A", "--format=%cI", "--",
                           os.path.relpath(mp, ROOT).replace(os.sep, "/")], cwd=ROOT, capture_output=True,
                          text=True).stdout.split()
    return bool(when) and datetime.datetime.fromisoformat(when[-1]) < entry_open


def shadow_row(row, season):
    """Add T2O / T2R / T2M decisions and confidences to one graded outcome row (a copy)."""
    r = json.loads(json.dumps(row))
    edir = os.path.join(ROOT, "events", season, f"{row['ticker']}_{row['report_date']}")
    man = os.path.join(edir, "manifest.json")
    if not os.path.exists(man):
        return r
    eo = datetime.datetime.fromisoformat(json.load(open(man, encoding="utf-8"))["entry_open_et"])
    conf, probes = {}, {}
    rule = json.load(open(os.path.join(ROOT, "registry", "D004_decision_protocol_v4.json"), encoding="utf-8"))
    for b, m in MODELS.items():
        if frozen_before_entry(edir, m["manifest"], eo):
            t = json.load(open(os.path.join(edir, m["file"]), encoding="utf-8"))["t2"]
            if t.get("model") != model_of(b, rule):            # a frozen file from another model never counts
                r.setdefault("d013_excluded", []).append(f"{m['track']}: model {t.get('model')}")
                continue
            r["decisions"][m["track"]] = t["decision"]
            conf[m["track"]] = float(t["confidence"])
            probes[m["track"]] = t.get("leak_probe")
    r["d013_leak_probes"] = probes
    if (r.get("stage2") or {}).get("T2") == "frozen before the entry open" and r.get("t2_confidence") is not None:
        conf["T2"] = float(r["t2_confidence"])
    if all(k in conf for k in ("T2", "T2R", "T2O")):
        c = round((conf["T2"] + conf["T2R"] + conf["T2O"]) / 3, 4)
        conf["T2M"] = c
        r["decisions"]["T2M"] = "BUY" if c > 0.5 else "NO_BUY"
    r["d013_confidence"] = conf
    if r.get("exits", {}).get("exit_A", {}).get("WIN_raw") is not None:
        r.setdefault("correct", {})
        for tr in ("T2O", "T2R", "T2M"):
            if tr in r["decisions"]:
                r["correct"][tr] = (r["decisions"][tr] == "BUY") == r["exits"]["exit_A"]["WIN_raw"]
    return r


def as_slot(rows, track):
    """report.evaluate computes probability statistics for the T2G slot; put the track's decision and confidence
    there (copies), so the D005 code is reused unchanged."""
    out = []
    for r in rows:
        c = r.get("d013_confidence", {}).get(track)
        if c is None or track not in r["decisions"]:
            continue
        x = json.loads(json.dumps(r))
        x["decisions"]["T2G"] = r["decisions"][track]
        x["t2g_confidence"] = c
        out.append(x)
    return out


def report(season, write=False):
    import numpy as np
    import report as rp
    rows, voids, pending, inel = rp.load_rows(season)
    rows = [shadow_row(r, season) for r in rows]
    res = {}
    for tr in ("T2O", "T2R", "T2M"):
        rs = as_slot(rows, tr)
        res[tr] = rp.evaluate(rs, "T2G") if rs else {"n": 0}
        res[tr]["track"] = tr
        res[tr]["label"] = "SHADOW (D013) - never scored as T2, never in a confirmatory family"
    # T2 on the same events, for paired comparisons (intersection only, D004 v4 change 4's convention)
    paired = {}
    for tr in ("T2O", "T2R", "T2M"):
        both = [r for r in rows if tr in r.get("d013_confidence", {}) and "T2" in r.get("d013_confidence", {})]
        if not both:
            paired[tr] = {"n": 0}
            continue
        y = np.array([1.0 if r["exits"]["exit_A"]["WIN_raw"] else 0.0 for r in both])
        a = np.array([r["d013_confidence"][tr] for r in both])
        b = np.array([r["d013_confidence"]["T2"] for r in both])
        g = [r["entry_session"] for r in both]
        d = (a - y) ** 2 - (b - y) ** 2                         # < 0: the shadow's Brier is better than T2's
        p = {"n": len(both), "event_dates": len(set(g)), "brier_track": float(((a - y) ** 2).mean()),
             "brier_T2": float(((b - y) ** 2).mean()), "brier_diff_mean": float(d.mean()),
             "decision_agreement": float(np.mean((a > 0.5) == (b > 0.5))),
             "confidence_corr": float(np.corrcoef(a, b)[0, 1]) if len(both) > 2 and a.std() > 0 and b.std() > 0 else None,
             "mean_abs_conf_diff": float(np.abs(a - b).mean())}
        if rp.sufficient(len(both), len(set(g))):
            bb, se, t = rp.ols_k(d, np.ones((len(d), 1)), np.array(g), 0)
            p.update(brier_diff_se_cr1=se, brier_diff_t=t)
        paired[tr] = p
    out = {"season": season, "rule": "D013_t2_model_shadows_v1 §5", "run_et": now_et().isoformat(timespec="seconds"),
           "label": "SHADOW - descriptive; T2 is unaffected", "implementation_drift": drift() or None,
           "tracks": res, "paired_with_T2": paired,
           "leak_probes": [{"event": f"{r['ticker']}_{r['report_date']}", "track": tr, "answer": a}
                           for r in rows for tr, a in (r.get("d013_leak_probes") or {}).items()],
           "excluded_wrong_model": [x for r in rows for x in r.get("d013_excluded", [])],
           "graded_rows": len(rows), "pending": pending, "voids": voids}
    for tr in ("T2O", "T2R", "T2M"):
        v, pv = res[tr], paired[tr]
        print(f"{tr}: n={v.get('n')} hit={v.get('BUY_hit_rate')} brier={(v.get('probability') or {}).get('brier')} "
              f"paired n={pv.get('n')} brier_diff={pv.get('brier_diff_mean')} agree={pv.get('decision_agreement')}")
    if write:
        write_json(os.path.join(ROOT, "outcomes", "reports", f"D013_{season}_{now_et():%Y-%m-%d}.json"), out)
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    bk = a[a.index("--backend") + 1] if "--backend" in a else "all"
    chosen = list(MODELS) if bk == "all" else [bk]
    if any(b not in MODELS for b in chosen):
        raise SystemExit(f"unknown backend: {chosen} - D013 backends are {list(MODELS)}")
    if a[:1] == ["run"]:
        run(chosen)
    elif a[:1] == ["list"]:
        configure()
        for b in chosen:
            for season, edir, _ in ts.waiting(b):
                print(b, season, os.path.basename(edir))
    elif a[:1] == ["report"]:
        report(a[1], "--write" in a)
    else:
        raise SystemExit(__doc__)
