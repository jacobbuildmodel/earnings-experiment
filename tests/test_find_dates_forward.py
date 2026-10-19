"""find_dates (2026-10-19): only dates from today on can be the coming report. With the whole season window, a
release's own dateline counted as a second date, so GLXY, CORZ and EEFT stayed "ambiguous" while both second sources
agreed (recall audit, JOURNAL 2026-10-19)."""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import find_dates as fd  # noqa: E402
from common import ET  # noqa: E402

GLXY = ("linkedin facebook x email reddit NEW YORK , Oct. 13, 2026 /PRNewswire/ -- Galaxy Digital Inc. (Nasdaq: GLXY) "
        "(\"Galaxy\" or the \"Company\") is pleased to announce that it will report third quarter 2026 financial results "
        "before the opening of Nasdaq on Tuesday, October 27, 2026.")


def test_dateline_is_a_date_in_the_season_window():
    pub = datetime.datetime(2026, 10, 13, 16, 15, tzinfo=ET)
    season = fd.parse_page(GLXY, (datetime.date(2026, 10, 12), datetime.date(2026, 11, 20)), pub)
    forward = fd.parse_page(GLXY, (datetime.date(2026, 10, 19), datetime.date(2026, 11, 20)), pub)
    assert sorted({s["date"] for s in season}) == ["2026-10-13", "2026-10-27"]       # the defect: two dates
    assert [(s["date"], s["session"]) for s in forward] == [("2026-10-27", "BMO")]  # the fix: one, with its session


def test_confirm_one_probes_from_today(tmp_path, monkeypatch):
    windows = []

    def probe(t, window):
        windows.append(window)
        return {"checked_et": "t", "outcome": "found", "date": "2026-10-27", "session": "BMO", "feed": "f",
                "source": {"url": "u", "published_et": "p", "sentence": "s", "title": "t",
                           "session_from_call_time": False}}
    monkeypatch.setattr(fd, "ROOT", str(tmp_path))
    monkeypatch.setattr(fd, "probe", probe)
    monkeypatch.setattr(fd, "second_source_agrees", lambda *a: (True, []))
    monkeypatch.setattr(fd, "now_et", lambda: datetime.datetime(2026, 10, 19, 9, 30, tzinfo=ET))
    ev = {"status": "PENDING", "calendar_dates": ["2026-10-20"]}
    confirmed = []
    fd.confirm_one("seasonA", "GLXY", ev, (datetime.date(2026, 10, 12), datetime.date(2026, 11, 20)),
                   {"BMO": -2, "AMC": -1}, datetime.date(2026, 10, 19), confirmed, [])
    assert windows == [(datetime.date(2026, 10, 19), datetime.date(2026, 11, 20))]
    assert confirmed == ["GLXY"] and ev["status"] == "CONFIRMED" and ev["snapshot_session"] == "2026-10-23"
    assert json.loads((tmp_path / "events" / "seasonA" / "GLXY_2026-10-27" / "confirm.json").read_text())["session"] == "BMO"


MRNA_PAGE = ("Moderna to Report Third Quarter 2026 Financial Results on Friday, November 6, 2026 | Nasdaq Skip to main content "
             "Moderna to Report Third Quarter 2026 Financial Results on Friday, November 6, 2026 Published Oct 13, 2026 7:00am EDT "
             "linkedin facebook x email reddit CAMBRIDGE, MA / ACCESS Newswire / October 13, 2026 / Moderna, Inc. (NASDAQ:MRNA), "
             "today announced that it will host a live conference call and webcast at 8:00 a.m. ET on Friday, November 6, 2026 to "
             "report its third quarter 2026 financial results, and provide a corporate update.")


def test_access_newswire_dateline_is_a_release():
    body, pub = fd.nasdaq_body(MRNA_PAGE)
    assert body is not None and pub == datetime.datetime(2026, 10, 13, 7, 0, tzinfo=ET)
    st = fd.parse_page(body, (datetime.date(2026, 10, 19), datetime.date(2026, 11, 20)), pub)
    assert [(s["date"], s["session"], s["session_from_call_time"]) for s in st] == [("2026-11-06", "BMO", True)]


def test_an_article_without_a_dateline_is_still_skipped():
    article = MRNA_PAGE.replace("/ ACCESS Newswire / October 13, 2026 /", "- Moderna said on")
    assert fd.nasdaq_body(article) == (None, None)
