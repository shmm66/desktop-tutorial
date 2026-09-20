from __future__ import annotations

import email.utils
import threading
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

COINDESK_RSS = "https://www.coindesk.com/feed"
FOREX_FACTORY = "https://www.forexfactory.com/calendar"
COINDESK_HOME = "https://www.coindesk.com/"

USER_AGENT = "TraderPlannerPro/7.5"


def fetch_rss(url=COINDESK_RSS, limit=12):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml, text/xml"})
    with urllib.request.urlopen(req, timeout=8) as response:
        data = response.read()
    root = ET.fromstring(data)
    items = []
    for item in root.findall(".//item")[:limit]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        stamp = ""
        if pub:
            try:
                stamp = datetime.fromtimestamp(email.utils.parsedate_to_datetime(pub).timestamp(), tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            except Exception:
                stamp = pub
        if title and link:
            items.append({"title": title, "link": link, "published": stamp})
    return items


def fetch_crypto_news(callback):
    def worker():
        try:
            rows = fetch_rss()
        except Exception:
            rows = []
        callback(rows)
    threading.Thread(target=worker, daemon=True).start()
