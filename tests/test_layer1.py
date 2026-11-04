"""Tests for the D019 §3(b) Layer-1 capture (pipeline/layer1.py).

    python -m pytest tests/test_layer1.py -q

Synthetic data only: no network, and nothing under the real outcomes/ is read or written (every capture runs
against a temporary ROOT, with fake yfinance, SEC ticker and frames sources).
"""
import datetime
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pipeline"))
import layer1 as l1  # noqa: E402
from common import ET  # noqa: E402

UTC = datetime.timezone.utc


def ts(s, tz=ET):
    return datetime.datetime.fromisoformat(s).replace(tzinfo=tz)


def yrow(when, est=1.00, rep=1.10, sur=10.0, tz=ET):
    return (ts(when, tz), {"EPS Estimate": est, "Reported EPS": rep, "Surprise(%)": sur})


def frow(cik, start, end, val, accn="0000000000-26-000001"):
    return {"accn": accn, "cik": cik, "entityName": "X", "loc": "US-NY", "start": start, "end": end, "val": val}


def frames(rows, date="2026-10-20", fail=()):
    """Every frame an event on `date` needs, empty unless `rows` fills it: {(concept, frame): [row, ...]}."""
    cur, ago = l1.frames_for(date)
    out = {(c, f): {} for c in l1.CONCEPTS for f in cur + ago}
    for k, rs in rows.items():
        out[k] = {r["cik"]: r for r in rs}
    for k in fail:
        out[k] = None
    return out


class FakeSec:
    def __init__(self, ciks):
        self.ciks = ciks

    def cik(self, t):
        return self.ciks.get(t)


def ev(ticker, date, track="SH-M", void=None, session="BMO"):
    return {"track": track, "ticker": ticker, "date": date, "session": session, "void": void, "graded": True}


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setattr(l1, "ROOT", str(tmp_path))
    return tmp_path


def write_graded(root, evs, season="seasonA"):
    p = root / "outcomes" / "shadow" / season / "graded.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"season": season, "events": evs}))


def store_lines(root, season="seasonA"):
    p = root / "outcomes" / "layer1" / f"{season}.jsonl"
    return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


# ---------------------------------------------------------------- pure parts

def test_quarters_and_the_frames_a_print_needs():
    assert l1.quarters(datetime.date(2026, 4, 13), datetime.date(2026, 10, 20)) == ["CY2026Q2", "CY2026Q3", "CY2026Q4"]
    assert l1.quarters(datetime.date(2026, 11, 1), datetime.date(2027, 1, 5)) == ["CY2026Q4", "CY2027Q1"]
    cur, ago = l1.frames_for("2026-10-20")
    assert cur == ["CY2026Q2", "CY2026Q3", "CY2026Q4"]
    assert ago == ["CY2025Q2", "CY2025Q3", "CY2025Q4"]


def test_events_skip_void_and_unprinted_and_merge_tracks():
    graded = [ev("AAA", "2026-10-20"), ev("AAA", "2026-10-20", track="SH-W"), ev("BBB", "2026-10-20", void="print_early"),
              ev("CCC", "2026-11-04"), ev("DDD", "2026-10-21", track="SH-X")]
    out = l1.events(graded, datetime.date(2026, 11, 4))
    assert [(e["ticker"], e["tracks"]) for e in out] == [("AAA", ["SH-M", "SH-W"])]


def test_eps_matches_the_et_date_only():
    rows = [yrow("2026-10-28 16:05"), yrow("2026-07-29 16:05", 0.9, 1.0, 11.1)]
    got, when = l1.eps_of(rows, "2026-10-28")
    assert got == {"eps_estimate": 1.0, "eps_reported": 1.1, "eps_surprise_pct": 10.0}
    assert when.startswith("2026-10-28T16:05")
    got, why = l1.eps_of(rows, "2026-10-29")          # a day off is never taken
    assert got is None and "nearest 2026-10-28" in why
    # 01:00 UTC on 10-29 is 21:00 ET on 10-28: the ET date decides
    got, _ = l1.eps_of([yrow("2026-10-29 01:00", tz=UTC)], "2026-10-28")
    assert got is not None


def test_eps_waits_for_reported_and_keeps_a_missing_estimate_missing():
    got, why = l1.eps_of([yrow("2026-10-28 16:05", rep=float("nan"))], "2026-10-28")
    assert got is None and "no Reported EPS" in why
    got, _ = l1.eps_of([yrow("2026-10-28 16:05", est=float("nan"), sur=None)], "2026-10-28")
    assert got == {"eps_estimate": None, "eps_reported": 1.1, "eps_surprise_pct": None}


def test_revenue_is_the_reported_quarter_never_the_previous_one():
    q2 = frow(1, "2026-04-01", "2026-06-30", 500)
    q3 = frow(1, "2026-07-01", "2026-09-30", 600)
    ya = frow(1, "2025-07-01", "2025-09-30", 550)
    fr = frames({("Revenues", "CY2026Q2"): [q2], ("Revenues", "CY2026Q3"): [q3], ("Revenues", "CY2025Q3"): [ya]})
    got, why = l1.revenue_of(fr, 1, "2026-10-20")
    assert why is None
    assert got["revenue"][0] == 600 and got["revenue"][1]["end"] == "2026-09-30"
    assert got["revenue_year_ago"][0] == 550 and got["revenue_year_ago"][1]["frame"] == "CY2025Q3"
    # the 10-Q not filed yet: Q2 ends 112 days before the print, so nothing is taken
    fr = frames({("Revenues", "CY2026Q2"): [q2], ("Revenues", "CY2025Q3"): [ya]})
    got, why = l1.revenue_of(fr, 1, "2026-10-20")
    assert got == {} and why == l1.NO_QUARTER


def test_a_previous_quarter_can_never_fit_the_lag():
    # the shortest quarter is 12 weeks (ACI: 2026-06-20 -> 2026-09-12, 84 days); a print 7+ days after its end
    # still sits 91+ days after the previous quarter's end
    assert (datetime.date(2026, 9, 12) - datetime.date(2026, 6, 20)).days + 7 > l1.MAX_LAG
    q_prev = frow(1, "2026-03-29", "2026-06-20", 1)
    fr = frames({("Revenues", "CY2026Q2"): [q_prev]}, date="2026-09-19")
    assert l1.revenue_of(fr, 1, "2026-09-19") == ({}, l1.NO_QUARTER)      # the 12-week Q3 unfiled: nothing


def test_concept_order_decides():
    a = frow(1, "2026-07-01", "2026-09-30", 700)
    b = frow(1, "2026-07-01", "2026-09-30", 650)
    both = frames({("Revenues", "CY2026Q3"): [a],
                   ("RevenueFromContractWithCustomerExcludingAssessedTax", "CY2026Q3"): [b]})
    got, _ = l1.revenue_of(both, 1, "2026-10-20")
    assert got["revenue"][0] == 700 and got["revenue"][1]["concept"] == "Revenues"
    only_b = frames({("RevenueFromContractWithCustomerExcludingAssessedTax", "CY2026Q3"): [b]})
    got, why = l1.revenue_of(only_b, 1, "2026-10-20")
    assert got["revenue"][1]["concept"] == "RevenueFromContractWithCustomerExcludingAssessedTax"
    assert "no year-ago quarter" in why


def test_a_failed_frame_call_blocks_the_event():
    q3 = frow(1, "2026-07-01", "2026-09-30", 600)
    fr = frames({("RevenueFromContractWithCustomerExcludingAssessedTax", "CY2026Q3"): [q3]},
                fail=[("Revenues", "CY2026Q3")])
    got, why = l1.revenue_of(fr, 1, "2026-10-20")
    assert got == {} and "failed" in why


def test_a_stored_actual_pins_the_year_ago_concept_and_period():
    stored = {"concept": "RevenueFromContractWithCustomerExcludingAssessedTax", "frame": "CY2026Q3",
              "start": "2026-07-01", "end": "2026-09-30", "accn": "x", "cik": 1, "unit": "USD"}
    fr = frames({("Revenues", "CY2025Q3"): [frow(1, "2025-07-01", "2025-09-30", 1)],
                 ("RevenueFromContractWithCustomerExcludingAssessedTax", "CY2025Q3"):
                     [frow(1, "2025-07-01", "2025-09-30", 2)]})
    got, why = l1.revenue_of(fr, 1, "2026-10-20", stored)
    assert why is None and "revenue" not in got
    assert got["revenue_year_ago"][0] == 2


# ---------------------------------------------------------------- the run, against a temporary ROOT

def run(root, today, yf, fr, ciks=None):
    calls = []

    def yf_get(t):
        calls.append(t)
        return yf(t)

    tab = l1.capture("seasonA", sec=FakeSec(ciks or {"AAA": 1}), yf_get=yf_get, frames_get=lambda sec, keys: fr,
                     today=today, pause=0)
    return tab, calls


def test_capture_is_write_once_and_retries_what_is_missing(root):
    write_graded(root, [ev("AAA", "2026-10-20"), ev("AAA", "2026-10-20", track="SH-W"),
                        ev("BBB", "2026-10-21", void="print_contradicted"), ev("CCC", "2026-11-10")])
    q3 = frow(1, "2026-07-01", "2026-09-30", 600)
    ya = frow(1, "2025-07-01", "2025-09-30", 550)
    tab, calls = run(root, datetime.date(2026, 10, 25), lambda t: [yrow("2026-10-20 07:00")],
                     frames({("Revenues", "CY2026Q3"): [q3]}))
    assert calls == ["AAA"]
    f = tab["events"][0]["fields"]
    assert f["eps_reported"]["value"] == 1.1 and f["eps_reported"]["tier"].startswith("aggregator")
    assert f["revenue"]["value"] == 600 and f["revenue"]["tier"].startswith("filed")
    assert f["revenue_year_ago"]["value"] is None and "no year-ago" in f["revenue_year_ago"]["missing"]
    assert len(store_lines(root)) == 4
    # Yahoo revises the figures and the year-ago quarter appears: EPS is not fetched again, only the gap is filled
    tab, calls = run(root, datetime.date(2026, 11, 1), lambda t: [yrow("2026-10-20 07:00", 9, 9, 9)],
                     frames({("Revenues", "CY2026Q3"): [frow(1, "2026-07-01", "2026-09-30", 999)],
                             ("Revenues", "CY2025Q3"): [ya]}))
    assert calls == []
    lines = store_lines(root)
    assert len(lines) == 5 and lines[-1]["field"] == "revenue_year_ago" and lines[-1]["value"] == 550
    f = tab["events"][0]["fields"]
    assert f["eps_reported"]["value"] == 1.1 and f["revenue"]["value"] == 600
    # only outcomes/layer1/ is written
    written = {os.path.relpath(os.path.join(dp, n), root).replace(os.sep, "/")
               for dp, _, ns in os.walk(root) for n in ns}
    assert written == {"outcomes/shadow/seasonA/graded.json", "outcomes/layer1/seasonA.jsonl",
                       "outcomes/layer1/seasonA.json"}


def test_a_closed_window_stops_retrying_and_keeps_the_last_reason(root):
    write_graded(root, [ev("AAA", "2026-10-20")])
    run(root, datetime.date(2026, 10, 25), lambda t: [yrow("2026-10-19 16:05")], frames({}))
    tab, calls = run(root, datetime.date(2026, 10, 20) + datetime.timedelta(days=l1.EPS_WINDOW + 1),
                     lambda t: [yrow("2026-10-20 07:00")], frames({}))
    assert calls == []
    m = tab["events"][0]["fields"]["eps_reported"]
    assert m["value"] is None and m["final"] is True and "nearest 2026-10-19" in m["missing"]
    assert tab["events"][0]["fields"]["revenue"]["final"] is False


def test_yfinance_failures_end_the_eps_fetch(root):
    write_graded(root, [ev(f"T{i:02d}", "2026-10-20") for i in range(l1.YF_STOP + 5)])

    def boom(t):
        raise RuntimeError("rate limited")

    tab, calls = run(root, datetime.date(2026, 10, 25), boom, frames({}), ciks={})
    assert len(calls) == l1.YF_STOP
    reasons = {e["fields"]["eps_reported"]["missing"].split(":")[0] for e in tab["events"]}
    assert reasons == {"yfinance failed", f"yfinance stopped answering ({l1.YF_STOP} failed calls in a row)"}
    assert store_lines(root) == []


def test_no_cik_is_disclosed_even_beside_an_eps_note(root):
    write_graded(root, [ev("ZZZ", "2026-10-20")])
    tab, _ = run(root, datetime.date(2026, 10, 25), lambda t: [], frames({}), ciks={})
    f = tab["events"][0]["fields"]
    assert "no Yahoo row" in f["eps_reported"]["missing"]
    assert f["revenue"]["missing"] == f["revenue_year_ago"]["missing"] == "no SEC CIK for the ticker"


def test_no_commit_inside_the_s2_window():
    assert l1.busy(datetime.datetime(2026, 11, 4, 15, 0, tzinfo=ET)) is True
    assert l1.busy(datetime.datetime(2026, 11, 4, 11, 0, tzinfo=ET)) is False
    assert l1.busy(datetime.datetime(2026, 11, 7, 15, 0, tzinfo=ET)) is False      # Saturday
    assert l1.busy(datetime.datetime(2026, 11, 27, 12, 0, tzinfo=ET)) is True      # early close at 13:00
