"""Shared plumbing for the pipeline: paths, the US-Eastern clock, the frozen registry, SEC access."""
import datetime
import hashlib
import json
import os
import time
from zoneinfo import ZoneInfo

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(ROOT, "registry")
ET = ZoneInfo("America/New_York")

# SEC returns 403 without a User-Agent (CLAUDE.md data-source facts).
SEC_HEADERS = {"User-Agent": "EarningsExperiment research jacobong999@gmail.com",
               "Accept-Encoding": "gzip, deflate"}
WEB_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) EarningsExperiment research",
               "Accept": "application/json"}


def now_et():
    return datetime.datetime.now(ET)


def registry(name):
    """Load a frozen registry JSON, refusing to run if its hash no longer matches FROZEN.sha256."""
    path = os.path.join(REGISTRY, name)
    data = open(path, "rb").read().replace(b"\r\n", b"\n")
    digest = hashlib.sha256(data).hexdigest()
    for line in open(os.path.join(REGISTRY, "FROZEN.sha256"), encoding="utf-8"):
        if line.strip() and line.split(maxsplit=1)[1].strip().lstrip("*") == name:
            if line.split()[0] != digest:
                raise SystemExit(f"{name} does not match its frozen hash - refusing to run")
            return json.loads(data)
    raise SystemExit(f"{name} is not in FROZEN.sha256 - refusing to run on an unfrozen rule")


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False, default=str)
        f.write("\n")


def write_once(path, obj):
    """Raw captures are never overwritten (D001 §2: fetch once)."""
    if os.path.exists(path):
        raise SystemExit(f"{path} already exists - raw captures are never overwritten")
    write_json(path, obj)


class Sec:
    """Polite SEC EDGAR client: User-Agent, <= 5 requests a second, simple on-disk cache for filings."""

    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        self.last = 0.0
        self._tickers = None

    def get(self, url, binary=False):
        wait = 0.2 - (time.time() - self.last)
        if wait > 0:
            time.sleep(wait)
        for attempt in range(3):
            r = requests.get(url, headers=SEC_HEADERS, timeout=60)
            self.last = time.time()
            if r.status_code == 200:
                return r.content if binary else r.text
            if r.status_code in (429, 503):
                time.sleep(2 * (attempt + 1))
                continue
            r.raise_for_status()
        r.raise_for_status()

    def cik(self, ticker):
        if self._tickers is None:
            rows = json.loads(self.get("https://www.sec.gov/files/company_tickers.json")).values()
            self._tickers = {row["ticker"].upper(): int(row["cik_str"]) for row in rows}
        t = ticker.upper()
        return self._tickers.get(t) or self._tickers.get(t.replace("-", ".")) or self._tickers.get(t.replace(".", "-"))

    def filings(self, cik):
        """All filings (recent block) as a list of dicts, newest first."""
        sub = json.loads(self.get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json"))
        rec = sub["filings"]["recent"]
        keys = ["form", "filingDate", "accessionNumber", "primaryDocument"]
        return [dict(zip(keys, vals)) for vals in zip(*(rec[k] for k in keys))]

    def document(self, cik, filing):
        acc = filing["accessionNumber"].replace("-", "")
        path = os.path.join(self.cache_dir, f"{cik}_{acc}_{filing['primaryDocument']}")
        if os.path.exists(path):
            return open(path, "rb").read()
        url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{filing['primaryDocument']}"
        body = self.get(url, binary=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        open(path, "wb").write(body)
        return body
