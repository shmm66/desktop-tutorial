from __future__ import annotations

import concurrent.futures
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
COINDESK_HOME = "https://www.coindesk.com/"
CRYPTO_NEWS_HOME = "https://cryptoslate.com/news-terminal/"

FEEDS = [
    ("CoinDesk", COINDESK_RSS),
    ("Cointelegraph", COINTELEGRAPH_RSS),
    ("Decrypt", DECRYPT_RSS),
    ("CryptoSlate", CRYPTOSLATE_RSS),
    ("Google News • Crypto", GOOGLE_CRYPTO_RSS),
]

USER_AGENT = "TraderPlannerPro/7.9"


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


def _download_feed(url, timeout=12):
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        "Cache-Control": "no-cache",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read()
    except Exception as primary_error:
        try:
            import requests
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.content
        except Exception:
            raise primary_error


def fetch_rss(url, source="News", limit=12):
    data = _download_feed(url, timeout=12)
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


def fetch_all_news(limit=24):
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(FEEDS)) as pool:
        jobs = {pool.submit(fetch_rss, url, source, max(8, limit)): source for source, url in FEEDS}
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
    if not rows:
        # Always leave the in-app news terminal useful even when all RSS
        # publishers are blocked by a corporate proxy or DNS filter.
        rows = [
            {"source":"CoinDesk","title":"Open CoinDesk live news terminal","link":COINDESK_HOME,"published":"LIVE"},
            {"source":"Cointelegraph","title":"Open Cointelegraph live news","link":"https://cointelegraph.com/","published":"LIVE"},
            {"source":"CryptoSlate","title":"Open CryptoSlate live news terminal","link":CRYPTO_NEWS_HOME,"published":"LIVE"},
            {"source":"Forex Factory","title":"Open Forex Factory economic calendar","link":FOREX_FACTORY,"published":"LIVE"},
        ]
    return rows[:limit]


def fetch_crypto_news(callback):
    def worker():
        try:
            rows = fetch_all_news(limit=24)
        except Exception:
            rows = []
        callback(rows)

    threading.Thread(target=worker, name="TraderPlannerNews", daemon=True).start()
