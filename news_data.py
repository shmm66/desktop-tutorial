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
GOOGLE_FOREX_RSS = (
    "https://news.google.com/rss/search?"
    "q=(forex+OR+EURUSD+OR+GBPUSD+OR+USDJPY+OR+Federal+Reserve)+when:1d&hl=en-US&gl=US&ceid=US:en"
)
FOREX_FACTORY = "https://www.forexfactory.com/calendar"
FOREX_FACTORY_FEED = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
COINDESK_HOME = "https://www.coindesk.com/"
CRYPTO_NEWS_HOME = "https://cryptoslate.com/news-terminal/"

FOREX_FEEDS = [
    ("Forex Factory", FOREX_FACTORY_FEED),
    ("Google News • Forex", GOOGLE_FOREX_RSS),
]

FEEDS = [
    ("CoinDesk", COINDESK_RSS),
    ("Cointelegraph", COINTELEGRAPH_RSS),
    ("Decrypt", DECRYPT_RSS),
    ("CryptoSlate", CRYPTOSLATE_RSS),
    ("Google News • Crypto", GOOGLE_CRYPTO_RSS),
    ("Google News • Forex", GOOGLE_FOREX_RSS),
]

USER_AGENT = "TraderPlannerPro/8.3.0"
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


def _download_feed_bytes(url):
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        "Cache-Control": "no-cache",
    }
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=4.5) as response:
            return response.read()
    except Exception:
        # Some desktop networks block feed hosts with browser-like TLS or 403
        # rules. A text proxy gives the parser one additional non-auth path.
        proxy = "https://r.jina.ai/http://" + url.split("://", 1)[-1]
        proxy_request = urllib.request.Request(proxy, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(proxy_request, timeout=6.0) as response:
            return response.read()


def fetch_rss(url, source="News", limit=12):
    data = _download_feed_bytes(url)
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        # Jina can return an HTML/Markdown representation for a feed. Extract
        # the most useful linked headlines rather than returning an empty page.
        text_blob = data.decode("utf-8", "ignore")
        links = re.findall(r"\[([^\]]{8,180})\]\((https?://[^)]+)\)", text_blob)
        rows = []
        seen = set()
        for title, link in links:
            clean_title = _clean(title)
            if clean_title and link not in seen and not link.lower().endswith((".jpg",".png",".webp")):
                seen.add(link)
                rows.append({
                    "source": source,
                    "title": clean_title,
                    "link": link,
                    "published": "",
                })
            if len(rows) >= limit:
                break
        return rows

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
    executor = concurrent.futures.ThreadPoolExecutor(
        max_workers=min(6, max(1, len(feeds))), thread_name_prefix="TPNews"
    )
    jobs = {
        executor.submit(fetch_rss, url, source, max(8, limit)): source
        for source, url in feeds
    }
    # Never wait indefinitely for a broken RSS endpoint.
    done, _ = concurrent.futures.wait(jobs, timeout=9.0)
    for job in done:
        try:
            results.extend(job.result(timeout=0.1))
        except Exception:
            continue
    try:
        executor.shutdown(wait=False, cancel_futures=True)
    except Exception:
        try:
            executor.shutdown(wait=False)
        except Exception:
            pass

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


def cached_news(limit=28):
    try:
        rows = json.loads(NEWS_CACHE.read_text(encoding="utf-8"))
        if isinstance(rows, list):
            return rows[:limit]
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
