from __future__ import annotations
import html, threading, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
NEWS_SOURCES={
 "forex_factory":{"name":"Forex Factory","feed":"https://www.forexfactory.com/rss.php","url":"https://www.forexfactory.com/news"},
 "coindesk":{"name":"CoinDesk","feed":"https://www.coindesk.com/arc/outboundfeeds/rss/","url":"https://www.coindesk.com/"},
}
def fetch_news(key,limit=12):
    src=NEWS_SOURCES[key]
    try:
        req=urllib.request.Request(src["feed"],headers={"User-Agent":"TraderPlannerPro/7.5","Accept":"application/rss+xml, application/xml, text/xml"})
        with urllib.request.urlopen(req,timeout=10) as r: data=r.read()
        root=ET.fromstring(data); rows=[]
        for item in root.findall(".//item")[:limit]:
            rows.append({"source":src["name"],"title":html.unescape((item.findtext("title") or "").strip()),
                         "link":html.unescape((item.findtext("link") or "").strip()),
                         "published":html.unescape((item.findtext("pubDate") or "").strip()),
                         "summary":html.unescape((item.findtext("description") or "").strip())[:300]})
        return {"ok":True,"source":key,"items":rows,"updated_at":datetime.now(timezone.utc).isoformat(timespec="seconds")}
    except Exception as exc:
        return {"ok":False,"source":key,"items":[],"error":str(exc),"updated_at":datetime.now(timezone.utc).isoformat(timespec="seconds")}
def fetch_all(callback):
    def worker():
        payload={k:fetch_news(k) for k in NEWS_SOURCES}; callback(payload)
    threading.Thread(target=worker,daemon=True).start()
