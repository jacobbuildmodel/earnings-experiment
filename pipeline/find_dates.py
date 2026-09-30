"""Find the COMPANY source for an event's date and session (D003 §6), by code.

    python pipeline/find_dates.py probe <TICKER> [<TICKER> ...]    # print what the company says; writes nothing
    python pipeline/find_dates.py apply <season> [--commit]         # every PENDING event: confirm where it is clear

Why: the pilot had 12 candidates and the AI step confirmed them one by one. A Season A preview on
2026-09-28 found ~250 candidates. The AI step cannot read ~250 IR sites a night, so unconfirmed names
would be lost to power, the binding constraint (CHARTER §6.1). Code reads the common IR platforms and
confirms the clear cases; the AI step handles what code leaves PENDING.

What counts is unchanged (D003 §6): a company page stating the report date and either the session or a
release time; with only a call time, a call before 09:30 ET -> BMO, at or after 16:00 ET -> AMC, flag
`session_from_call_time`; a call during the session gives no session. The quote is stored verbatim.

Code confirms ONLY when all of these hold, and otherwise leaves the event PENDING with a recheck note:
  - exactly one results date inside the season window is stated on the company page
  - its session comes from explicit wording in the same sentence, or from a call time on that date
  - the page was published before now, and at least one second source (yfinance timestamp or Nasdaq
    session) agrees with date AND session right now
The gate re-checks both second sources inside the S2 window, so a wrong parse cannot pass the gate:
it becomes `unconfirmed`, never a mis-timed trade.
"""
import datetime
import html
import json
import os
import re
import sys
import time
from urllib.parse import urljoin, urlparse

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ET, ROOT, now_et, rule_for, write_json  # noqa: E402

VERSION = "find_dates v1 (2026-09-28)"
BROWSER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/126.0 Safari/537.36", "Accept": "*/*"}
Q4_PRESS = ("/feed/PressRelease.svc/GetPressReleaseList?LanguageId=1&bodyType=0&pressReleaseDateFilter=3"
            "&pageSize=15&pageNumber=0&tagList=&includeTags=true&year=-1&excludeSelection=1")
RSS_PATHS = ["/news-events/press-releases/rss", "/news-releases/rss", "/rss/news-releases.xml",
             "/press-releases/rss", "/rss/pressrelease.aspx", "/news/rss"]
TITLE = re.compile(r"(announce|report|release|host|webcast|conference call|to discuss|date)", re.I)
TITLE_RESULTS = re.compile(r"(result|earnings|quarter)", re.I)
MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}
# "." or DOT: sentences() swaps an abbreviation's period for DOT while it splits
DATE_RE = re.compile(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*[.․]?\s+(\d{1,2})(?!\d)"
                     r"(?:st|nd|rd|th)?(?:,?\s+(20\d\d))?", re.I)
US = r"(u[.․]s[.․] )?"
BMO_RE = re.compile(rf"before (the )?{US}(stock )?market(s)? open|prior to (the )?{US}(stock )?market(s)?"
                    r" open|before the opening of|before the (start|beginning|open) of (the )?(regular )?trading|"
                    r"pre-market|premarket|before the bell|prior to the opening|before (the )?(nyse|nasdaq) open", re.I)
AMC_RE = re.compile(rf"after (the )?{US}(stock )?market(s)? (close|closes)|after (the )?close|following the close|"
                    r"after the closing|after market hours|after (the )?(nyse|nasdaq)|after-market|after market close|"
                    r"after the bell|post-market|after the end of (the )?(regular )?trading", re.I)
TIME_RE = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*(a[.․]?m[.․]?|p[.․]?m[.․]?)\s*\(?\s*"
                     r"(eastern|central|mountain|pacific|e[sd]?t|c[sd]?t|m[sd]?t|p[sd]?t)\b", re.I)
TZ_SHIFT = {"e": 0, "c": 1, "m": 2, "p": 3}  # hours to add to reach Eastern


def get(url, timeout=20):
    try:
        r = requests.get(url, headers=BROWSER, timeout=timeout, allow_redirects=True)
        return r if r.status_code == 200 and r.content else None
    except requests.RequestException:
        return None


def text_of(body):
    from bs4 import BeautifulSoup
    import warnings
    warnings.filterwarnings("ignore")
    soup = BeautifulSoup(body, "lxml")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    return re.sub(r"\s+", " ", html.unescape(soup.get_text(" "))).strip()


def hosts_for(ticker):
    import yfinance as yf
    try:
        info = yf.Ticker(ticker).info or {}
    except Exception:
        info = {}
    out = []
    for key in ("irWebsite", "website"):
        u = info.get(key)
        if not u or "corporate-ir.net" in u or "shareholder.com" in u:
            continue
        host = urlparse(u if "//" in u else "https://" + u).netloc.lower()
        dom = host[4:] if host.startswith("www.") else host
        for h in (host, f"ir.{dom}", f"investors.{dom}", f"investor.{dom}", f"www.{dom}"):
            if h not in out:
                out.append(h)
    return out


def items_q4(host):
    r = get(f"https://{host}{Q4_PRESS}")
    if not r:
        return []
    try:
        rows = r.json().get("GetPressReleaseListResult") or []
    except ValueError:
        return []
    out = []
    for it in rows:
        try:
            pub = datetime.datetime.strptime(it["PressReleaseDate"], "%m/%d/%Y %H:%M:%S").replace(tzinfo=ET)
        except (KeyError, ValueError):
            continue
        link = it.get("LinkToUrl") or it.get("LinkToDetailPage") or ""
        out.append({"title": it.get("Headline", ""), "published": pub, "url": urljoin(f"https://{host}/", link),
                    "feed": f"https://{host}{Q4_PRESS.split('?')[0]} (Q4 press-release feed)"})
    return out


def items_rss(host):
    from email.utils import parsedate_to_datetime
    for path in RSS_PATHS:
        r = get(f"https://{host}{path}")
        if not r or b"<rss" not in r.content[:2000] and b"<feed" not in r.content[:2000]:
            continue
        out = []
        for m in re.finditer(rb"<item>(.*?)</item>", r.content, re.S):
            block = m.group(1).decode("utf-8", "replace")
            title = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", block, re.S)
            link = re.search(r"<link>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>", block, re.S)
            pub = re.search(r"<pubDate>(.*?)</pubDate>", block, re.S)
            try:
                when = parsedate_to_datetime(pub.group(1).strip()).astimezone(ET) if pub else None
            except (TypeError, ValueError):
                when = None
            if title and link and when:
                out.append({"title": html.unescape(title.group(1).strip()), "published": when,
                            "url": link.group(1).strip(), "feed": f"https://{host}{path} (RSS)"})
        if out:
            return out
    return []


def feed_items(ticker):
    seen = []
    for host in hosts_for(ticker):
        items = items_q4(host) or items_rss(host)
        if items:
            return items, host
        seen.append(host)
        time.sleep(0.3)
    return [], None


def to_et(hour, minute, ampm, zone):
    h = hour % 12 + (12 if ampm.lower().startswith("p") else 0)
    return datetime.time((h + TZ_SHIFT[zone[0].lower()]) % 24, minute)


DOT = "․"  # one-dot leader: holds an abbreviation's period while splitting; restored in stored quotes
ABBREV = re.compile(r"\b(a\.m|p\.m|inc|corp|co|ltd|no|st|u\.s|jan|feb|mar|apr|aug|sep|sept|oct|nov|dec)\.", re.I)


def sentences(text):
    """Sentences, without splitting at "p.m. Eastern", "Inc. (", "Sep. 30" and the like."""
    text = ABBREV.sub(lambda m: m.group(0).replace(".", DOT), text)
    return re.split(r"(?<=[.;!?])\s+(?=[A-Z])", text)


def parse_page(text, window, published):
    """Every results-date statement on the page: (date, session, from_call_time, sentence)."""
    lo, hi = window
    found = []
    for s in sentences(text):
        low = s.lower()
        if not re.search(r"result|earnings|report|release|call|webcast", low):
            continue
        dm = list(DATE_RE.finditer(s))
        for i, m in enumerate(dm):
            # the clause that belongs to this date: from the previous date to the next one, so "after
            # the close on Oct 22 and a call on Oct 23 at 8:30 a.m." gives each date its own wording
            clause = s[dm[i - 1].end() if i else 0: dm[i + 1].start() if i + 1 < len(dm) else len(s)]
            mon = MONTHS[m.group(1).lower()[:3]]
            year = int(m.group(3)) if m.group(3) else published.year + (1 if mon < published.month - 6 else 0)
            try:
                d = datetime.date(year, mon, int(m.group(2)))
            except ValueError:
                continue
            if not lo <= d <= hi:
                continue
            before = s[max(0, m.start() - 40): m.start()].lower()
            if re.search(r"(ended|ending|end of|as of|through|until|replay|period)\W+(\w+\W+){0,2}$", before):
                continue  # a quarter end, a replay window - not the report date
            hedged = bool(re.search(r"on or about|tentative|subject to change|expected to be on|around\W*$", before + " "))
            session, from_call = None, False
            bmo, amc = BMO_RE.search(clause), AMC_RE.search(clause)
            if bmo and not amc:
                session = "BMO"
            elif amc and not bmo:
                session = "AMC"
            elif not bmo and not amc:
                times = [to_et(int(t.group(1)), int(t.group(2) or 0), t.group(3), t.group(4)) for t in TIME_RE.finditer(clause)]
                if len(set(times)) == 1:
                    t = times[0]
                    session = "BMO" if t < datetime.time(9, 30) else "AMC" if t >= datetime.time(16, 0) else "INTRADAY"
                    from_call = bool(re.search(r"call|webcast|broadcast", clause, re.I))
            # verbatim: the page's own words around the date, abbreviation periods restored
            quote = s[max(0, m.start() - 350): m.end() + 250].replace(DOT, ".").strip()
            found.append({"date": d.isoformat(), "session": session, "session_from_call_time": from_call,
                          "hedged": hedged, "sentence": quote})
    return found


def probe(ticker, window, since_days=75):
    """What the company's own feed says about the next results date. Returns a dict; writes nothing."""
    items, host = feed_items(ticker)
    res = {"ticker": ticker, "host": host, "checked_et": now_et().isoformat(), "version": VERSION}
    if not items:
        res["outcome"] = "no_feed"
        return res
    cutoff = now_et() - datetime.timedelta(days=since_days)
    hits = [i for i in items if i["published"] >= cutoff and TITLE.search(i["title"]) and TITLE_RESULTS.search(i["title"])]
    res["feed"] = items[0]["feed"]
    res["newest_item"] = {"title": items[0]["title"][:150], "published": items[0]["published"].isoformat()}
    statements = []
    for it in hits[:4]:
        r = get(it["url"])
        if not r:
            continue
        for st in parse_page(text_of(r.content), window, it["published"]):
            st.update(url=it["url"], title=it["title"], published_et=it["published"].isoformat(timespec="minutes"))
            statements.append(st)
        time.sleep(0.3)
    res["statements"] = statements
    # Explicit release wording outranks a call time; a call time is used only when no page gives wording.
    explicit = [s for s in statements if s["session"] in ("BMO", "AMC") and not s["session_from_call_time"]]
    by_call = [s for s in statements if s["session"] in ("BMO", "AMC", "INTRADAY") and s["session_from_call_time"]]
    use = explicit or by_call
    dates = sorted({s["date"] for s in use})
    sessions = sorted({s["session"] for s in use})
    all_dates = sorted({s["date"] for s in statements})
    if not statements:
        res["outcome"] = "no_date_announced"
    elif any(s["hedged"] for s in statements):
        res["outcome"] = f"hedged_date {all_dates}"
    elif len(all_dates) > 1:
        # e.g. results on Oct 22 (no session given) and a call on Oct 23 at 8:30 a.m.: taking the call's
        # date would confirm the wrong day, and yfinance often stamps the call - leave it to the AI step
        res["outcome"] = f"ambiguous_dates {all_dates}"
    elif not use:
        res["outcome"] = f"no_session_stated {sorted({s['date'] for s in statements})}"
    elif len(dates) > 1:
        res["outcome"] = f"ambiguous_dates {dates}"
    elif sessions not in (["AMC"], ["BMO"]):
        res["outcome"] = f"no_clear_session {sessions}"
    else:
        res.update(outcome="found", date=dates[0], session=sessions[0], source=use[0])
    return res


def second_source_agrees(ticker, date, session):
    from s2_gate import second_sources
    seconds = second_sources(ticker, datetime.date.fromisoformat(date))
    agree = [s for s in seconds if s.get("session") == session]
    disagree = [s for s in seconds if s.get("session") and s.get("session") != session]
    return bool(agree) and not disagree, seconds


def apply(season, do_commit=False):
    from sessions import shift
    sp = os.path.join(ROOT, "universe", season, "event_status.json")
    st = json.load(open(sp, encoding="utf-8"))
    rule = rule_for("D003_universe_screen", season)
    window = tuple(datetime.date.fromisoformat(x) for x in rule["seasons"][season]["window"])
    snap = rule["s2"]["snapshot_session"]
    today = now_et().date()
    confirmed, paths = [], [sp]
    started = time.time()

    def earliest(item):  # most urgent first: the earliest calendar date any source gives
        ev = item[1]
        dates = ev.get("calendar_dates") or re.findall(r"20\d\d-\d\d-\d\d", ev.get("note", "")) or ["9999"]
        return (min(dates), item[0])

    pending = sorted(((k, e) for k, e in st["events"].items() if e.get("status") == "PENDING"), key=earliest)
    for n, (key, ev) in enumerate(pending):
        if time.time() - started > BUDGET_SECONDS:
            print(f"budget of {BUDGET_SECONDS // 60} min used - {len(pending) - n} names left for the next run / AI step")
            break
        try:
            confirm_one(season, key, ev, window, snap, today, confirmed, paths)
        except Exception as exc:  # one bad page must not cost the rest
            ev.setdefault("rechecks", []).append(f"{now_et().isoformat()}: {VERSION} - error {type(exc).__name__}: {exc}")
        if do_commit and (n + 1) % 20 == 0:
            st["updated_et"] = now_et().isoformat()
            write_json(sp, st)
            from due import commit
            commit(paths, f"{season}: company dates found by code (batch) - {confirmed}")
        time.sleep(0.5)
    st["updated_et"] = now_et().isoformat()
    write_json(sp, st)
    print(f"{season}: confirmed by code {confirmed}")
    if do_commit:
        from due import commit
        commit(paths, f"{season}: company dates found by code - {len(confirmed)} confirmed {confirmed}")
    return confirmed


BUDGET_SECONDS = 75 * 60


def confirm_one(season, key, ev, window, snap, today, confirmed, paths):
    from sessions import shift
    if ev.get("status") == "PENDING":
        res = probe(key, window)
        note = f"{res['checked_et']}: {VERSION} - {res['outcome']}"
        if res.get("newest_item"):
            note += f"; feed {res['feed']}, newest item {res['newest_item']['published'][:16]} '{res['newest_item']['title'][:80]}'"
        if res["outcome"] == "found":
            date, session = res["date"], res["session"]
            try:
                snap_session = shift(datetime.date.fromisoformat(date), snap[session])
                shift(datetime.date.fromisoformat(date), 0)  # the report date must itself be a session
            except ValueError as exc:
                ev.setdefault("rechecks", []).append(f"{res['checked_et']}: {VERSION} - found {date} {session}, not a session: {exc}")
                return
            ok, seconds = second_source_agrees(key, date, session)
            if snap_session <= today:
                note += f"; found {date} {session} but its snapshot session {snap_session} has passed - left for the AI step"
            elif not ok:
                note += f"; found {date} {session} but no second source agrees yet ({seconds}) - left PENDING"
            else:
                src = res["source"]
                edir = os.path.join(ROOT, "events", season, f"{key}_{date}")
                cpath = os.path.join(edir, "confirm.json")
                if not os.path.exists(cpath):
                    write_json(cpath, {
                        "session": session, "session_from_call_time": src["session_from_call_time"],
                        "company_source": {"url": src["url"], "published_et": src["published_et"],
                                           "quote": src["sentence"], "title": src["title"],
                                           "retrieved_et": res["checked_et"],
                                           "how": f"{VERSION}: company feed {res['feed']}; the quote is the sentence on the "
                                                  "linked page that states the date and session"},
                        "second_sources_at_confirm": seconds})
                    paths.append(cpath)
                ev.update(status="CONFIRMED", calendar_date=date, session=session,
                          snapshot_session=snap_session.isoformat(),
                          entry=f"{shift(datetime.date.fromisoformat(date), snap[session] + 1)} open",
                          flags=sorted(set(ev.get("flags", []) + (["session_from_call_time"] if src["session_from_call_time"] else [])
                                           + ["confirmed_by_code"])))
                note += f"; CONFIRMED {date} {session}, snapshot {snap_session}"
                confirmed.append(key)
        ev.setdefault("rechecks", []).append(note)
        print(note)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "probe":
        lo = now_et().date()
        for t in a[1:]:
            print(json.dumps(probe(t.upper(), (lo, lo + datetime.timedelta(days=90))), indent=1, default=str))
    elif a and a[0] == "apply":
        apply(a[1], "--commit" in a)
    else:
        raise SystemExit(__doc__)
