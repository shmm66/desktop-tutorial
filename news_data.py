from __future__ import annotations

import concurrent.futures
import json
from pathlib import Path
import email.utils
import html
import re
import threading
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

COINDESK_RSS = "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml"
COINTELEGRAPH_RSS = "https://cointelegraph.com/rss"
DECRYPT_RSS = "https://decrypt.co/feed"
CRYPTOSLATE_RSS = "https://cryptoslate.com/feed/"
GOOGLE_CRYPTO_RSS = (
    "https://news.google.com/rss/search?"
    "q=(bitcoin+OR+ethereum+OR+crypto+OR+blockchain)+when:1d&hl=en-US&gl=US&ceid=US:en"
)
FOREX_FACTORY = "https://www.forexfactory.com/calendar"
FOREX_FACTORY_FEED = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
COINDESK_HOME = "https://www.coindesk.com/"
CRYPTO_NEWS_HOME = "https://cryptoslate.com/news-terminal/"

FOREX_FEEDS = [("Forex Factory", FOREX_FACTORY_FEED)]

FEEDS = [
    ("CoinDesk", COINDESK_RSS),
    ("Cointelegraph", COINTELEGRAPH_RSS),
    ("Decrypt", DECRYPT_RSS),
    ("CryptoSlate", CRYPTOSLATE_RSS),
    ("Google News • Crypto", GOOGLE_CRYPTO_RSS),
]

USER_AGENT = "TraderPlannerPro/7.9"
NEWS_CACHE = Path.home() / "TraderPlannerPro" / "news_cache.json"


def _clean(value):
    return html.unescape(re.sub(r"<[^>]+>", " ", value or "")).replace("\xa0", " ").strip()


def _parse_stamp(value):
    raw = (value or "").strip()
    if not raw:
        return ""
    try:
        dt = email.utils.parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        except Exception:
            return raw


def fetch_rss(url, source="News", limit=12):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
            "Cache-Control": "no-cache",
        },
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        data = response.read()

    root = ET.fromstring(data)
    items = []

    # RSS 2.0
    for item in root.findall(".//item"):
        title = _clean(item.findtext("title"))
        link = _clean(item.findtext("link"))
        pub = item.findtext("pubDate") or item.findtext("published")
        if title and link:
            items.append({
                "source": source,
                "title": title,
                "link": link,
                "published": _parse_stamp(pub),
            })

    # Atom feeds
    if not items:
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for entry in root.findall(".//a:entry", ns):
            title = _clean(entry.findtext("a:title", default="", namespaces=ns))
            link = ""
            link_el = entry.find("a:link", ns)
            if link_el is not None:
                link = (link_el.attrib.get("href") or "").strip()
            pub = entry.findtext("a:published", default="", namespaces=ns) or entry.findtext(
                "a:updated", default="", namespaces=ns
            )
            if title and link:
                items.append({
                    "source": source,
                    "title": title,
                    "link": link,
                    "published": _parse_stamp(pub),
                })

    return items[:limit]


def fetch_all_news(limit=24, include_forex=False):
    results = []
    feeds = list(FEEDS) + (FOREX_FEEDS if include_forex else [])
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(feeds)) as pool:
        jobs = {pool.submit(fetch_rss, url, source, max(8, limit)): source for source, url in feeds}
        for job in concurrent.futures.as_completed(jobs):
            try:
                results.extend(job.result())
            except Exception:
                continue

    unique = {}
    for row in results:
        key = re.sub(r"[^a-z0-9]+", "", row.get("title", "").lower())
        if key:
            unique.setdefault(key, row)

    rows = list(unique.values())
    rows.sort(key=lambda row: row.get("published", ""), reverse=True)
    rows = rows[:limit]
    if rows:
        try:
            NEWS_CACHE.parent.mkdir(parents=True, exist_ok=True)
            NEWS_CACHE.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass
        return rows

    try:
        cached = json.loads(NEWS_CACHE.read_text(encoding="utf-8"))
        if isinstance(cached, list):
            return cached[:limit]
    except (OSError, ValueError, TypeError):
        pass
    return []


def fetch_market_news(callback, include_forex=False):
    def worker():
        try:
            rows = fetch_all_news(limit=28, include_forex=include_forex)
        except Exception:
            rows = []
        callback(rows)

    threading.Thread(target=worker, name="TraderPlannerNews", daemon=True).start()


def fetch_crypto_news(callback):
    fetch_market_news(callback, include_forex=False)
