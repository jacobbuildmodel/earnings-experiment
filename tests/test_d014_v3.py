"""D014 v3: the entry minute, the first quote, the retail net arithmetic, survivor labels.
Run: python -m pytest tests/test_d014_v3.py -q"""
import csv
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "analysis", "d014"))
sys.path.insert(0, os.path.dirname(__file__))
import fetch  # noqa: E402
import fetch_v3  # noqa: E402
import run_d014 as rd  # noqa: E402
import run_d014_v3 as r3  # noqa: E402
import test_d014_v2 as t2  # noqa: E402

D = datetime.date(2025, 3, 4)


def b(hhmm, vw):
    return {"t": fetch.at(D, hhmm).astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "vw": vw}


def test_entry_bar_takes_the_open_minute_or_later():
    bars = [b("09:30", 10.0), b("09:34", 10.4), b("09:35", 10.5)]
    t, vw = fetch_v3.entry_bar(bars, fetch.at(D, "09:34").replace(second=48))      # delayed NYSE open 09:34:48
    assert vw == 10.4 and t.minute == 34
    assert fetch_v3.entry_bar(bars, fetch.at(D, "09:30"))[1] == 10.0
    assert fetch_v3.entry_bar([b("09:51", 9.0)], fetch.at(D, "09:50")) == (None, None)


def test_first_quote(monkeypatch):
    seen = {}

    def get(path, params):
        seen.update(params)
        return {"quotes": [{"bp": 9.9, "ap": 10.1}]}
    monkeypatch.setattr(fetch, "get", get)
    bid, ask, hs = fetch_v3.first_quote("X", fetch.at(D, "09:30"))
    assert (bid, ask) == (9.9, 10.1) and abs(hs - 0.01) < 1e-12 and seen["sort"] == "asc"


def test_retail_net_arithmetic():
    e = {"s": 1, "o": 100.0, "vw": 101.0, "hs_first": 0.002, "first_bid": 100.8, "first_ask": 101.2,
         "p": {"c": 103.0}, "mid": {"0935": 102.0}, "hs": {"0935": 0.001}}
    E, X = 101.0 * 1.002, 102.0 * 0.999
    assert abs(r3.retail_net(e, "5", 1) - (X / E - 1 - 0.0002)) < 1e-12              # follow = buy
    E2, X2 = 101.0 * 0.998, 102.0 * 1.001
    assert abs(r3.retail_net(e, "5", -1) - (-(X2 / E2 - 1) - 0.0002)) < 1e-12        # fade = short
    assert abs(r3.retail_net(e, "c", 1, "far_side") - (103.0 / 101.2 - 1 - 0.0002)) < 1e-12
    assert abs(r3.retail_net(e, "c", 1, "auction") - (103.0 / 100.0 - 1 - 0.0002)) < 1e-12


def test_labels_end_to_end(tmp_path, monkeypatch):
    t2.synthetic(tmp_path, monkeypatch, effect=0.003)
    rows = list(csv.DictReader(open(tmp_path / "raw" / "events_v2.csv")))
    with open(tmp_path / "raw" / "events_v3.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fetch_v3.FIELDS, lineterminator="\n")
        w.writeheader()
        for r in rows:                                                # entry 0.1% worse than the auction
            w.writerow({"ticker": r["ticker"], "R": r["R"], "vw": "", "hs_first": "0.0005", "status": "ok",
                        "first_bid": "", "first_ask": ""})
    # vw = o * 1.001: read the synthetic auction price back from v1's rows
    import gzip
    v1rows = {(r["ticker"], r["R"]): r for r in csv.DictReader(gzip.open(tmp_path / "raw" / "events_intraday.csv.gz", "rt"))}
    out = []
    for r in csv.DictReader(open(tmp_path / "raw" / "events_v3.csv")):
        o = float(v1rows[(r["ticker"], r["R"])]["o"])
        r.update(vw=o * 1.001, first_bid=o * 0.999, first_ask=o * 1.002)
        out.append(r)
    with open(tmp_path / "raw" / "events_v3.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fetch_v3.FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    rd.main()
    import run_d014_v2 as r2
    r2.main()
    r3.main()
    res = json.load(open(tmp_path / "results_v3.json"))
    lab = res["survivor_labels"]
    assert "v2 C7_washed_out|30" in lab and lab["v2 C7_washed_out|30"]["label"].startswith("executable")
    assert not any(k.startswith("v2 C7_minus") for k in lab)                 # differences are not trades
    d = res["descriptive_unconditional_by_entry_2bp"]["all|30 follow"]["train"]
    assert d["primary"] < d["auction"]                                        # the retail entry costs something
