"""
PRE EDGAR fetcher — locates the PRIMARY guidance document for a name.
================================================================================
Built 2026-07-30. Answers the owner's question "python or outsource?" — the answer is
PYTHON, via SEC EDGAR, and it beats outsourcing on every axis that matters:

  * It IS the primary source. A vendor's guidance field is that vendor's READING of this
    document; EDGAR is the document. PRE's hard rule is verify against a primary source,
    and this is the primary source.
  * Free, official, no key, no rate contract (SEC asks only for a declared User-Agent).
  * Auditable: every record carries the exact accession URL, so a GG can be re-checked
    years later. A paid feed gives you a number with no way to re-derive it.

WHAT THIS MODULE DOES AND DELIBERATELY DOES NOT DO
  DOES:     find the company's earnings 8-K, pull the press-release exhibit, and return the
            guidance/outlook section as text WITH its citation.
  DOES NOT: parse the numbers into a verdict. Guidance prose is not reliably machine-parseable
            (ranges, GAAP vs non-GAAP, segment tables, footnoted exclusions), and a regex that
            silently mis-reads a range would inject a fabricated input into the one term built
            to be unfabricated. The numbers are read from the returned excerpt and recorded in
            a GuidanceRecord, whose provenance fields this module pre-fills so the citation
            cannot be typed by hand.

I/O lives here; `pre_guidance` stays pure and deterministic so it remains unit-testable.

THE PERIOD-MATCHING PROBLEM (found while building this — it changes the GG definition)
GG compares a company's guidance to its OWN PRIOR guidance FOR THE SAME PERIOD. But most US
issuers guide only ONE quarter ahead: the Q3 release guides Q4, the Q4 release guides Q1. Each
QUARTER is therefore guided exactly once and has no same-period predecessor to compare against.
Verified on QUALCOMM's 2026-07-29 8-K: it guides Q4 FY26 only, with no annual outlook.

The comparison that DOES exist is the FULL-YEAR guide, which is re-issued at every quarterly
release for the same fiscal year. That is what "raised full-year guidance" means in a headline,
and it is the statement the market actually reacts to. So:

    PRIMARY   full-year guidance vs the SAME fiscal year's guide in the prior release
    STRONGEST any mid-quarter revision (pre-announcement) — rare, and flagged FRESH
    UNUSABLE  next-quarter guidance with no same-period prior -> GG stays None

CONSEQUENCE, stated rather than discovered later: GG coverage is PARTIAL BY CONSTRUCTION.
Issuers that give annual guidance (most large caps) yield a GG; issuers that guide one quarter
at a time (QCOM and much of semis) do not. That is handled correctly already — an absent GG
lowers completeness and shrinks the position; it does not fabricate a zero.
"""
from __future__ import annotations

import json
import re
import urllib.request
from typing import Optional

__version__ = "1.0.0"

# SEC requires a declared User-Agent identifying the requester.
UA = {"User-Agent": "PRE-research jacobong999@gmail.com"}
_CIK_CACHE: dict = {}

# The guidance section is reliably introduced by one of these headings.
OUTLOOK_HEADS = ("Business Outlook", "Financial Outlook", "Guidance", "Outlook",
                 "Fiscal 2026 Outlook", "Full Year Outlook", "Current Guidance")

# Language that signals a company REVISING its own prior outlook — the high-signal case.
REVISION_RE = re.compile(
    r"\b(rais\w+|increas\w+|lower\w+|reduc\w+|cut\w*|reiterat\w+|reaffirm\w+|maintain\w+|"
    r"updat\w+|narrow\w+|withdraw\w+)\s+(?:its\s+|our\s+|the\s+)?(?:full[- ]year\s+|"
    r"fiscal\s+\d{4}\s+|annual\s+)?(?:revenue\s+|earnings\s+|EPS\s+)?(guidance|outlook)",
    re.I)


def _get(url: str, raw: bool = False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        b = r.read()
    return b if raw else json.loads(b)


def cik_of(ticker: str) -> Optional[str]:
    """Zero-padded CIK for a ticker, from the SEC's own mapping file."""
    if not _CIK_CACHE:
        for row in _get("https://www.sec.gov/files/company_tickers.json").values():
            _CIK_CACHE[row["ticker"].upper()] = str(row["cik_str"]).zfill(10)
    return _CIK_CACHE.get(ticker.upper())


def earnings_8ks(ticker: str, n: int = 4) -> list:
    """The most recent earnings 8-Ks (Item 2.02 = Results of Operations), newest first.

    Item 2.02 is the filter that separates an earnings release from every other 8-K
    (executive changes, debt, byline amendments), so this does not depend on guessing
    from the filing date.
    """
    cik = cik_of(ticker)
    if not cik:
        return []
    d = _get(f"https://data.sec.gov/submissions/CIK{cik}.json")
    r = d["filings"]["recent"]
    items = r.get("items", [""] * len(r["form"]))
    out, seen_dates = [], set()
    for form, acc, fdate, item in zip(r["form"], r["accessionNumber"], r["filingDate"], items):
        # 8-K Item 2.02 is "Results of Operations" — the exact filter that separates an
        # earnings release from every other 8-K without guessing from the date.
        # FOREIGN PRIVATE ISSUERS (ARM) file 6-K instead, which carries NO item codes at all,
        # so they are admitted on form alone and de-duplicated by date. Excluding them was
        # silently dropping every non-US name from GG coverage.
        is_earnings_8k = form == "8-K" and "2.02" in (item or "")
        is_6k = form == "6-K"
        if not (is_earnings_8k or is_6k):
            continue
        if is_6k and fdate in seen_dates:
            continue        # issuers often file several 6-Ks the same day
        seen_dates.add(fdate)
        out.append({"ticker": ticker.upper(), "cik": cik, "filing_date": fdate,
                    "accession": acc, "form": form,
                    "confidence": "ITEM_2.02" if is_earnings_8k else "FORM_6K_UNVERIFIED"})
        if len(out) >= n:
            break
    return out


# Exhibit-99 filenames are NOT standardised across filing agents. All four of these are the
# same thing, observed in one sitting:
#   msft-ex99_1.htm | exhibit991erq32026.htm | qcom062826erex991.htm | lrcx_exhibitx991xq4x2026.htm
# A naive r"ex-?99" matches two of the four and SILENTLY misses the others — which is how FICO
# and LRCX both came back "no EX-99 exhibit" on filings that plainly have one. Allow the
# optional "hibit" and up to two separator characters (agents use '-', '_', and 'x' for dots).
EX99_RE = re.compile(r"ex(?:hibit)?.{0,2}?99", re.I)
# Fallback for agents that name the release without any "99" at all.
RELEASE_RE = re.compile(r"press|earning|release|results", re.I)
# Last resort: the filing's own primary document, e.g. arm-20260630.htm. Foreign private
# issuers file 6-K and often carry the results in the primary doc with no EX-99 at all.
PRIMARY_RE = re.compile(r"^[a-z]{1,6}[-_]\d{8}\.htm$", re.I)
# Never mistake XBRL viewer fragments for the press release.
NOT_RELEASE_RE = re.compile(r"^(R\d+\.htm|FilingSummary|MetaLinks|Show\.js|report\.css)", re.I)


def press_release_url(filing: dict) -> Optional[str]:
    """The press-release document inside an earnings 8-K / 6-K, by decreasing confidence."""
    cik, acc = filing["cik"], filing["accession"]
    a = acc.replace("-", "")
    idx = _get(f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{a}/index.json")
    names = [i["name"] for i in idx["directory"]["item"]
             if i["name"].endswith((".htm", ".txt")) and not NOT_RELEASE_RE.match(i["name"])
             and not i["name"].startswith(acc)]
    cand = ([f for f in names if EX99_RE.search(f)]
            or [f for f in names if RELEASE_RE.search(f)]
            or [f for f in names if PRIMARY_RE.match(f)])
    if not cand:
        return None
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{a}/{cand[0]}"


def _plain(html: str) -> str:
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    t = re.sub(r"<[^>]+>", " ", t)
    for ent, rep in (("&#8211;", "-"), ("&#8212;", "-"), ("&#8217;", "'"), ("&#8220;", '"'),
                     ("&#8221;", '"'), ("&nbsp;", " "), ("&#160;", " "), ("&amp;", "&")):
        t = t.replace(ent, rep)
    return re.sub(r"\s+", " ", t).strip()


def outlook_excerpt(url: str, chars: int = 2200) -> dict:
    """Return the guidance section plus any explicit revision language, with the citation.

    The excerpt is what a human/LLM reads to fill in a GuidanceRecord. The citation fields
    are returned alongside so they are COPIED FROM THE FETCH rather than typed — which is
    what makes the provenance contract in pre_guidance hard to fake.
    """
    text = _plain(_get(url, raw=True).decode("utf-8", "ignore"))
    start, head = None, None
    for h in OUTLOOK_HEADS:
        i = text.find(h)
        if i != -1 and (start is None or i < start):
            start, head = i, h
    excerpt = text[start:start + chars] if start is not None else None
    revisions = sorted({m.group(0).strip() for m in REVISION_RE.finditer(text)})
    return {"source_url": url, "heading": head, "excerpt": excerpt,
            "revision_language": revisions, "chars": len(text)}


def guidance_pack(ticker: str, n: int = 2) -> dict:
    """One call per name: the last `n` earnings releases with their outlook sections.

    Two releases is the minimum that supports a GG, because GG is a COMPARISON — the current
    full-year guide against the SAME fiscal year's guide in the prior release. One release
    can never produce a GG, which is exactly why the naive "just read the latest press
    release" approach silently fails.
    """
    pack = {"ticker": ticker.upper(), "releases": [], "notes": []}
    filings = earnings_8ks(ticker, n=n)
    if not filings:
        pack["notes"].append("no Item 2.02 earnings 8-K found (foreign issuer files 6-K?)")
        return pack
    for f in filings:
        try:
            url = press_release_url(f)
            if not url:
                pack["notes"].append(f"{f['filing_date']}: no EX-99 exhibit"); continue
            ex = outlook_excerpt(url)
            ex["filing_date"] = f["filing_date"]
            ex["accession"] = f["accession"]
            pack["releases"].append(ex)
        except Exception as e:
            pack["notes"].append(f"{f['filing_date']}: {e!r}"[:140])
    if len(pack["releases"]) < 2:
        pack["notes"].append("fewer than 2 releases retrieved — a GG comparison needs both "
                             "the current and the prior guide for the SAME period")
    return pack


if __name__ == "__main__":
    import sys
    for t in sys.argv[1:] or ["MSFT"]:
        p = guidance_pack(t)
        print(f"\n===== {p['ticker']} =====")
        for r in p["releases"]:
            print(f"  {r['filing_date']}  [{r['heading']}]  {r['source_url']}")
            if r["revision_language"]:
                print(f"     revision language: {', '.join(r['revision_language'][:4])}")
            if r["excerpt"]:
                print(f"     {r['excerpt'][:420]}...")
        for n in p["notes"]:
            print("  ! " + n)
