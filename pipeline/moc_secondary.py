"""D019 §3(a): the MOC secondary on SH-M and SH-W - code only. Rules: registry/D019_moc_secondary_v1.md.

    python pipeline/moc_secondary.py grade <season> [--no-fetch]   # fetch settled closes once, write moc.json
    python pipeline/moc_secondary.py report <season> [--write]      # the statistic; only Season B is evidence

The trade Jacob can place: buy at the close of D009's entry session (the last close before the print), sell at the
close of the reaction day (D001's exit-B session), both by market-on-close order.
- Events: D009's own, read from outcomes/shadow/<season>/graded.json (pipeline/shadow.py builds it): the same
  names, dates, sessions, VOID rules and 8-K timing check. An event counts only where D009 graded it.
- Prices: yfinance daily Close, auto_adjust=False (the official closing-auction price), settled sessions only,
  through D009's own fetch() into a separate write-once store, outcomes/shadow/<season>/moc_prices.jsonl.
  D009's prices.jsonl is never written. A missing price leaves the event ungraded; nothing is filled.
- Net of US$0.99 per order, two orders, at a stated US$1,000 notional (0.198%). The MOC spread is 0 in v1: the fill
  is the closing-auction price itself. A stress line deducts a further 0.10% (descriptive).
- The Gate 2 statistic is SH-M's net mean on Season B (point estimate >= +0.50%). Any other season prints
  DESCRIPTIVE, not evidence.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shadow  # noqa: E402
from common import ROOT, now_et, write_json  # noqa: E402

RULE = "D019_moc_secondary_v1"
FEES = 2 * 0.99 / 1000.0      # two orders of US$0.99 at a stated US$1,000 notional
STRESS = 0.001                # descriptive: a further 0.10% a round trip
BAR = 0.005                   # D019 §5, Gate 2: the point estimate >= +0.50%
EVIDENCE_SEASON = "seasonB"   # registered after Season A was read: only Season B counts
TRACKS = ("SH-M", "SH-W")     # SH-M is the Gate 2 statistic; SH-W a secondary
UNVERIFIED = ("late_8k", "timing_unverified")


def out_dir(season):
    return os.path.join(ROOT, "outcomes", "shadow", season)


class MocPrices(shadow.Prices):
    """D009's write-once price store, pointed at its own file."""

    def __init__(self, season):
        self.path = os.path.join(out_dir(season), "moc_prices.jsonl")
        self.rows, self.new = {}, []
        if os.path.exists(self.path):
            for line in open(self.path, encoding="utf-8"):
                r = json.loads(line)
                self.rows[(r["symbol"], r["session"], r["field"])] = r


def sessions_of(ev):
    """(entry session, exit session): the close before the print and the reaction-day close."""
    tm = ev["timing"]
    return tm["entry"]["session"], tm["exit_B"]["session"]


def needs_of(ev):
    e_s, x_s = sessions_of(ev)
    return {(e_s, "close"), (x_s, "close"), (x_s, f"div:{e_s}"), (x_s, f"split:{e_s}")}


def leg(prices, ev):
    """The MOC round trip from stored rows, or None while any price or the dividend field is missing."""
    e_s, x_s = sessions_of(ev)
    t = ev["ticker"]
    e, x = prices.get(t, e_s, "close"), prices.get(t, x_s, "close")
    div = prices.get(t, x_s, f"div:{e_s}")
    if e is None or x is None or div is None or not e:
        return None
    r = (x + div) / e - 1
    return {"entry_session": e_s, "exit_session": x_s, "entry_close": e, "exit_close": x, "dividends": div,
            "raw_return": r, "net_return": r - FEES, "WIN_raw": r > 0,
            "splits_in_window": [s for s in (prices.get(t, x_s, f"split:{e_s}") or []) if s]}


def build(events, prices):
    """One row per D009-graded SH-M / SH-W event. Pure: reads stored prices only."""
    rows = []
    for ev in events:
        if ev.get("track") not in TRACKS or not ev.get("graded"):
            continue
        lg = leg(prices, ev)
        void = "split_in_window" if lg and lg["splits_in_window"] else None
        rows.append({"track": ev["track"], "ticker": ev["ticker"], "date": ev["date"], "session": ev["session"],
                     "flags": ev.get("flags") or [], "moc": lg, "void": void,
                     "graded": bool(lg) and void is None})
    return rows


def grade(season, do_fetch=True):
    src = os.path.join(out_dir(season), "graded.json")
    if not os.path.exists(src):
        raise SystemExit(f"{src} missing - run `python pipeline/shadow.py grade {season}` first")
    events = shadow.load(src)["events"]
    prices = MocPrices(season)
    if do_fetch:
        needs = {}
        for ev in events:
            if ev.get("track") in TRACKS and ev.get("graded"):
                needs.setdefault(ev["ticker"], set()).update(needs_of(ev))
        shadow.fetch(prices, needs)
    rows = build(events, prices)
    write_json(os.path.join(out_dir(season), "moc.json"),
               {"season": season, "rule": RULE, "graded_by": "pipeline/moc_secondary.py",
                "graded_et": now_et().isoformat(timespec="seconds"), "evidence": season == EVIDENCE_SEASON,
                "events": rows})
    for tr in TRACKS:
        r = [x for x in rows if x["track"] == tr]
        print(f"{season} {tr} MOC: {len(r)} D009-graded events, {sum(x['graded'] for x in r)} with both closes, "
              f"{sum(1 for x in r if x['void'])} void")
    return rows


# ---------------------------------------------------------------- statistics

def t_quantile(p, df):
    """The p-quantile of Student's t (bisection on D015's t_cdf)."""
    from shadow_c1 import t_cdf
    lo, hi = -1e3, 1e3
    for _ in range(200):
        mid = (lo + hi) / 2
        if t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def summary(rows, name):
    """n, clusters, raw and net means, win rate, CR1 SE, the t(G - 1) 95% interval and the one-sided p."""
    g = [r for r in rows if r["graded"]]
    if not g:
        return {"n": 0, "dates": 0, "note": "no graded events"}
    y = [r["moc"]["net_return"] for r in g]
    cl = [r["moc"]["entry_session"] for r in g]
    res = shadow.mean_test(y, cl, name)
    res["raw_mean"] = sum(r["moc"]["raw_return"] for r in g) / len(g)
    res["win_rate"] = sum(r["moc"]["WIN_raw"] for r in g) / len(g)
    if res.get("mean") is not None:
        res["net_mean_stress"] = res["mean"] - STRESS
    se, G = res.get("se"), res.get("dates", 0)
    if se is not None and se == se and G >= 2:
        q = t_quantile(0.975, G - 1)
        res["ci95_t"] = [res["mean"] - q * se, res["mean"] + q * se]
    if "status" not in res:
        res["status"] = "insufficient"
    return res


def stats_(rows, season):
    out = {"season": season, "rule": RULE, "evidence": season == EVIDENCE_SEASON, "fees_round_trip": FEES,
           "tracks": {}}
    for tr in TRACKS:
        r = [x for x in rows if x["track"] == tr]
        main = summary(r, f"MOC-{tr}-{season}")
        clean = summary([x for x in r if not set(x["flags"]) & set(UNVERIFIED)], f"MOC-{tr}-{season}-clean")
        out["tracks"][tr] = {"all": main, "without_unverified_timing": clean}
    m = out["tracks"]["SH-M"]["all"]
    if out["evidence"] and m.get("mean") is not None:
        out["gate2"] = {"statistic": "SH-M MOC net mean, Season B", "point": m["mean"], "bar": BAR,
                        "met": m["mean"] >= BAR, "status": m["status"]}
    return out


def pct(x):
    return "n/a" if x is None or x != x else f"{x * 100:+.2f}%"


def lines(res):
    head = ("EVIDENCE: Season B, the Gate 2 statistic (D019 §5)" if res["evidence"] else
            "DESCRIPTIVE, not evidence (registry/D019_moc_secondary_v1.md §5: only Season B counts)")
    out = [f"# MOC secondary · {res['season']} · {head}", "",
           f"Close before the print -> reaction-day close; net of {res['fees_round_trip'] * 100:.3f}% fees "
           "(US$0.99 x 2 at US$1,000); MOC spread 0 by assumption (v1).", "",
           "| track | sample | n | sessions | raw mean | net mean | 95% (t, G-1) | p (one-sided) | win | net - 0.10% | status |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for tr, blk in res["tracks"].items():
        for label, s in (("all", blk["all"]), ("without unverified timing", blk["without_unverified_timing"])):
            ci = s.get("ci95_t")
            ci_txt = "n/a" if not ci else f"{pct(ci[0])} to {pct(ci[1])}"
            p_txt = "n/a" if s.get("p_one_sided") is None else f"{s['p_one_sided']:.4f}"
            win_txt = "n/a" if s.get("win_rate") is None else f"{s['win_rate'] * 100:.1f}%"
            out.append(f"| {tr} | {label} | {s.get('n', 0)} | {s.get('dates', 0)} | {pct(s.get('raw_mean'))} | "
                       f"{pct(s.get('mean'))} | {ci_txt} | {p_txt} | {win_txt} | {pct(s.get('net_mean_stress'))} | "
                       f"{s.get('status', s.get('note', ''))} |")
    if "gate2" in res:
        g = res["gate2"]
        out += ["", f"**Gate 2 bar:** SH-M net mean {pct(g['point'])} vs >= {pct(g['bar'])}: "
                    f"**{'met' if g['met'] else 'not met'}** (status {g['status']})."]
    return out


def report(season, write=False):
    p = os.path.join(out_dir(season), "moc.json")
    if not os.path.exists(p):
        raise SystemExit(f"{p} missing - run `python pipeline/moc_secondary.py grade {season}` first")
    res = stats_(shadow.load(p)["events"], season)
    text = "\n".join(lines(res)) + "\n"
    print(text)
    if write:
        path = os.path.join(ROOT, "outcomes", "reports", f"moc_secondary_{season}_{now_et():%Y-%m-%d}.md")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print("written", os.path.relpath(path, ROOT))
    return res


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == "grade":
        grade(a[1], "--no-fetch" not in a)
    elif len(a) >= 2 and a[0] == "report":
        report(a[1], "--write" in a)
    else:
        raise SystemExit(__doc__)
