"""D003 v4 addendum 1 (2026-10-19): Yahoo's after-close placeholder for an upcoming date carries the EDT offset, so it
reads 15:00 on a standard-time date. That exact signature is no vote for AMC and still disagrees with BMO; every other
mid-session stamp is INTRADAY and disagrees, as before."""
import datetime
import os
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import s2_gate  # noqa: E402
import find_dates as fd  # noqa: E402

NY = ZoneInfo("America/New_York")
ts = lambda *a: datetime.datetime(*a, tzinfo=NY)  # noqa: E731
YF_PLACEHOLDER = {"source": "yfinance get_earnings_dates", "timestamp": "2026-11-03T15:00:00-05:00", "session": None,
                  "artifact": "amc_placeholder"}
NASDAQ_AMC = {"source": "nasdaq calendar", "time": "time-after-hours", "session": "AMC"}
NASDAQ_BMO = {"source": "nasdaq calendar", "time": "time-pre-market", "session": "BMO"}


def test_session_from_ts():
    assert s2_gate.session_from_ts(ts(2026, 11, 3, 15, 0)) is None               # AMD's placeholder (EST date)
    assert s2_gate.amc_placeholder(ts(2026, 11, 3, 15, 0))
    assert s2_gate.session_from_ts(ts(2025, 11, 4, 16, 0)) == "AMC"              # AMD's real 2025 print
    assert s2_gate.session_from_ts(ts(2026, 10, 20, 15, 0)) == "INTRADAY"        # 15:00 on an EDT date: not the artifact
    assert s2_gate.session_from_ts(ts(2026, 11, 3, 12, 0)) == "INTRADAY"         # a real midday stamp still disagrees
    assert s2_gate.session_from_ts(ts(2026, 10, 20, 9, 29)) == "BMO"
    assert s2_gate.session_from_ts(ts(2026, 10, 20, 16, 0)) == "AMC"


def test_votes_shared_by_gate_and_find_dates():
    assert s2_gate.votes([YF_PLACEHOLDER, NASDAQ_AMC], "AMC") == ([NASDAQ_AMC], [])     # Nasdaq agrees, no veto
    assert s2_gate.votes([YF_PLACEHOLDER], "AMC") == ([], [])                           # the placeholder never agrees
    assert s2_gate.votes([YF_PLACEHOLDER, NASDAQ_BMO], "BMO") == ([NASDAQ_BMO], [YF_PLACEHOLDER])  # still vetoes BMO
    intraday = {"source": "yfinance get_earnings_dates", "timestamp": "2026-11-03T12:00:00-05:00", "session": "INTRADAY"}
    assert s2_gate.votes([intraday, NASDAQ_AMC], "AMC") == ([NASDAQ_AMC], [intraday])  # other intraday stamps veto


def test_find_dates_uses_the_shared_votes(monkeypatch):
    monkeypatch.setattr(s2_gate, "second_sources", lambda t, d: [YF_PLACEHOLDER, NASDAQ_AMC])
    assert fd.second_source_agrees("AMD", "2026-11-03", "AMC")[0]
    assert not fd.second_source_agrees("AMD", "2026-11-03", "BMO")[0]


def test_the_gate_uses_the_shared_votes():
    src = open(s2_gate.__file__, encoding="utf-8").read()
    assert "agree, disagree = votes(seconds, session)" in src
