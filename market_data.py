from __future__ import annotations
import json, threading, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"TraderPlannerPro"; CACHE_PATH=ROOT/"market_cache.json"; USER_AGENT="TraderPlannerPro/7.5"
CRYPTO_FALLBACK=[("BTC","BTC-USD"),("ETH","ETH-USD"),("USDT","USDT-USD"),("BNB","BNB-USD"),("XRP","XRP-USD"),("USDC","USDC-USD"),("SOL","SOL-USD"),("TRX","TRX-USD"),("DOGE","DOGE-USD"),("ADA","ADA-USD")]
FOREX_SYMBOLS=[("GOLD","GC=F"),("SILVER","SI=F"),("COPPER","HG=F"),("EUR/USD","EURUSD=X"),("GBP/USD","GBPUSD=X"),("USD/JPY","JPY=X"),("USD/CHF","CHF=X"),("AUD/USD","AUDUSD=X"),("WTI OIL","CL=F"),("S&P 500","^GSPC"),("NASDAQ 100","^NDX"),("DOW 30","^DJI"),("APPLE","AAPL"),("MICROSOFT","MSFT"),("NVIDIA","NVDA"),("AMAZON","AMZN")]
CRYPTO_ENDPOINT="https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1&sparkline=false&price_change_percentage=24h"
CRYPTO_GLOBAL_ENDPOINT="https://api.coingecko.com/api/v3/global"
YAHOO_ENDPOINT="https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=5m"
FEAR_GREED_ENDPOINT="https://api.alternative.me/fng/?limit=1"

def _request_json(url,timeout=6):
    req=urllib.request.Request(url,headers={"User-Agent":USER_AGENT,"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as r: return json.loads(r.read().decode())
def _f(v):
    try:return float(v)
    except:return None
def _read():
    try:
        d=json.loads(CACHE_PATH.read_text(encoding="utf-8")); return d if isinstance(d,dict) else {}
    except:return {}
def _write(d):
    try:
        CACHE_PATH.parent.mkdir(parents=True,exist_ok=True); tmp=CACHE_PATH.with_suffix(".tmp"); tmp.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8"); tmp.replace(CACHE_PATH)
    except: pass
def _yahoo(symbol):
    try:
        data=_request_json(YAHOO_ENDPOINT.format(symbol=urllib.parse.quote(symbol,safe="")),5)
        result=(data.get("chart",{}).get("result") or [None])[0]
        if not result:return None
        meta=result.get("meta") or {}; price=_f(meta.get("regularMarketPrice")); prev=_f(meta.get("previousClose"))
        if price is None:return None
        ch=((price-prev)/prev*100) if prev not in (None,0) else None
        return price,ch
    except:return None
def _parallel(rows):
    found={}
    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs={pool.submit(_yahoo,s):(label,s) for label,s in rows}
        for f in as_completed(jobs):
            label,_=jobs[f]
            try:v=f.result()
            except:v=None
            if v:found[label]={"symbol":label,"name":label,"price":v[0],"change":v[1]}
    return [found[label] for label,_ in rows if label in found]
def _crypto():
    try:
        rows=_request_json(CRYPTO_ENDPOINT,8)
        return [{"symbol":str(x.get("symbol","")).upper(),"name":x.get("name",""),"price":_f(x.get("current_price")),"change":_f(x.get("price_change_percentage_24h_in_currency"))} for x in rows[:10] if _f(x.get("current_price")) is not None]
    except:return _parallel(CRYPTO_FALLBACK)
def _forex(): return _parallel(FOREX_SYMBOLS)
def _indicators():
    out={"fear_greed":None,"btc_dominance":None,"usdt_dominance":None}
    try:
        row=((_request_json(FEAR_GREED_ENDPOINT,5).get("data") or [None])[0]) or {}
        if row.get("value") is not None:out["fear_greed"]={"value":int(float(row["value"])),"label":str(row.get("value_classification") or "")}
    except:pass
    try:
        pct=(_request_json(CRYPTO_GLOBAL_ENDPOINT,6).get("data") or {}).get("market_cap_percentage") or {}
        out["btc_dominance"]=_f(pct.get("btc")); out["usdt_dominance"]=_f(pct.get("usdt"))
    except:pass
    return out
def fetch_market(mode):
    market="Forex" if str(mode).lower()=="forex" else "Crypto"
    rows=_forex() if market=="Forex" else _crypto(); indicators=_indicators(); now=datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload={"market":market,"updated_at":now,"source":"live" if rows else "unavailable","items":rows,"indicators":indicators}
    if rows:_write(payload); return payload
    cached=_read()
    if cached.get("items"):return {"market":market,"updated_at":cached.get("updated_at"),"source":"cache","items":cached.get("items",[]),"indicators":cached.get("indicators",indicators)}
    return payload
class MarketDataService:
    def __init__(self,callback=None,refresh_seconds=60):self.callback=callback;self.refresh_seconds=max(30,int(refresh_seconds));self._market="Crypto";self._running=False
    def start(self,market):
        self._market="Forex" if market=="Forex" else "Crypto"
        if self._running:return
        self._running=True; threading.Thread(target=self._worker,daemon=True,name="TraderPlannerMarketData").start()
    def set_market(self,market):self._market="Forex" if market=="Forex" else "Crypto"
    def stop(self):self._running=False
    def _worker(self):
        while self._running:
            p=fetch_market(self._market)
            if self.callback:
                try:self.callback(p)
                except:pass
            end=time.time()+self.refresh_seconds
            while self._running and time.time()<end:time.sleep(1)
