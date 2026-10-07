"""find_dates v3 (2026-10-07): the Nasdaq copy of a company's wire release, used when the company's own feed
cannot be read. Only a page with a wire dateline counts, and the header (with its own publish time) is cut."""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import find_dates as fd  # noqa: E402
from common import ET  # noqa: E402

WIN = (datetime.date(2026, 10, 12), datetime.date(2026, 11, 20))
UBER = ("Uber Announces Date of Third Quarter 2026 Results Conference Call | Nasdaq Skip to main content Uber "
        "Announces Date of Third Quarter 2026 Results Conference Call Published Oct 5, 2026 4:30pm EDT linkedin "
        "facebook SAN FRANCISCO --(BUSINESS WIRE)-- Uber Technologies, Inc. (NYSE: UBER ) will hold its quarterly "
        "conference call to discuss its third quarter 2026 financial results on Wednesday, November 4th at 5:00 "
        "a.m. Pacific Time ( 8:00 a.m. Eastern Time ). A replay will be accessible for at least 90 days.")
ARTICLE = ("Uber earnings preview | Nasdaq Published Oct 6, 2026 9:12am EDT By A Writer, Zacks - Uber is expected "
           "to report on November 4, 2026 before the market opens.")


def test_wire_release_body_and_minute():
    body, pub = fd.nasdaq_body(UBER)
    assert pub == datetime.datetime(2026, 10, 5, 16, 30, tzinfo=ET)
    assert "4:30pm" not in body  # the header's own time must not read as a second call time
    st = fd.parse_page(body, WIN, pub)
    assert [(s["date"], s["session"]) for s in st] == [("2026-11-04", "BMO")]


def test_article_without_wire_dateline_is_not_a_company_source():
    assert fd.nasdaq_body(ARTICLE) == (None, None)


def test_no_published_line():
    assert fd.nasdaq_body("SAN FRANCISCO --(BUSINESS WIRE)-- Uber will report on November 4.") == (None, None)
