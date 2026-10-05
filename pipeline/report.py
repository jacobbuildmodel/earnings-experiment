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
import zlib

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
    """Mann-Whitney AUC with ties counted half (average ranks)."""
    p, y = np.asarray(p, float), np.asarray(y, float)
    n1, n0 = int((y == 1).sum()), int((y == 0).sum())
    if not n1 or not n0:
        return float("nan")
    order = np.argsort(p, kind="mergesort")
    ranks = np.empty(len(p))
    sp = p[order]
    i = 0
    while i < len(sp):
        j = i
        while j + 1 < len(sp) and sp[j + 1] == sp[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return float((ranks[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


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


def ols_k(y, X, g, j):
    """General OLS with CR1 cluster-robust SE; returns (coef_j, se_j, t_j)."""
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    u = y - X @ beta
    groups, inv = np.unique(g, return_inverse=True)
    G, n, k = len(groups), len(y), X.shape[1]
    C = np.zeros((n, G))
    C[np.arange(n), inv] = 1.0
    S = (X * u[:, None]).T @ C                          # k x G
    adj = G / (G - 1) * (n - 1) / (n - k) if G > 1 and n > k else 1.0
    V = adj * XtX_inv @ (S @ S.T) @ XtX_inv
    se = math.sqrt(V[j, j]) if V[j, j] > 0 else float("nan")
    return float(beta[j]), se, float(beta[j] / se) if se == se and se else float("nan")


def wild_p_k(y, X, g, j, rng, two_sided=False):
    """Restricted wild cluster bootstrap-t for coefficient j of a k-regressor OLS (the null drops column
    j). One-sided H1: coef > 0 unless two_sided. Same weights rule as wild_cluster_p."""
    b, se, t = ols_k(y, X, g, j)
    if not t == t:
        return float("nan")
    groups, inv = np.unique(g, return_inverse=True)
    G, n, k = len(groups), len(y), X.shape[1]
    Xr = np.delete(X, j, axis=1)
    y0 = Xr @ np.linalg.lstsq(Xr, y, rcond=None)[0]
    u0 = y - y0
    A = np.linalg.inv(X.T @ X)
    H = A @ X.T
    C = np.zeros((n, G))
    C[np.arange(n), inv] = 1.0
    adj = G / (G - 1) * (n - 1) / (n - k) if G > 1 and n > k else 1.0
    W = rng.choice([-1.0, 1.0], (B_WILD, G)) if G >= 12 else rng.choice(WEBB, (B_WILD, G))
    Y = y0[None, :] + u0[None, :] * W[:, inv]
    beta = Y @ H.T                                      # B x k
    U = Y - beta @ X.T                                  # B x n
    S = np.stack([(U * X[:, r]) @ C for r in range(k)])  # k x B x G cluster scores
    M = np.einsum("rbg,sbg->brs", S, S)
    v = adj * np.einsum("r,brs,s->b", A[j], M, A[j])
    with np.errstate(invalid="ignore", divide="ignore"):
        tb = beta[:, j] / np.sqrt(v)
    hits = np.sum(np.abs(tb) >= abs(t)) if two_sided else np.sum(tb >= t)
    return (int(hits) + 1) / (B_WILD + 1)


def holm(pvals):
    """Holm step-down adjusted p-values, {name: p} -> {name: p_adj}."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, run, out = len(items), 0.0, {}
    for i, (k, p) in enumerate(items):
        run = max(run, min(1.0, (m - i) * p))
        out[k] = run
    return out


def bh(pvals):
    """Benjamini-Hochberg q-values, list of p -> list of q (same order)."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    q, prev = [0.0] * m, 1.0
    for rank in range(m, 0, -1):
        i = order[rank - 1]
        prev = min(prev, pvals[i] * m / rank)
        q[i] = prev
    return q


# ---------------------------------------------------------------- evaluation (D005 §2-§4)

def R(name):
    """An independent, reproducible random stream per test (implementation v2): adding or removing one
    test never changes another test's p-value."""
    return np.random.default_rng([SEED, zlib.crc32(name.encode("utf-8"))])


def sufficient(n, dates):
    return n >= MIN_EVENTS and dates >= MIN_DATES


def verdict(n, dates, p):
    """D005 v1 wording (still computed, rule 5). "confirmed" comes solely from confirmatory()."""
    if not sufficient(n, dates):
        return "insufficient"
    if p != p:
        return "no selection (track bought all or none)"
    return f"evidence of lift (exploratory, p={p:.3f})" if p < 0.05 else f"no evidence of lift (p={p:.3f})"


def verdict_v2(n, dates, p, return_lift):
    """D005 v2 wording: a directional lift only counts as a success with a non-negative return lift."""
    if not sufficient(n, dates):
        return "insufficient"
    if p != p:
        return "no selection (track bought all or none)"
    if p >= 0.05:
        return f"no evidence of directional lift (p={p:.3f})"
    if return_lift is not None and return_lift < 0:
        return f"directional lift WITHOUT return lift - not a success (p={p:.3f}, return lift {return_lift:+.4f})"
    return f"evidence of directional lift, return lift non-negative (exploratory, p={p:.3f})"


def win(r, key="exit_A"):
    return 1.0 if r["exits"][key]["WIN_raw"] else 0.0


def within_date(y, x, g):
    """Separation with entry-session fixed effects: only dates with both a BUY and a NO_BUY inform it."""
    yt, xt = y.astype(float).copy(), x.astype(float).copy()
    for c in np.unique(g):
        m = g == c
        yt[m] -= yt[m].mean()
        xt[m] -= xt[m].mean()
    keep = np.array([np.ptp(x[g == c]) > 0 for c in g])
    if keep.sum() < 3 or len(np.unique(g[keep])) < 2:
        return {"estimate": None, "note": "fewer than 2 entry sessions with both a BUY and a NO_BUY"}
    X = np.column_stack([np.zeros(keep.sum()) + 1e-12, xt[keep]])
    X[:, 0] = 1.0
    b, se, t = ols_k(yt[keep], X, g[keep], 1)
    return {"estimate": b, "se_cr1": se, "t_cr1": t, "sessions_used": int(len(np.unique(g[keep]))),
            "label": "robustness - descriptive"}


def leave_one_date_out(y, x, g):
    lifts = []
    for c in np.unique(g):
        m = g != c
        if 0 < x[m].mean() < 1:
            lifts.append(float(y[m][x[m] == 1].mean() - y[m].mean()))
    full = float(y[x == 1].mean() - y.mean())
    return {"lift_min": min(lifts) if lifts else None, "lift_max": max(lifts) if lifts else None,
            "sign_flips": int(sum(np.sign(v) != np.sign(full) for v in lifts)), "dates": len(lifts),
            "label": "robustness - descriptive"}


def legs(rs, x):
    """Secondary: exit A split into the pre-print session and the print gap, per set."""
    out = {}
    for name, m in (("all", np.ones(len(rs), bool)), ("BUY", x == 1), ("NO_BUY", x == 0)):
        sel = [r["exits"]["exit_A"].get("legs") for r, k in zip(rs, m) if k]
        sel = [s for s in sel if s]
        if sel:
            out[name] = {"n": len(sel),
                         "pre_print_mean": float(np.mean([s["pre_print"] for s in sel])),
                         "pre_print_up_share": float(np.mean([s["pre_print"] > 0 for s in sel])),
                         "print_gap_mean": float(np.mean([s["print_gap"] for s in sel])),
                         "print_gap_up_share": float(np.mean([s["print_gap"] > 0 for s in sel]))}
    out["label"] = "secondary"
    return out


def evaluate(rows, track, variant="all"):
    """One track against T0 on the events where the track has a decision. Only the "all" variant gets a
    verdict; robustness cuts are descriptive (implementation v2, external review 2026-09-21)."""
    rs = [r for r in rows if r["decisions"].get(track) in ("BUY", "NO_BUY")]
    n = len(rs)
    if not n:
        return {"track": track, "n": 0, "verdict": "no decisions"}
    tag = f"{track}/{variant}"
    y = np.array([win(r) for r in rs])
    ret = np.array([r["exits"]["exit_A"]["raw_return"] for r in rs])
    x = np.array([1.0 if r["decisions"][track] == "BUY" else 0.0 for r in rs])
    g = np.array([r["entry_session"] for r in rs])
    dates = len(set(g))
    f = float(x.mean())
    t0_hit = float(y.mean())
    out = {"track": track, "variant": variant, "n": n, "event_dates": dates, "buy_share": f,
           "T0_hit_rate": t0_hit, "T0_mean_return": float(ret.mean()), "sufficient": sufficient(n, dates)}
    p, rlift = float("nan"), None
    if 0 < f < 1:
        out.update({"BUY_hit_rate": float(y[x == 1].mean()), "NO_BUY_hit_rate": float(y[x == 0].mean()),
                    "NO_BUY_accuracy": float(1 - y[x == 0].mean()),
                    "BUY_mean_return": float(ret[x == 1].mean()), "NO_BUY_mean_return": float(ret[x == 0].mean()),
                    "exit_A_legs": legs(rs, x)})
        if out["sufficient"]:  # below the rule 7 minimum no effect size or p-value is produced to be quoted
            b, se, _ = ols_cluster(y, x, g)
            p = wild_cluster_p(y, x, g, R(tag + "/win"))
            rb, _, _ = ols_cluster(ret, x, g)
            rlift = float(ret[x == 1].mean() - ret.mean())
            out.update({"lift": float(y[x == 1].mean() - t0_hit), "separation": b, "separation_se_cr1": se,
                        "p_one_sided": p, "return_lift": rlift, "return_separation": rb,
                        "return_p_one_sided": wild_cluster_p(ret, x, g, R(tag + "/ret")),
                        "within_date": within_date(y, x, g), "leave_one_date_out": leave_one_date_out(y, x, g)})
    elif f == 1:
        out.update({"BUY_hit_rate": t0_hit, "lift": 0.0})
    if variant == "all":
        out["verdict_D005_v1"] = verdict(n, dates, p)
        out["verdict"] = verdict_v2(n, dates, p, rlift)
        if out["verdict"].startswith("evidence") or out["verdict"].startswith("directional"):
            out["power_note"] = ("at this sample size a significant result is quite likely a false positive and "
                                 "overstates the true edge (D005 v1 §7, v2 §5)")
    else:
        out["verdict"] = "robustness cut - descriptive, no verdict"
    if track in ("T2", "T2G"):
        conf_all = [r.get("t2_confidence" if track == "T2" else "t2g_confidence") for r in rs]
        ok = np.array([c is not None and isinstance(c, (int, float)) and math.isfinite(c) for c in conf_all])
        conf = np.array([float(c) for c, k in zip(conf_all, ok) if k])
        yy, gg = y[ok], g[ok]
        out["t2_confidence_missing"] = int((~ok).sum())
        if len(conf):
            brier = float(((conf - yy) ** 2).mean())
            brier_ref = float(((yy.mean() - yy) ** 2).mean())
            cc = np.clip(conf, 0.01, 0.99)
            by_c = {}
            for i, c in enumerate(gg):
                by_c.setdefault(c, []).append(i)
            by_c = {k: np.array(v) for k, v in by_c.items()}
            bins = []
            for lo, hi in [(0, 0.4), (0.4, 0.5), (0.5, 0.6), (0.6, 1.01)]:
                m = (conf >= lo) & (conf < hi)
                bins.append({"bin": f"{lo:.2f}-{min(hi, 1):.2f}", "n": int(m.sum()),
                             "mean_conf": float(conf[m].mean()) if m.any() else None,
                             "hit_rate": float(yy[m].mean()) if m.any() else None})
            prob = {
                "n": int(len(conf)), "brier": brier, "brier_reference_in_sample_base_rate": brier_ref,
                "brier_skill": 1 - brier / brier_ref if brier_ref else float("nan"),
                "log_loss": float(-(yy * np.log(cc) + (1 - yy) * np.log(1 - cc)).mean()),
                "auc": auc(conf, yy),
                "auc_ci90_cluster": pairs_cluster_ci(lambda i: auc(conf[i], yy[i]), by_c, R(tag + "/auc")) if len(by_c) > 1 else None,
                "share_conf_0.45_0.55": float(((conf >= 0.45) & (conf <= 0.55)).mean()), "calibration": bins}
            # D005 v2: does the confidence number itself rank outcomes? WIN = a + b*confidence, clustered.
            if sufficient(len(conf), len(set(gg))) and np.ptp(conf) > 0:
                Xc = np.column_stack([np.ones(len(conf)), conf])
                cb, cse, ct = ols_k(yy, Xc, gg, 1)
                prob["confidence_test"] = {"slope": cb, "se_cr1": cse, "t_cr1": ct,
                                           "p_one_sided": wild_p_k(yy, Xc, gg, 1, R(tag + "/conf"))}
            out["probability"] = prob
    return out


def t2_vs_t1(rows):
    """D005 §3: stacked WIN = a + g*T2 + b*BUY + d*BUY*T2, clustered by entry session; test d > 0."""
    rs = [r for r in rows if r["decisions"].get("T1") in ("BUY", "NO_BUY") and r["decisions"].get("T2") in ("BUY", "NO_BUY")]
    dates = len({r["entry_session"] for r in rs})
    out = {"n_events": len(rs), "event_dates": dates, "sufficient": sufficient(len(rs), dates)}
    if not out["sufficient"]:
        out["verdict"] = "insufficient"
        return out
    y, X, g = [], [], []
    for r in rs:
        for is_t2, tr in ((0.0, "T1"), (1.0, "T2")):
            buy = 1.0 if r["decisions"][tr] == "BUY" else 0.0
            y.append(win(r)); X.append([1.0, is_t2, buy, buy * is_t2]); g.append(r["entry_session"])
    y, X, g = np.array(y), np.array(X), np.array(g)
    if np.linalg.matrix_rank(X) < 4:
        out["verdict"] = "no selection in one track"
        return out
    d, se, t = ols_k(y, X, g, 3)
    p = wild_p_k(y, X, g, 3, R("T2_vs_T1"))
    out.update({"delta": d, "delta_se_cr1": se, "p_one_sided": p,
                "verdict": f"T2 separates better than T1 (exploratory, p={p:.3f})" if p < 0.05 else f"no evidence T2 beats T1 (p={p:.3f})"})
    return out


def confirmatory(season, tracks, stacked):
    """Holm over the hypotheses registered for this season in registry/D005_confirmatory_<season>.json.
    With no registration there is no confirmatory verdict at all (D005 §4)."""
    path = os.path.join(ROOT, "registry", f"D005_confirmatory_{season}.json")
    if not os.path.exists(path):
        return {"registered": False, "note": "no confirmatory hypotheses registered for this season - nothing can be 'confirmed'"}
    from common import registry
    reg = registry(f"D005_confirmatory_{season}.json")   # refuses an unfrozen file
    raw = {}
    for h in reg["hypotheses"]:
        if h["test"] == "T1_lift":
            raw[h["id"]] = tracks["T1"]["all"].get("p_one_sided", float("nan"))
        elif h["test"] == "T2_lift":
            raw[h["id"]] = tracks["T2"]["all"].get("p_one_sided", float("nan"))
        elif h["test"] == "T2_vs_T1":
            raw[h["id"]] = stacked.get("p_one_sided", float("nan"))
        elif h["test"] == "T2_confidence":
            raw[h["id"]] = (tracks["T2"]["all"].get("probability", {}).get("confidence_test") or {}).get("p_one_sided", float("nan"))
    raw = {k: (1.0 if v != v else v) for k, v in raw.items()}  # an untestable hypothesis is not confirmed
    adj = holm(raw)
    # D005 v2 §1: a lift hypothesis is confirmed only with a non-negative return lift as well
    rl = {h["id"]: tracks[h["test"][:2]]["all"].get("return_lift") for h in reg["hypotheses"]
          if h["test"] in ("T1_lift", "T2_lift")}
    verdicts = {}
    for k in adj:
        ok = adj[k] < 0.05 and (k not in rl or (rl[k] is not None and rl[k] >= 0))
        verdicts[k] = "confirmed" if ok else "not confirmed"
    return {"registered": True, "alpha": 0.05, "raw_p": raw, "holm_p": adj, "return_lift": rl, "verdicts": verdicts}


def h_s0(rows):
    """D008 §2 H-S0 (implementation v3, 2026-10-02): S0's mean exit-A raw return net of the 0.20% round
    trip is > 0. Sample: graded PASS events (S0 buys every one). One-sided, the D005 restricted wild
    cluster bootstrap by entry session on an intercept-only model. Interim runs are monitoring; the
    registered test is on Seasons A + B pooled (D008 §2)."""
    rr = [r for r in rows if "raw_return" in r["exits"]["exit_A"]]
    y = np.array([r["exits"]["exit_A"]["raw_return"] - 0.002 for r in rr], float)
    g = np.array([r["entry_session"] for r in rr])
    out = {"hypothesis": "D008 H-S0: mean net exit-A return > 0", "n": len(rr), "dates": len(set(g)),
           "net_mean": float(y.mean()) if len(y) else None}
    if len(y) < 3 or len(set(g)) < 2:
        return {**out, "verdict": "insufficient"}
    X = np.ones((len(y), 1))
    b, se, t = ols_k(y, X, g, 0)
    p = wild_p_k(y, X, g, 0, R("H-S0"))
    v = "insufficient" if not sufficient(len(y), len(set(g))) else (
        f"net mean > 0 at p={p:.3f} (this season alone; Gate 2 pools A + B)" if p < 0.05 else f"no evidence (p={p:.3f})")
    return {**out, "se": se, "t": t, "p_one_sided": p, "verdict": v}


def by_cluster(rows, track):
    """Every cluster is listed; under the rule 7 minimum it is 'insufficient' whatever its estimate."""
    est, listing = {}, {}
    for c in sorted({r.get("cluster") for r in rows}, key=str):
        rs = [r for r in rows if r.get("cluster") == c and r["decisions"].get(track) in ("BUY", "NO_BUY")]
        dates = len({r["entry_session"] for r in rs})
        listing[c] = {"n": len(rs), "event_dates": dates, "status": "sufficient" if sufficient(len(rs), dates) else "insufficient"}
        if len(rs) < 2:
            continue
        y = np.array([win(r) for r in rs])
        x = np.array([1.0 if r["decisions"][track] == "BUY" else 0.0 for r in rs])
        if 0 < x.mean() < 1 and dates > 1:
            b, se, _ = ols_cluster(y, x, np.array([r["entry_session"] for r in rs]))
            est[c] = (b, se)
    pooled = eb_shrink(est)
    for c, v in (pooled.get("clusters") or {}).items():
        if listing[c]["status"] == "sufficient":
            listing[c].update(v)
    return {"clusters": listing, "pooled": pooled.get("pooled"), "tau2": pooled.get("tau2")}


def numeric_factors(season, event):
    p = os.path.join(ROOT, "events", season, event, "factors.json")
    if not os.path.exists(p):
        return {}
    out = {}
    for k, v in (json.load(open(p, encoding="utf-8")).get("factors") or {}).items():
        val = v.get("value") if isinstance(v, dict) else None
        if isinstance(val, (int, float)) and not isinstance(val, bool) and math.isfinite(val):
            out[k] = float(val)
    return out


def factor_table(season, rows):
    """D005 §5 exploration. Every test run is listed and counted; BH across all of them; a CANDIDATE
    needs q < 0.10, |t| > 3 and the same sign in both halves (split at the median entry session)."""
    facs = {r["event"]: numeric_factors(season, r["event"]) for r in rows}
    names = sorted({k for f in facs.values() for k in f})
    groups = {"all": rows}
    for c in sorted({r.get("cluster") for r in rows}, key=str):
        groups[f"cluster={c}"] = [r for r in rows if r.get("cluster") == c]
    tests = []
    for fac in names:
        for gname, grs in groups.items():
            rs = [r for r in grs if fac in facs[r["event"]]]
            if len(rs) < 9:
                continue
            v = np.array([facs[r["event"]][fac] for r in rs])
            lo, hi = np.quantile(v, [1 / 3, 2 / 3])
            sel = [(r, 1.0 if x >= hi else 0.0) for r, x in zip(rs, v) if x <= lo or x >= hi]
            if len({t for _, t in sel}) < 2 or len({r["entry_session"] for r, _ in sel}) < 2:
                continue
            med = sorted(r["entry_session"] for r in rs)[len(rs) // 2]
            for oname, fy in (("WIN_raw", win), ("raw_return", lambda r: r["exits"]["exit_A"]["raw_return"])):
                y = np.array([fy(r) for r, _ in sel])
                x = np.array([t for _, t in sel])
                g = np.array([r["entry_session"] for r, _ in sel])
                X = np.column_stack([np.ones_like(x), x])
                eff, se, t = ols_k(y, X, g, 1)
                p = wild_p_k(y, X, g, 1, R(f"factor/{fac}/{gname}/{oname}"), two_sided=True)
                halves = []
                for first in (True, False):
                    m = np.array([(r["entry_session"] < med) == first for r, _ in sel])
                    if (x[m] == 1).any() and (x[m] == 0).any():
                        halves.append(float(y[m][x[m] == 1].mean() - y[m][x[m] == 0].mean()))
                tests.append({"factor": fac, "group": gname, "outcome": oname, "n": len(sel),
                              "event_dates": len(set(g)), "effect_top_minus_bottom": eff, "t_cr1": t, "p_two_sided": p,
                              "halves": halves})
    qs = bh([x["p_two_sided"] if x["p_two_sided"] == x["p_two_sided"] else 1.0 for x in tests]) if tests else []
    for x, q in zip(tests, qs):
        same = len(x["halves"]) == 2 and np.sign(x["halves"][0]) == np.sign(x["halves"][1]) == np.sign(x["effect_top_minus_bottom"])
        x["q_bh"] = q
        x["status"] = ("insufficient" if not sufficient(x["n"], x["event_dates"]) else
                       "CANDIDATE" if (q < 0.10 and abs(x["t_cr1"]) > 3 and same) else "not promoted")
    return {"tests_run": len(tests), "candidates": [x for x in tests if x["status"] == "CANDIDATE"],
            "note": "B-family factors are measured only on implied move >= 4% (D003 gate) - truncated range",
            "tests": tests}


def gate_selectivity(season):
    """How hard the S2 gate bit, per cluster and per business stage, over every gated event - including
    the INELIGIBLE ones (external review 2026-09-21: a cluster comparison is also a comparison of how
    selective the gate was). Descriptive."""
    cands = {}
    for name in ("candidates.json", "candidates_midseason.json"):
        cp = os.path.join(ROOT, "universe", season, name)
        if os.path.exists(cp):
            cands.update({c["ticker"]: c for c in json.load(open(cp, encoding="utf-8"))["candidates"]})
    groups = {}
    for gp in glob.glob(os.path.join(ROOT, "events", season, "*", "gate.json")):
        g = json.load(open(gp, encoding="utf-8"))
        if g.get("dry"):
            continue
        fp = os.path.join(os.path.dirname(gp), "factors.json")
        stage = None
        if os.path.exists(fp):
            stage = ((json.load(open(fp, encoding="utf-8")).get("factors") or {}).get("K_stage") or {}).get("value")
        im = (g.get("options") or {}).get("implied_move")
        for key in (f"cluster={cands.get(g['ticker'], {}).get('cluster')}", f"stage={stage}"):
            d = groups.setdefault(key, {"gated": 0, "passed": 0, "reasons": {}, "implied_moves": []})
            d["gated"] += 1
            d["passed"] += g["status"] == "PASS"
            if g["status"] != "PASS":
                d["reasons"][g.get("reason")] = d["reasons"].get(g.get("reason"), 0) + 1
            if im is not None:
                d["implied_moves"].append(im)
    out = {}
    for k, d in sorted(groups.items()):
        ims = d.pop("implied_moves")
        out[k] = {**d, "pass_rate": d["passed"] / d["gated"], "mean_implied_move_all_gated": float(np.mean(ims)) if ims else None}
    return {"groups": out, "label": "descriptive"}


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


def implementation_status():
    """D005 §8: are grade.py and report.py the registered implementation?"""
    import hashlib
    reg = os.path.join(ROOT, "registry", "D005_implementation_v1.sha256")
    if not os.path.exists(reg):
        return "unregistered"
    want = {}
    for line in open(reg, encoding="utf-8"):
        if line.strip() and not line.startswith("#"):
            h, name = line.split(maxsplit=1)
            want[name.strip()] = h
    got = {n: hashlib.sha256(open(os.path.join(ROOT, n), "rb").read().replace(b"\r\n", b"\n")).hexdigest() for n in want}
    return "registered (matches the latest version in D005_implementation_v1.sha256)" if got == want else f"CHANGED since registration: {[n for n in want if got[n] != want[n]]}"


def run(season, write=False):
    rows, voids, pending, ineligible = load_rows(season)
    rep = {"season": season, "computed_et": now_et().isoformat(timespec="seconds"), "rule": "D005_evaluation_v1",
           "implementation": implementation_status(),
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
        rep["tracks"][track] = {v: evaluate(rs, track, v) for v, rs in variants.items()}
        rep["tracks"][track]["by_cluster_partial_pooling"] = by_cluster(rows, track)
    # D004 v4: the Gemini shadow (T2G) is evaluated like a track but labelled SHADOW; never in the confirmatory family
    if any(r["decisions"].get("T2G") for r in rows):
        rep["tracks_shadow"] = {"T2G": {"all": evaluate(rows, "T2G", "all"), "label": "SHADOW (D004 v4 T2G)"}}
    rep["T2_vs_T1"] = t2_vs_t1(rows)
    rep["gate_selectivity"] = gate_selectivity(season)
    rep["confirmatory"] = confirmatory(season, rep["tracks"], rep["T2_vs_T1"])
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
    rep["H_S0"] = h_s0(rows)
    rep["findings"] = factor_table(season, rows)
    summary = {k: v for k, v in rep.items() if k != "findings"}
    summary["findings"] = {k: v for k, v in rep["findings"].items() if k != "tests"}
    print(json.dumps(summary, indent=1, default=str))
    if write:
        stamp = now_et().strftime("%Y-%m-%d")
        write_json(os.path.join(ROOT, "outcomes", "reports", f"{season}_{stamp}.json"), rep)
    return rep


if __name__ == "__main__":
    a = sys.argv[1:]
    run(a[0], write="--write" in a)
