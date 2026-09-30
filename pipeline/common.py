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
        # 0.45 s per process: four parallel gate workers stay under SEC's 10 requests/second
        wait = 0.45 - (time.time() - self.last)
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

    def facts(self, cik):
        """XBRL companyfacts, cached on disk for 12 hours (stage and H factors both read it)."""
        path = os.path.join(self.cache_dir, f"companyfacts_{cik}.json")
        if os.path.exists(path) and time.time() - os.path.getmtime(path) < 12 * 3600:
            return json.load(open(path, encoding="utf-8"))
        body = self.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json")
        os.makedirs(self.cache_dir, exist_ok=True)
        tmp = f"{path}.{os.getpid()}"
        open(tmp, "w", encoding="utf-8").write(body)
        os.replace(tmp, path)
        return json.loads(body)

    def cik(self, ticker):
        if self._tickers is None:
            # cached on disk for 12 hours: parallel gate processes would otherwise each fetch it
            path = os.path.join(self.cache_dir, "company_tickers.json")
            if os.path.exists(path) and time.time() - os.path.getmtime(path) < 12 * 3600:
                body = open(path, encoding="utf-8").read()
            else:
                body = self.get("https://www.sec.gov/files/company_tickers.json")
                os.makedirs(self.cache_dir, exist_ok=True)
                tmp = f"{path}.{os.getpid()}"
                open(tmp, "w", encoding="utf-8").write(body)
                os.replace(tmp, path)
            rows = json.loads(body).values()
            self._tickers = {row["ticker"].upper(): int(row["cik_str"]) for row in rows}
        t = ticker.upper()
        return self._tickers.get(t) or self._tickers.get(t.replace("-", ".")) or self._tickers.get(t.replace(".", "-"))

    def submission(self, cik):
        if not hasattr(self, "_subs"):
            self._subs = {}
        if cik not in self._subs:
            self._subs[cik] = json.loads(self.get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json"))
        return self._subs[cik]

    def filings(self, cik):
        """All filings (recent block) as a list of dicts, newest first."""
        sub = self.submission(cik)
        rec = sub["filings"]["recent"]
        keys = ["form", "filingDate", "accessionNumber", "primaryDocument"]
        return [dict(zip(keys, vals)) for vals in zip(*(rec[k] for k in keys))]

    def document(self, cik, filing):
        acc = filing["accessionNumber"].replace("-", "")
        path = os.path.join(self.cache_dir, f"{cik}_{acc}_{filing['primaryDocument'].replace('/', '_')}")
        if os.path.exists(path):
            return open(path, "rb").read()
        url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{filing['primaryDocument']}"
        body = self.get(url, binary=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        open(path, "wb").write(body)
        return body


def rule_for(base, season):
    """The frozen rule version that governs a season (rule 5: a new version never touches the seasons
    before it). Scans FROZEN.sha256 for <base>_vN.json; a version applies to the seasons in its
    `applies_to_seasons` list (v1, which has none, to its own `seasons`). The highest N that applies wins.
    Every candidate is loaded through registry(), so an unfrozen or altered file is refused."""
    best = None
    for line in open(os.path.join(REGISTRY, "FROZEN.sha256"), encoding="utf-8"):
        if not line.strip():
            continue
        name = line.split(maxsplit=1)[1].strip().lstrip("*")
        if not (name.startswith(base + "_v") and name.endswith(".json")):
            continue
        n = int(name[len(base) + 2:-5])
        data = registry(name)
        applies = data.get("applies_to_seasons") or list(data.get("seasons", {}))
        if season in applies and (best is None or n > best[0]):
            best = (n, data)
    if best is None:
        raise SystemExit(f"no frozen {base} version covers season {season!r}")
    return best[1]
