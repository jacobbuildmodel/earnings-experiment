"""D004 v4 stage 1: the T2 dossier - every input T2 may read, gathered BY CODE at the snapshot.

    python pipeline/dossier.py <season> <TICKER> <YYYY-MM-DD>     # writes events/<season>/<T>_<D>/dossier.json

Why: the agentic T2 (D004 v1-v3) researched on its own for ~50 turns, which a subscription allowance can
pay for once or twice per 5 hours (load tests 2026-10-02/03). Here code fetches the inputs once, stamps
each with its publication time, drops anything not published before the gate's captured_et, and the file
is frozen with the event BEFORE any model reads it. T2 then gets one call and no tools, so its
information set is exactly this file plus its own pre-cutoff training - no live web page, no after-hours
news, and the record says precisely what it saw.

Items (each: id, kind, source, published, text or data):
  meta / gate / factors / base rates    - the frozen gate.json, factors.json and registry base-rate card
  release   - the company's most recent earnings release (EX-99.1 of the latest Item 2.02 8-K)
  periodic  - MD&A of the latest 10-Q / 10-K (or its first part when the section is not found)
  8k        - every other 8-K of the last 90 days: items and opening text
  headlines - yfinance news titles with publisher and publication time (titles only, no page text)
A failed fetch is recorded under "missing", never filled (CLAUDE.md).
"""
import datetime
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ET, REGISTRY, ROOT, Sec, now_et, write_json  # noqa: E402

RELEASE_CHARS = 14000
MDA_CHARS = 12000
EIGHTK_CHARS = 1500
MAX_8K = 6
MAX_HEADLINES = 20


def to_text(body):
    from bs4 import BeautifulSoup
    import warnings
    warnings.filterwarnings("ignore")
    if isinstance(body, bytes):
        body = body.decode("utf-8", "ignore")
    soup = BeautifulSoup(body, "lxml")
    for tag in soup.find_all(["ix:header", "script", "style"]):  # inline-XBRL hidden facts are not text
        tag.decompose()
    for tag in soup.find_all(style=re.compile(r"display:\s*none", re.I)):
        tag.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(" ")).strip()
    return text


def eightk_body(text):
    """An 8-K's substance starts at its first 'Item N.NN' after the cover page."""
    m = re.search(r"Item\s+\d\.\d\d", text[300:], re.I)
    return text[300 + m.start():] if m else text


def parse_ts(s):
    if not s:
        return None
    try:
        x = datetime.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return x.astimezone(ET) if x.tzinfo else x.replace(tzinfo=ET)
    except ValueError:
        return None


def exhibit_991(sec, cik, accession):
    """The EX-99.1 document of a filing, read from the filing index's Type column (file names vary:
    ex991.htm, q4fy26exhibit991er.htm ...). Falls back to a file-name match. None if there is none."""
    acc = accession.replace("-", "")
    try:
        html = sec.get(f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{accession}-index.html")
        for row in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S | re.I):
            if re.search(r">\s*EX-99\.?0?1\s*<", row, re.I):
                m = re.search(r'href="[^"]*/([^/"]+\.(?:htm|html|txt))"', row, re.I)
                if m:
                    return m.group(1)
    except Exception:
        pass
    try:
        idx = json.loads(sec.get(f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/index.json"))
        docs = [x["name"] for x in idx["directory"]["item"]]
        return next((n for n in docs if re.search(r"(ex|exhibit)[-_]?99[-_.]?0?1", n, re.I)
                     and n.lower().endswith((".htm", ".html", ".txt"))), None)
    except Exception:
        return None


def mda(text, form):
    """The MD&A section: the last 'Management's Discussion' heading that is followed by real text (the
    first hit is usually the table of contents)."""
    hits = [m.start() for m in re.finditer(r"management(?:.s|s)?\s+discussion\s+and\s+analysis", text, re.I)]
    for h in reversed(hits):
        chunk = text[h:h + MDA_CHARS]
        if len(chunk) > 3000 and not re.search(r"item\s+\d", chunk[200:1200], re.I):
            return chunk, "MD&A"
    return text[:MDA_CHARS], "opening of the filing (MD&A heading not found)"


def build(season, ticker, date):
    edir = os.path.join(ROOT, "events", season, f"{ticker}_{date}")
    gate = json.load(open(os.path.join(edir, "gate.json"), encoding="utf-8"))
    cutoff = parse_ts(gate["captured_et"])
    snap_day = cutoff.date()
    items, missing = [], []

    def ok_date_only(d):
        return datetime.date.fromisoformat(d[:10]) < snap_day

    def add(**kw):
        items.append({"id": f"I{len(items) + 1}", **kw})

    fac = json.load(open(os.path.join(edir, "factors.json"), encoding="utf-8"))
    base = json.load(open(os.path.join(REGISTRY, "D004_base_rates_v3.json"), encoding="utf-8"))
    add(kind="gate", source=f"events/{season}/{ticker}_{date}/gate.json", published=gate["captured_et"],
        data={k: gate.get(k) for k in ("ticker", "report_date", "session", "timing", "snapshot_session",
                                       "captured_et", "options", "status")})
    add(kind="factors", source=f"events/{season}/{ticker}_{date}/factors.json", published=gate["captured_et"],
        data={k: (v.get("value") if isinstance(v, dict) else v) for k, v in (fac.get("factors") or {}).items()})
    add(kind="base_rates", source="registry/D004_base_rates_v3.json", published="2026-09-29",
        data={k: base[k] for k in ("what", "overall", "by_cluster", "by_session", "caveats") if k in base})

    sec = Sec(os.path.join(ROOT, "cache", "sec"))
    cik = sec.cik(ticker)
    if not cik:
        missing.append("SEC: no CIK for the ticker")
    else:
        try:
            rec = sec.submission(cik)["filings"]["recent"]
            rows = [dict(zip(("form", "filingDate", "acceptanceDateTime", "accessionNumber", "primaryDocument", "items"),
                             vals)) for vals in zip(rec["form"], rec["filingDate"], rec["acceptanceDateTime"],
                                                    rec["accessionNumber"], rec["primaryDocument"], rec["items"])]
            for r in rows:
                r["accepted"] = parse_ts(r["acceptanceDateTime"])
            before = [r for r in rows if r["accepted"] and r["accepted"] < cutoff]
            # the latest earnings release: EX-99.1 of the newest Item 2.02 8-K
            rel = next((r for r in before if r["form"].startswith("8-K") and "2.02" in r["items"].split(",")), None)
            if rel:
                acc = rel["accessionNumber"].replace("-", "")
                try:
                    name = exhibit_991(sec, cik, rel["accessionNumber"]) or rel["primaryDocument"]
                    body = sec.get(f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{name}", binary=True)
                    add(kind="release", source=f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{name}",
                        published=rel["accepted"].isoformat(), form=rel["form"],
                        text=to_text(body)[:RELEASE_CHARS])
                except Exception as exc:
                    missing.append(f"earnings release {rel['accessionNumber']}: {type(exc).__name__}: {exc}")
            else:
                missing.append("no Item 2.02 8-K before the snapshot in the SEC recent-filings block")
            per = next((r for r in before if r["form"] in ("10-Q", "10-K", "10-Q/A", "10-K/A")), None)
            if per:
                try:
                    body = sec.document(cik, {"accessionNumber": per["accessionNumber"], "primaryDocument": per["primaryDocument"]})
                    chunk, what = mda(to_text(body), per["form"])
                    acc = per["accessionNumber"].replace("-", "")
                    add(kind="periodic", source=f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{per['primaryDocument']}",
                        published=per["accepted"].isoformat(), form=per["form"], section=what, text=chunk)
                except Exception as exc:
                    missing.append(f"{per['form']} {per['accessionNumber']}: {type(exc).__name__}: {exc}")
            else:
                missing.append("no 10-Q / 10-K before the snapshot")
            lo = cutoff - datetime.timedelta(days=90)
            n8 = 0
            for r in before:
                if not r["form"].startswith("8-K") or r["accepted"] < lo or r is rel or n8 >= MAX_8K:
                    continue
                try:
                    body = sec.document(cik, {"accessionNumber": r["accessionNumber"], "primaryDocument": r["primaryDocument"]})
                    acc = r["accessionNumber"].replace("-", "")
                    add(kind="8k", source=f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{r['primaryDocument']}",
                        published=r["accepted"].isoformat(), form=r["form"], items=r["items"],
                        text=eightk_body(to_text(body))[:EIGHTK_CHARS])
                    n8 += 1
                except Exception as exc:
                    missing.append(f"8-K {r['accessionNumber']}: {type(exc).__name__}: {exc}")
        except Exception as exc:
            missing.append(f"SEC submissions: {type(exc).__name__}: {exc}")

    # headlines: Yahoo Finance's RSS headline feed (yfinance .news returned nothing on 2026-10-05) - the
    # title and the feed's one-line summary, each with its own publication time, strictly before the snapshot
    try:
        import email.utils
        import xml.etree.ElementTree as ET_
        import requests
        from common import WEB_HEADERS
        r = requests.get("https://feeds.finance.yahoo.com/rss/2.0/headline",
                         params={"s": ticker, "region": "US", "lang": "en-US"}, headers=WEB_HEADERS, timeout=30)
        r.raise_for_status()
        kept = []
        for it in ET_.fromstring(r.content).iter("item"):
            title = (it.findtext("title") or "").strip()
            when = it.findtext("pubDate")
            try:
                pub = email.utils.parsedate_to_datetime(when).astimezone(ET) if when else None
            except (TypeError, ValueError):
                pub = None
            if not pub or not title or pub >= cutoff:
                continue
            summ = re.sub(r"\s+", " ", (it.findtext("description") or "")).strip()[:300]
            kept.append((pub, title, summ, (it.findtext("link") or "").strip()))
        for pub, title, summ, link in sorted(kept, reverse=True)[:MAX_HEADLINES]:
            add(kind="headline", source=link or "feeds.finance.yahoo.com/rss/2.0/headline", published=pub.isoformat(),
                text=title + (f" - {summ}" if summ else ""))
        if not kept:
            missing.append("headlines: none dated before the snapshot")
    except Exception as exc:
        missing.append(f"headlines: {type(exc).__name__}: {exc}")

    # Code's own check, the same rule freeze.py applies to an agentic T2 (D004 v2 change 2)
    for it in items:
        pub = it.get("published")
        p = parse_ts(pub)
        if p is None or (len(str(pub)) <= 10 and not ok_date_only(pub)) or (len(str(pub)) > 10 and p >= cutoff):
            if it["kind"] not in ("gate", "factors"):
                raise SystemExit(f"dossier item {it['id']} {it['kind']} published {pub} is not before {cutoff} - refusing")
    out = {"event": f"{ticker}_{date}", "season": season, "built_et": now_et().isoformat(timespec="seconds"),
           "cutoff_et": cutoff.isoformat(), "rule": "D004_decision_protocol_v4 §1 (stage 1)",
           "items": items, "missing": missing,
           "chars": sum(len(json.dumps(i)) for i in items)}
    write_json(os.path.join(edir, "dossier.json"), out)
    print(f"{ticker} {date}: dossier {len(items)} items, {out['chars']} chars; missing: {missing or 'none'}")
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 3:
        raise SystemExit(__doc__)
    t0 = time.time()
    build(a[0], a[1].upper(), a[2])
    print(f"built in {time.time() - t0:.1f}s")
