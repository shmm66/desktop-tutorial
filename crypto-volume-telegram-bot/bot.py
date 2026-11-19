import os, asyncio, statistics, logging
from datetime import datetime, timezone
import httpx

TG_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN","").strip()
CHAT_ID=os.getenv("TELEGRAM_CHAT_ID","").strip()
CG_KEY=os.getenv("COINGECKO_DEMO_API_KEY","").strip()
CMC_KEY=os.getenv("COINMARKETCAP_API_KEY","").strip()
TOP_N=min(100,max(10,int(os.getenv("TOP_N","100"))))
RVOL_MIN=float(os.getenv("ALERT_RVOL","2.0"))
RVOL_MAX=float(os.getenv("ALERT_COLLAPSE","0.5"))
CG="https://api.coingecko.com/api/v3"
BN="https://api.binance.com"
logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s")
log=logging.getLogger("scanner")

async def get(client,url,params=None,headers=None):
    err=None
    for i in range(4):
        try:
            r=await client.get(url,params=params,headers=headers,timeout=20)
            if r.status_code==429 or r.status_code>=500:
                await asyncio.sleep(min(2**i,12)); continue
            r.raise_for_status(); return r.json()
        except Exception as e:
            err=e; await asyncio.sleep(min(2**i,12))
    raise RuntimeError(f"API request failed: {url}: {err}")

async def get_universe(c):
    h={"x-cg-demo-api-key":CG_KEY} if CG_KEY else {}
    try:
        data=await get(c,CG+"/coins/markets",{"vs_currency":"usd","order":"market_cap_desc","per_page":TOP_N,"page":1,"sparkline":"false"},h)
        return [{"symbol":x["symbol"].upper(),"name":x["name"],"rank":x.get("market_cap_rank"),"change24":x.get("price_change_percentage_24h"),"change7":x.get("price_change_percentage_7d_in_currency")} for x in data]
    except Exception as e:
        log.warning("CoinGecko failed: %s",e)
    if CMC_KEY:
        d=await get(c,"https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest",{"start":1,"limit":TOP_N,"convert":"USD"},{"X-CMC_PRO_API_KEY":CMC_KEY})
        return [{"symbol":x["symbol"].upper(),"name":x["name"],"rank":x.get("cmc_rank"),"change24":x["quote"]["USD"].get("percent_change_24h"),"change7":x["quote"]["USD"].get("percent_change_7d")} for x in d.get("data",[])]
    raise RuntimeError("Universe API unavailable; configure a free CoinGecko Demo key or CMC key.")

async def main():
    if not TG_TOKEN or not CHAT_ID: raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID.")
    limits=httpx.Limits(max_connections=16,max_keepalive_connections=8)
    async with httpx.AsyncClient(limits=limits,headers={"User-Agent":"CryptoVolumeScanner/0.1"}) as c:
        assets=await get_universe(c)
        info=await get(c,BN+"/api/v3/exchangeInfo")
        pairs={x["baseAsset"]:x["symbol"] for x in info["symbols"] if x.get("status")=="TRADING" and x.get("quoteAsset")=="USDT" and x.get("isSpotTradingAllowed",True)}
        sem=asyncio.Semaphore(8)
        async def scan(a):
            symbol=pairs.get(a["symbol"])
            if not symbol: return {**a,"status":"not_listed"}
            async with sem:
                try:
                    ks=await get(c,BN+"/api/v3/klines",{"symbol":symbol,"interval":"1h","limit":192})
                    now=int(datetime.now(timezone.utc).timestamp()*1000)
                    vols=[float(k[7]) for k in ks if int(k[6])<now]
                    if len(vols)<48: return {**a,"status":"short_history"}
                    base=vols[:-1][-167:]; med=statistics.median(base)
                    if med<=0: return {**a,"status":"bad_baseline"}
                    return {**a,"status":"ok","rvol":vols[-1]/med,"volume":vols[-1],"median":med}
                except Exception as e: return {**a,"status":"error","error":str(e)[:90]}
        rows=await asyncio.gather(*(scan(a) for a in assets))
        valid=[x for x in rows if x["status"]=="ok"]
        surge=sorted([x for x in valid if x["rvol"]>=RVOL_MIN],key=lambda x:x["rvol"],reverse=True)[:10]
        collapse=sorted([x for x in valid if x["rvol"]<=RVOL_MAX],key=lambda x:x["rvol"])[:10]
        stamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        out=[f"📊 CRYPTO VOLUME SCANNER | {stamp}",f"Top universe: {len(assets)} | Valid Binance Spot USDT markets: {len(valid)}/{len(assets)}","Hourly volume vs median of up to previous 7 days. Values are quote volume in USDT.","Volume changes alone do not prove capital inflow/outflow.","","🚀 SURGE"]
        out += [f"{x['symbol']} (#{x.get('rank') or '-'}) — {x['rvol']:.2f}x median | 1h {x['volume']:,.0f} USDT | 24h price {x.get('change24')}%" for x in surge] or ["No surge above threshold."]
        out += ["","🧊 COLLAPSE"]
        out += [f"{x['symbol']} — {x['rvol']:.2f}x median | 1h {x['volume']:,.0f} USDT | 24h price {x.get('change24')}%" for x in collapse] or ["No collapse below threshold."]
        miss=[x["symbol"] for x in rows if x["status"]!="ok"]
        out += ["","🩺 DATA HEALTH",f"Valid: {len(valid)}/{len(assets)} | unavailable/partial: {len(miss)}"]
        if miss: out.append("Not covered: "+", ".join(miss[:30]))
        out += ["","Sources: CoinGecko/CMC universe + Binance Spot OHLCV.","Starter scope: Futures/OI/Funding/Liquidations and BTC-relative strength are not yet implemented."]
        resp=await c.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",json={"chat_id":CHAT_ID,"text":"\n".join(out)[:3900],"disable_web_page_preview":True},timeout=20)
        resp.raise_for_status()
        if not resp.json().get("ok"): raise RuntimeError("Telegram rejected message.")
        log.info("Report sent. valid=%s total=%s",len(valid),len(assets))

if __name__=="__main__": asyncio.run(main())
