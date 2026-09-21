"""The evaluation - D005, computed by code from graded outcomes, never judged.

    python pipeline/report.py <season> [--write]

Reads outcomes/<season>/*.json (written by grade.py). Prints the D005 tables; --write also saves
outcomes/reports/<season>_<date>.json and .md. Outcomes and reports live under outcomes/, which the AI
step never has on disk (D004: T2 does not see this season's outcomes).

Every statistic here is named in registry/D005_evaluation_v1.md; its method is not chosen after
seeing data. Randomness is seeded (D005 §3), so a rerun gives the same numbers.
"""
import datetime
import glob
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, now_et, write_json  # noqa: E402

SEED = 20260921
B_WILD = 9999
B_PAIRS = 2000
MIN_EVENTS, MIN_DATES = 30, 10
WEBB = np.array([-math.sqrt(1.5), -1, -math.sqrt(0.5), math.sqrt(0.5), 1, math.sqrt(1.5)])


# ---------------------------------------------------------------- statistics (D005 §3)

def ols_cluster(y, x, g):
    """y = a + b*x; returns b, CR1 cluster-robust SE, t. x is 0/1 or continuous; g = cluster ids."""
    X = np.column_stack([np.ones_like(x), x])
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    u = y - X @ beta
    groups = np.unique(g)
    G, n = len(groups), len(y)
    meat = np.zeros((2, 2))
    for c in groups:
        s = X[g == c].T @ u[g == c]
        meat += np.outer(s, s)
    adj = G / (G - 1) * (n - 1) / (n - 2) if G > 1 and n > 2 else 1.0
    V = adj * XtX_inv @ meat @ XtX_inv
    se = math.sqrt(V[1, 1]) if V[1, 1] > 0 else float("nan")
    return float(beta[1]), se, float(beta[1] / se) if se and se == se else float("nan")


def wild_cluster_p(y, x, g, rng):
    """One-sided p for H0: b <= 0 vs b > 0. Restricted wild cluster bootstrap-t (Cameron, Gelbach &
    Miller 2008); Rademacher weights with >= 12 clusters, Webb 6-point weights below that.
    Vectorised over all draws; gives the same statistic as calling ols_cluster once per draw."""
    b, se, t = ols_cluster(y, x, g)
    if not t == t:
        return float("nan")
    groups, inv = np.unique(g, return_inverse=True)
    G, n = len(groups), len(y)
    X = np.column_stack([np.ones_like(x), x])
    XtX_inv = np.linalg.inv(X.T @ X)
    H = XtX_inv @ X.T                                  # 2 x n
    C = np.zeros((n, G))
    C[np.arange(n), inv] = 1.0
    adj = G / (G - 1) * (n - 1) / (n - 2) if G > 1 and n > 2 else 1.0
    y0 = np.full_like(y, y.mean())                     # fit under the null b = 0
    u0 = y - y0
    W = rng.choice([-1.0, 1.0], (B_WILD, G)) if G >= 12 else rng.choice(WEBB, (B_WILD, G))
    Y = y0[None, :] + u0[None, :] * W[:, inv]          # B x n bootstrap samples
    beta = Y @ H.T                                     # B x 2
    U = Y - beta @ X.T                                 # B x n residuals
    S0 = (U * X[:, 0]) @ C                             # B x G cluster score sums, intercept
    S1 = (U * X[:, 1]) @ C                             # B x G, slope
    m00, m01, m11 = (S0 * S0).sum(1), (S0 * S1).sum(1), (S1 * S1).sum(1)
    a, c = XtX_inv[1, 0], XtX_inv[1, 1]
    v11 = adj * (a * a * m00 + 2 * a * c * m01 + c * c * m11)
    with np.errstate(invalid="ignore", divide="ignore"):
        tb = beta[:, 1] / np.sqrt(v11)
    count = int(np.sum(tb >= t))
    return (count + 1) / (B_WILD + 1)


def auc(p, y):
    pos, neg = p[y == 1], p[y == 0]
    if not len(pos) or not len(neg):
        return float("nan")
    wins = sum((a > b) + 0.5 * (a == b) for a in pos for b in neg)
    return wins / (len(pos) * len(neg))


def pairs_cluster_ci(fn, idx_by_cluster, rng, level=0.90):
    """Percentile CI from resampling whole clusters (entry sessions) with replacement."""
    keys = list(idx_by_cluster)
    vals = []
    for _ in range(B_PAIRS):
        pick = rng.choice(len(keys), len(keys))
        idx = np.concatenate([idx_by_cluster[keys[k]] for k in pick])
        v = fn(idx)
        if v == v:
            vals.append(v)
    if not vals:
        return [float("nan"), float("nan")]
    a = (1 - level) / 2
    return [float(np.quantile(vals, a)), float(np.quantile(vals, 1 - a))]


def eb_shrink(estimates):
    """Partial pooling (D005 §5): normal-normal empirical Bayes, DerSimonian-Laird tau^2."""
    rows = [(k, b, se) for k, (b, se) in estimates.items() if se and se == se and se > 0 and b == b]
    if len(rows) < 2:
        return {}
    w = np.array([1 / se ** 2 for _, _, se in rows])
    b = np.array([x for _, x, _ in rows])
    pooled = float((w * b).sum() / w.sum())
    q = float((w * (b - pooled) ** 2).sum())
    tau2 = max(0.0, (q - (len(rows) - 1)) / (w.sum() - (w ** 2).sum() / w.sum()))
    out = {}
    for k, bk, se in rows:
        shrink = tau2 / (tau2 + se ** 2) if tau2 > 0 else 0.0
        out[k] = {"raw": bk, "se": se, "shrunk": shrink * bk + (1 - shrink) * pooled, "weight_on_own": shrink}
    return {"pooled": pooled, "tau2": tau2, "clusters": out}


# ---------------------------------------------------------------- evaluation (D005 §2-§4)

def verdict(n, dates, p, confirmatory=False):
    if n < MIN_EVENTS or dates < MIN_DATES:
        return "insufficient"
    if p != p:
        return "no selection (track bought all or none)"
    if confirmatory:
        return "confirmed" if p < 0.05 else "not confirmed"
    return f"evidence of lift (exploratory, p={p:.3f})" if p < 0.05 else f"no evidence of lift (p={p:.3f})"


def evaluate(rows, track, rng):
    """One track against T0 on the events where the track has a decision."""
    rs = [r for r in rows if r["decisions"].get(track) in ("BUY", "NO_BUY")]
    n = len(rs)
    if not n:
        return {"track": track, "n": 0, "verdict": "no decisions"}
    y = np.array([1.0 if r["exits"]["exit_A"]["WIN_raw"] else 0.0 for r in rs])
    ret = np.array([r["exits"]["exit_A"]["raw_return"] for r in rs])
    x = np.array([1.0 if r["decisions"][track] == "BUY" else 0.0 for r in rs])
    g = np.array([r["entry_session"] for r in rs])
    dates = len(set(g))
    f = x.mean()
    t0_hit = y.mean()
    out = {"track": track, "n": n, "event_dates": dates, "buy_share": f, "T0_hit_rate": t0_hit,
           "T0_mean_return": float(ret.mean())}
    if 0 < f < 1:
        hb, hn = y[x == 1].mean(), y[x == 0].mean()
        b, se, t = ols_cluster(y, x, g)
        p = wild_cluster_p(y, x, g, rng) if dates >= 2 else float("nan")
        rb, rse, rt = ols_cluster(ret, x, g)
        rp = wild_cluster_p(ret, x, g, rng) if dates >= 2 else float("nan")
        out.update({"BUY_hit_rate": hb, "NO_BUY_hit_rate": hn, "lift": hb - t0_hit, "separation": b,
                    "separation_se_cr1": se, "p_one_sided": p,
                    "BUY_mean_return": float(ret[x == 1].mean()), "NO_BUY_mean_return": float(ret[x == 0].mean()),
                    "return_lift": float(ret[x == 1].mean() - ret.mean()), "return_separation": rb, "return_p_one_sided": rp,
                    "NO_BUY_accuracy": 1 - hn})
    else:
        p = float("nan")
        out.update({"BUY_hit_rate": t0_hit if f == 1 else None, "lift": 0.0 if f == 1 else None, "p_one_sided": p})
    out["verdict"] = verdict(n, dates, p)
    if track == "T2":
        conf = np.array([float(r["t2_confidence"]) for r in rs])
        base = t0_hit
        brier = float(((conf - y) ** 2).mean())
        brier_ref = float(((base - y) ** 2).mean())
        cc = np.clip(conf, 0.01, 0.99)
        by_c = {}
        for i, c in enumerate(g):
            by_c.setdefault(c, []).append(i)
        by_c = {k: np.array(v) for k, v in by_c.items()}
        out["probability"] = {
            "brier": brier, "brier_reference_in_sample_base_rate": brier_ref,
            "brier_skill": 1 - brier / brier_ref if brier_ref else float("nan"),
            "log_loss": float(-(y * np.log(cc) + (1 - y) * np.log(1 - cc)).mean()),
            "auc": auc(conf, y), "auc_ci90_cluster": pairs_cluster_ci(lambda i: auc(conf[i], y[i]), by_c, rng),
            "share_conf_0.45_0.55": float(((conf >= 0.45) & (conf <= 0.55)).mean()),
            "calibration": [{"bin": f"{lo:.2f}-{hi:.2f}", "n": int(((conf >= lo) & (conf < hi)).sum()),
                             "mean_conf": float(conf[(conf >= lo) & (conf < hi)].mean()) if ((conf >= lo) & (conf < hi)).any() else None,
                             "hit_rate": float(y[(conf >= lo) & (conf < hi)].mean()) if ((conf >= lo) & (conf < hi)).any() else None}
                            for lo, hi in [(0, 0.4), (0.4, 0.5), (0.5, 0.6), (0.6, 1.01)]]}
    return out


def by_cluster(rows, track, rng):
    est = {}
    for c in sorted({r.get("cluster") for r in rows}):
        rs = [r for r in rows if r.get("cluster") == c and r["decisions"].get(track) in ("BUY", "NO_BUY")]
        if len(rs) < 2:
            continue
        y = np.array([1.0 if r["exits"]["exit_A"]["WIN_raw"] else 0.0 for r in rs])
        x = np.array([1.0 if r["decisions"][track] == "BUY" else 0.0 for r in rs])
        if 0 < x.mean() < 1 and len(set(r["entry_session"] for r in rs)) > 1:
            b, se, _ = ols_cluster(y, x, np.array([r["entry_session"] for r in rs]))
            est[c] = (b, se)
    return eb_shrink(est)


def load_rows(season):
    rows, voids, pending, ineligible = [], {}, 0, 0
    for p in sorted(glob.glob(os.path.join(ROOT, "outcomes", season, "*.json"))):
        o = json.load(open(p, encoding="utf-8"))
        if o.get("gate_status") != "PASS":
            ineligible += 1
        elif o.get("void"):
            voids[o["void"]] = voids.get(o["void"], 0) + 1
        elif o.get("graded"):
            rows.append(o)
        else:
            pending += 1
    return rows, voids, pending, ineligible


def run(season, write=False):
    rows, voids, pending, ineligible = load_rows(season)
    rng = np.random.default_rng(SEED)
    rep = {"season": season, "computed_et": now_et().isoformat(timespec="seconds"), "rule": "D005_evaluation_v1",
           "counts": {"graded": len(rows), "void": voids, "pending": pending, "ineligible_never_graded": ineligible,
                      "event_dates": len({r["entry_session"] for r in rows}),
                      "t2_missing": sum(1 for r in rows if r["decisions"].get("T2") is None)},
           "label": "PILOT - bugs, not findings" if season == "pilot" else "exploratory (not confirmatory)"}
    variants = {"all": rows,
                "excl_price_dispute": [r for r in rows if "price_dispute" not in r["exits"]["exit_A"].get("flags", [])],
                "excl_timing_unverified": [r for r in rows if "timing_unverified" not in r["flags"]],
                "excl_confound_8k": [r for r in rows if "confound_8k" not in r["flags"]]}
    rep["tracks"] = {}
    for track in ("T1", "T2"):
        rep["tracks"][track] = {v: evaluate(rs, track, rng) for v, rs in variants.items()}
        rep["tracks"][track]["by_cluster_partial_pooling"] = by_cluster(rows, track, rng)
    # secondary outcomes on the primary exit, and secondary exits, for T0 (always reported, labelled)
    sec = {}
    for key in ("exit_A", "exit_B", "exit_C"):
        rr = [r["exits"][key] for r in rows if "raw_return" in r["exits"].get(key, {})]
        if rr:
            sec[key] = {"n": len(rr), "WIN_raw": float(np.mean([e["WIN_raw"] for e in rr])),
                        "WIN_net": float(np.mean([e["WIN_net"] for e in rr])),
                        "WIN_excess": float(np.mean([e["WIN_excess"] for e in rr if "WIN_excess" in e])) if any("WIN_excess" in e for e in rr) else None,
                        "mean_raw_return": float(np.mean([e["raw_return"] for e in rr])),
                        "label": "PRIMARY outcome" if key == "exit_A" else "secondary"}
    rep["T0_by_exit"] = sec
    print(json.dumps(rep, indent=1, default=lambda v: None if isinstance(v, float) and v != v else str(v)))
    if write:
        stamp = now_et().strftime("%Y-%m-%d")
        write_json(os.path.join(ROOT, "outcomes", "reports", f"{season}_{stamp}.json"), rep)
    return rep


if __name__ == "__main__":
    a = sys.argv[1:]
    run(a[0], write="--write" in a)
