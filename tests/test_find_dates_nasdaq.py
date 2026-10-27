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


DBX = ("Dropbox to Announce Third Quarter 2026 Earnings Results | Nasdaq Published Oct 15, 2026 4:04pm EDT linkedin "
       "SAN FRANCISCO --(BUSINESS WIRE)-- Dropbox, Inc. (NASDAQ: DBX) announced today that it will report financial "
       "results for the third quarter of 2026 after the market closes on Thursday, November 5, 2026.")


class _Page:
    def __init__(self, text):
        self.content = text.encode()


def _items(nasdaq):
    pub = datetime.datetime(2026, 10, 15, tzinfo=ET)
    return [{"title": "Dropbox to Announce Third Quarter 2026 Earnings Results", "published": pub,
             "url": "https://www.nasdaq.com/x" if nasdaq else "https://dropbox.gcs-web.com/x",
             "feed": "nasdaq feed" if nasdaq else "company rss", **({"nasdaq": True} if nasdaq else {})}]


def test_unreadable_company_page_falls_back_to_the_nasdaq_copy(monkeypatch):
    # 2026-10-26, DBX: the company's feed lists the release, its page refuses the fetch
    monkeypatch.setattr(fd, "feed_items", lambda t: (_items(False), "investors.dropbox.com"))
    monkeypatch.setattr(fd, "items_nasdaq", lambda t: _items(True))
    monkeypatch.setattr(fd, "get", lambda url, timeout=20: _Page(DBX) if "nasdaq" in url else None)
    monkeypatch.setattr(fd, "now_et", lambda: datetime.datetime(2026, 10, 26, 9, 0, tzinfo=ET))
    monkeypatch.setattr(fd.time, "sleep", lambda s: None)
    res = fd.probe("DBX", WIN)
    assert (res["outcome"], res["date"], res["session"]) == ("found", "2026-11-05", "AMC")
    assert res["host"] == "www.nasdaq.com" and "company rss" in res["fallback"]


def test_financial_markets_wording_and_a_replay_window():
    # 2026-10-26: IONQ's release (Business Wire, Oct 22) and ONC's (Oct 22), quoted from the pages
    ionq = ("IonQ today announced that the company will release its financial results for the quarter ended "
            "September 30, 2026, on Thursday, Nov. 5, 2026, after the financial markets close. A replay of the "
            "conference call will be available approximately three hours after its conclusion at 1-855-669-9658 "
            "(domestic) and will be available until 11:59 PM Eastern Time, November 19, 2026.")
    onc = ("BeOne Medicines will report its third quarter 2026 financial results on Thursday, November 5, 2026, "
           "before the financial markets open.")
    pub = datetime.datetime(2026, 10, 22, 8, 0, tzinfo=ET)
    assert [(s["date"], s["session"]) for s in fd.parse_page(ionq, WIN, pub)] == [("2026-11-05", "AMC")]
    assert [(s["date"], s["session"]) for s in fd.parse_page(onc, WIN, pub)] == [("2026-11-05", "BMO")]
    carg = ("CarGurus will report financial results after the market close on Thursday, November 5, 2026. An audio "
            "replay of the call will also be available beginning at approximately 8:00 p.m. Eastern Time on "
            "November 5, 2026, until 11:59 p.m. Eastern Time on November 19, 2026.")
    assert [(s["date"], s["session"]) for s in fd.parse_page(carg, WIN, pub)] == [("2026-11-05", "AMC")]


def test_readable_company_page_never_uses_the_fallback(monkeypatch):
    monkeypatch.setattr(fd, "feed_items", lambda t: (_items(False), "investors.dropbox.com"))
    monkeypatch.setattr(fd, "items_nasdaq", lambda t: (_ for _ in ()).throw(AssertionError("no fallback")))
    monkeypatch.setattr(fd, "get", lambda url, timeout=20: _Page(DBX.split("linkedin ")[1]))
    monkeypatch.setattr(fd, "now_et", lambda: datetime.datetime(2026, 10, 26, 9, 0, tzinfo=ET))
    monkeypatch.setattr(fd.time, "sleep", lambda s: None)
    res = fd.probe("DBX", WIN)
    assert (res["outcome"], res["session"]) == ("found", "AMC") and "fallback" not in res
