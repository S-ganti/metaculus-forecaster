"""
sources.py - public-data fetchers for the forecaster. Standard library only.

Every fetch is cached to data/cache/<name>.json with the fetch time, so a forecast can be
re-run later on exactly the data it was made with (pre-registration needs that).

Sources (all free, no API key):
  google_news(q)   Google News RSS search                  -> headlines, outlet, date
  reddit(q)        PullPush public Reddit archive          -> posts (title, body, score)
  fred(series)     St. Louis Fed FRED CSV                  -> (date, value) observations
  gdelt_tone(q)    GDELT 2.0 doc API, average news tone     -> rate-limited; optional

Not available here (as of 2026-10-16):
  X / Twitter      search needs a signed-in account. Sign into X in BrowserOS neo and
                   collect posts with collect_x.js (see README), then load_posts() them.
  reddit.com       direct access is blocked from this network; PullPush is the route.
"""
from __future__ import annotations

import csv
import io
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

CACHE = Path(__file__).parent / "data" / "cache"
UA = {"User-Agent": "Mozilla/5.0 (metaculus-forecaster research script)"}


def _get(url: str, timeout: int = 30, retries: int = 2) -> bytes:
    last = None
    for i in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # 429s and timeouts: back off and retry
            last = e
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"fetch failed: {url} ({last})")


def _cached(name: str, fetch, refresh: bool = False):
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{name}.json"
    if f.exists() and not refresh:
        return json.loads(f.read_text(encoding="utf-8"))["items"]
    items = fetch()
    f.write_text(json.dumps({"fetched_utc": datetime.now(timezone.utc).isoformat(),
                             "items": items}, ensure_ascii=False, indent=1), encoding="utf-8")
    return items


# --------------------------------------------------------------------------- news
def google_news(query: str, days: int = 30, name: str | None = None, refresh: bool = False):
    """Headlines from Google News RSS for the last `days` days."""
    def fetch():
        q = urllib.parse.quote_plus(f"{query} when:{days}d")
        raw = _get(f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en")
        out = []
        for it in ET.fromstring(raw).iter("item"):
            title = it.findtext("title") or ""
            src = it.find("source")
            try:
                d = parsedate_to_datetime(it.findtext("pubDate")).date().isoformat()
            except Exception:
                d = ""
            out.append({"title": title, "source": src.text if src is not None else "",
                        "date": d, "link": it.findtext("link") or ""})
        return sorted(out, key=lambda x: x["date"], reverse=True)
    return _cached(name or f"news_{_slug(query)}", fetch, refresh)


# --------------------------------------------------------------------------- reddit
def reddit(query: str, days: int = 30, size: int = 100, name: str | None = None,
           refresh: bool = False):
    """Reddit submissions matching `query` in the last `days` days, via PullPush."""
    def fetch():
        after = int(time.time()) - days * 86400
        q = urllib.parse.quote(query)
        raw = _get(f"https://api.pullpush.io/reddit/search/submission/"
                   f"?q={q}&after={after}&size={size}&sort=desc&sort_type=created_utc")
        out = []
        for d in json.loads(raw).get("data", []):
            out.append({"title": d.get("title", ""),
                        "body": (d.get("selftext") or "")[:1500],
                        "score": d.get("score", 0),
                        "comments": d.get("num_comments", 0),
                        "sub": d.get("subreddit", ""),
                        "date": datetime.fromtimestamp(d.get("created_utc", 0),
                                                       timezone.utc).date().isoformat()})
        return out
    return _cached(name or f"reddit_{_slug(query)}", fetch, refresh)


# --------------------------------------------------------------------------- data
def fred(series: str, refresh: bool = False):
    """FRED series as [(date, value)], missing values dropped."""
    def fetch():
        raw = _get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}").decode()
        rows = list(csv.reader(io.StringIO(raw)))[1:]
        return [[d, float(v)] for d, v in rows if v not in ("", ".")]
    return _cached(f"fred_{series}", fetch, refresh)


def gdelt_tone(query: str, days: int = 30, refresh: bool = False):
    """Daily average tone of global news coverage (GDELT). Heavily rate-limited; may fail."""
    def fetch():
        q = urllib.parse.quote(query)
        raw = _get(f"https://api.gdeltproject.org/api/v2/doc/doc?query={q}"
                   f"&mode=timelinetone&timespan={days}d&format=json", retries=3)
        series = json.loads(raw).get("timeline", [{}])[0].get("data", [])
        return [{"date": s["date"][:8], "tone": s["value"]} for s in series]
    return _cached(f"gdelt_{_slug(query)}", fetch, refresh)


def load_posts(path: str | Path):
    """Load posts you collected yourself (e.g. X via BrowserOS) from a JSON list of
    {"title"/"text", "date"} objects."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _slug(s: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in s.lower()).strip("_")[:60]
