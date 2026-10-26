"""Peak capacity (STATE plan, "Peak capacity, computed by Oct 27"): can the paper accounts, the AI allowance and the
S2/T2 timing carry the Nov 2-6 peak? Code only, read-only: it reads the event calendar, the gate files and the
paper ledgers' SIZING fields (n, mid, wings, the opening natural, equity). It never reads a result, a P&L or C1.

    python ops/capacity_peak.py            # the tables behind ops/capacity_peak_2026-11.md
    python ops/capacity_peak.py --spot     # also price the upcoming names (one yfinance batch call)

Model, per event (D001 timing, D003 v4 snapshot offsets):
- gate on the snapshot session S (BMO: D-2, AMC: D-1); the reaction session R (BMO: D, AMC: D+1)
- butterfly (main account) and long straddle (second account) for every gate with quotes: open on S, close on R
  from 14:30 ET, so on day X both are alive for every event with S <= X <= R (the window's worst case)
- T0 stock (main account) for every PASS: bought at the open after S, sold at the next open; the evening
  before an open the account carries yesterday's buys plus the queued new buys
- PASS = gates x Season A's pass rate; T2 = 3 AI calls per PASS (T2, T2R, T2O)
"""
import datetime
import glob
import json
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
from sessions import shift  # noqa: E402

D = datetime.date.fromisoformat
FROM, TO = D("2026-10-26"), D("2026-11-13")
RISK = 0.005            # D011 / paper.py: equity at risk per event
MAX_POSITION = 0.10     # paper.py: stock cap per name


def load(p):
    return json.load(open(os.path.join(ROOT, p), encoding="utf-8"))


def q(xs, f):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(f * len(xs)))] if xs else None


def calendar():
    """[(ticker, report_date, session or None, status)] for Season A, the dated names."""
    out = []
    for k, ev in load("universe/seasonA/event_status.json")["events"].items():
        st = ev["status"]
        if st in ("CONFIRMED", "FROZEN"):
            out.append((k, D(ev["calendar_date"]), ev["session"], st))
        elif st == "PENDING" and ev.get("calendar_dates"):
            out.append((k, D(ev["calendar_dates"][0]), None, st))
    return out


def legs(report, session):
    s = shift(report, -2 if session == "BMO" else -1)
    r = shift(report, 0 if session == "BMO" else 1)
    return s, r


def gate_stats():
    ims, passes, n = [], 0, 0
    for g in glob.glob(os.path.join(ROOT, "events", "seasonA", "*", "gate.json")):
        j = json.load(open(g, encoding="utf-8"))
        n += 1
        passes += j.get("status") == "PASS"
        im = (j.get("options") or {}).get("implied_move")
        if im:
            ims.append(im)
    return n, passes, ims


def ledger_sizing(path, structure):
    """Sizing per trade, from fields fixed at the open: no result is read."""
    rows, skipped = [], 0
    for t in load(path)["trades"].values():
        skipped += bool(t.get("skipped"))
        if t.get("skipped") or not t.get("legs") or not t.get("gate_straddle_mid"):
            continue
        mid, n, eq, k = t["gate_straddle_mid"], t["n"], t["equity"], t["strike"]
        nat = next((r.get("natural") for r in (t.get("orders") or {}).get("open", []) if r.get("natural") is not None),
                   None)
        row = {"key": t["key"], "mid": mid, "n": n, "eq": eq, "at": t.get("created_et") or "",
               "floor": n == 1 and RISK * eq / (100 * mid) < 1}
        if structure == "F":
            lo, hi = t["wings"]
            w = max(hi - k, k - lo)
            credit = -nat if nat is not None else None
            row.update(w_over_mid=w / mid, credit_over_mid=None if credit is None else credit / mid,
                       margin_pct=None if credit is None else (w - credit) * 100 * n / eq)
        else:
            row.update(cost_pct=None if nat is None else nat * 100 * n / eq,
                       debit_over_mid=None if nat is None else nat / mid)
        rows.append(row)
    return rows, skipped / (skipped + len(rows))


def spots(tickers):
    import yfinance as yf
    h = yf.download(sorted(tickers), period="5d", progress=False, auto_adjust=False, threads=True)["Close"]
    last = h.ffill().iloc[-1]
    return {t: float(last[t]) for t in tickers if t in last and last[t] == last[t]}


def main(with_spot):
    cal = [c for c in calendar() if FROM - datetime.timedelta(days=7) <= c[1] <= TO + datetime.timedelta(days=7)]
    n_g, n_p, ims = gate_stats()
    rate = n_p / n_g
    im_med = statistics.median(ims)
    print(f"Season A gates so far {n_g}, PASS {n_p} -> pass rate {rate:.0%}; implied move median {im_med:.3f}, "
          f"p90 {q(ims, .9):.3f} (n={len(ims)})")

    # ---- 1. the calendar: prints by report date, gates by snapshot session (PENDING without a session: half each)
    by_report, by_gate = {}, {}
    for tk, rd, ses, st in cal:
        k = "pending" if st == "PENDING" else ses
        by_report.setdefault(rd, {}).setdefault(k, 0)
        by_report[rd][k] += 1
        for s_, w in ([(ses, 1.0)] if ses else [("BMO", .5), ("AMC", .5)]):
            s, _ = legs(rd, s_)
            by_gate.setdefault(s, {"confirmed": 0.0, "pending": 0.0})
            by_gate[s]["pending" if st == "PENDING" else "confirmed"] += w
    print("\n## prints by report date (Season A)")
    print("| date | BMO | AMC | pending | all |")
    for d in sorted(x for x in by_report if FROM <= x <= TO):
        r = by_report[d]
        print(f"| {d:%a %b %d} | {r.get('BMO', 0)} | {r.get('AMC', 0)} | {r.get('pending', 0)} | {sum(r.values())} |")
    print("\n## gates by snapshot session (pending names: half BMO, half AMC)")
    print("| S2 day | confirmed | + pending (est.) | gates | PASS at Season A's rate | AI calls (3 per PASS) |")
    for d in sorted(x for x in by_gate if FROM <= x <= TO):
        g = by_gate[d]
        tot = g["confirmed"] + g["pending"]
        print(f"| {d:%a %b %d} | {g['confirmed']:.0f} | {g['pending']:.1f} | {tot:.1f} | {tot * rate:.1f} | "
              f"{3 * tot * rate:.0f} |")

    # ---- 2. what one structure has cost so far (sizing fields only)
    f_rows, f_skip = ledger_sizing("paper/options_ledger.json", "F")
    l_rows, l_skip = ledger_sizing("paper/long_ledger.json", "L")
    fm = [r["margin_pct"] for r in f_rows if r["margin_pct"] is not None]
    lc = [r["cost_pct"] for r in l_rows if r["cost_pct"] is not None]
    wm = [r["w_over_mid"] for r in f_rows]
    cm = [r["credit_over_mid"] for r in f_rows if r["credit_over_mid"] is not None]
    dm = [r["debit_over_mid"] for r in l_rows if r["debit_over_mid"] is not None]
    eq_f = max(f_rows, key=lambda r: r["at"])["eq"]          # the equity at the latest open
    eq_l = max(l_rows, key=lambda r: r["at"])["eq"]
    print("\n## one structure so far (opening natural; no result read)")
    print(f"butterfly n={len(fm)}: margin % of equity median {statistics.median(fm):.2%}, p90 {q(fm, .9):.2%}, "
          f"max {max(fm):.2%}; wing width / straddle mid median {statistics.median(wm):.2f}; "
          f"credit / mid median {statistics.median(cm):.2f}; n=1 floor binding {sum(r['floor'] for r in f_rows)}")
    print(f"long straddle n={len(lc)}: cost % of equity median {statistics.median(lc):.2%}, p90 {q(lc, .9):.2%}, "
          f"max {max(lc):.2%}; debit / mid median {statistics.median(dm):.2f}; "
          f"n=1 floor binding {sum(r['floor'] for r in l_rows)}")
    print(f"equity at the latest open: main {eq_f} / second {eq_l}; gates skipped (no wing strike etc.): "
          f"main {f_skip:.0%}, second {l_skip:.0%}")

    # ---- 3. the peak, priced per name (needs spot)
    if not with_spot:
        return
    upcoming = [c for c in cal if legs(c[1], c[2] or "BMO")[1] >= FROM and legs(c[1], c[2] or "AMC")[0] <= TO]
    sp = spots({c[0].replace(".", "-") for c in upcoming})
    w_r, c_r, d_r = statistics.median(wm), statistics.median(cm), statistics.median(dm)
    days = [d for d in (FROM + datetime.timedelta(days=i) for i in range((TO - FROM).days + 1)) if d.weekday() < 5
            and d != D("2026-11-26")]
    fly, lng, stk_buy, missing = {d: 0.0 for d in days}, {d: 0.0 for d in days}, {d: 0.0 for d in days}, []
    n_alive, fly_lo = {d: 0.0 for d in days}, {d: 0.0 for d in days}
    per_name, structs = [], []
    for tk, rd, ses, st in upcoming:
        s0 = sp.get(tk.replace(".", "-"))
        if not s0:
            missing.append(tk)
            continue
        mid = s0 * im_med
        for s_, wgt in ([(ses, 1.0)] if ses else [("BMO", .5), ("AMC", .5)]):
            s, r = legs(rd, s_)
            n_f = max(1, int(RISK * eq_f / (100 * mid)))
            n_l = max(1, int(RISK * eq_l / (100 * mid)))
            m_f = (w_r - c_r) * mid * 100 * n_f / eq_f
            m_l = d_r * mid * 100 * n_l / eq_l
            stock = min(RISK / im_med, MAX_POSITION)          # notional / equity for one PASS
            entry = shift(s, 1)
            per_name.append((m_f, tk, s0, n_f))
            structs.append((s, r, tk, wgt, m_f, m_l))
            for d in days:
                if s <= d <= r:
                    fly[d] += wgt * (1 - f_skip) * m_f
                    lng[d] += wgt * (1 - l_skip) * m_l
                    n_alive[d] += wgt * (1 - f_skip)
                if s <= d < r:
                    fly_lo[d] += wgt * (1 - f_skip) * m_f
                if d == entry:
                    stk_buy[d] += wgt * rate * stock
    print(f"\n## the peak, priced (spot from yfinance; straddle mid = spot x {im_med:.3f}; wing/mid {w_r:.2f}, "
          f"credit/mid {c_r:.2f}, debit/mid {d_r:.2f}); no spot for {missing}")
    print("| day | butterflies alive (S<=day<=R) | butterfly margin % main, closes first - all alive | "
          "long straddle cost % second | T0 stock held overnight + queued % main (expected) |")
    for d in days:
        prev = shift(d, -1) if shift(d, -1) in stk_buy else None
        held = (stk_buy.get(prev) or 0) + stk_buy[d]
        print(f"| {d:%a %b %d} | {n_alive[d]:.0f} | {fly_lo[d]:.0%} - {fly[d]:.0%} | {lng[d]:.0%} | {held:.0%} |")
    top = sorted({tk: (m, tk, s0, n) for m, tk, s0, n in per_name}.values(), reverse=True)
    print("largest butterfly margins (one name, % of main equity, n):",
          ", ".join(f"{tk} {m:.1%} (spot {s0:.0f}, n={n})" for m, tk, s0, n in top[:8]))

    # ---- 4. refused opens (`capacity`, never simulated): day by day, closes free their margin first, then the
    # day's opens go in the order the code sends them (gate files sorted by path = by ticker) until the account's
    # options buying power (~ its equity, D011 §2 probe) is used up. A refused open holds nothing later.
    def simulate(col, skip, cap_of):
        live, out = [], {}
        for d in days:
            live = [x for x in live if x[1] > d]
            used = sum(x[3] * (1 - skip) * x[col] for x in live)
            want = sorted((x for x in structs if x[0] == d or (d == days[0] and x[0] < d)), key=lambda x: x[2])
            refused = sent = 0.0
            for x in want:
                need = x[3] * (1 - skip) * x[col]
                if x[0] < d or used + need <= cap_of(d):        # opened before the first day: already held
                    live.append(x)
                    used += need
                    sent += x[3] * (1 - skip)
                else:
                    refused += x[3] * (1 - skip)
            out[d] = (sent, refused, used)
        return out

    dpz = 30000 / eq_f                                     # STATE: DPZ's 100 shares tie up ~$30k
    main_dpz = simulate(4, f_skip, lambda d: 1.0 - dpz - 0.5 * stk_buy[d])
    main_flat = simulate(4, f_skip, lambda d: 1.0 - 0.5 * stk_buy[d])
    second = simulate(5, l_skip, lambda d: 1.0)
    print("\n## refused opens (`capacity`) per day: main with DPZ held / main with DPZ flattened / second account")
    print("| S2 day | structures wanted | main refused (DPZ held) | main refused (DPZ flat) | second refused |")
    tot = [0.0, 0.0, 0.0, 0.0]
    for d in days:
        if d == days[0]:
            continue
        w = main_flat[d][0] + main_flat[d][1]
        row = (w, main_dpz[d][1], main_flat[d][1], second[d][1])
        tot = [a + b for a, b in zip(tot, row)]
        if w:
            print(f"| {d:%a %b %d} | {row[0]:.0f} | {row[1]:.0f} | {row[2]:.0f} | {row[3]:.0f} |")
    print(f"| total | {tot[0]:.0f} | {tot[1]:.0f} ({tot[1] / tot[0]:.0%}) | {tot[2]:.0f} ({tot[2] / tot[0]:.0%}) | "
          f"{tot[3]:.0f} ({tot[3] / tot[0]:.0%}) |")


if __name__ == "__main__":
    main("--spot" in sys.argv[1:])
