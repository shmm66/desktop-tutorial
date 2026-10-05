# Trader Planner Pro — Trading Desk / TradingView Pro

## هدف
صفحه Trading Desk در پوسته بومی Windows 11 باقی می‌ماند، اما برای تست دقیق بازار یک حالت TradingView Pro ارائه می‌کند. این حالت از ویجت رسمی TradingView Advanced Chart در یک پنجره دسکتاپ pywebview استفاده می‌کند؛ بنابراین کندل‌ها از منبع نمودار TradingView می‌آیند و برنامه برای نمایش نمودار، OHLC مصنوعی تولید نمی‌کند.

## TradingView Pro
برای تست دقیق و مقایسه UI، مسیر TradingView Pro مستقیماً صفحه رسمی TradingView Chart را داخل پنجره دسکتاپ Edge WebView باز می‌کند:

https://www.tradingview.com/chart/

نماد و interval از داخل Trader Planner Pro به URL رسمی TradingView منتقل می‌شوند. این روش به‌جای بازسازی رابط TradingView با کد دست‌ساز، خود ترمینال رسمی را نمایش می‌دهد و برای بررسی کندل، مقیاس زمانی، Drawingها، Replay، Symbol Search و سایر رفتارهای نمودار مناسب‌تر است.

ویژگی‌های دقیق وابسته به حساب و فید TradingView هستند؛ برنامه هیچ OHLC مصنوعی تولید نمی‌کند و داده نمودار در این مسیر از خود TradingView می‌آید.

## بازارها و نمادهای پیش‌فرض

### Crypto
- BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT, ADAUSDT, DOGEUSDT, AVAXUSDT, LINKUSDT, TRXUSDT
- BTC Dominance: CRYPTOCAP:BTC.D
- USDT Dominance: CRYPTOCAP:USDT.D
- Total Market: CRYPTOCAP:TOTAL
- Total2 / Total3

### Forex / Macro / Stocks
- Gold: OANDA:XAUUSD
- Silver: OANDA:XAGUSD
- Copper: FXCM:COPPER
- Major FX: EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD, NZDUSD
- DXY: TVC:DXY
- S&P 500: SP:SPX
- Nasdaq 100: NASDAQ:NDX
- Dow: DJ:DJI
- WTI / Brent
- AAPL, MSFT, NVDA, AMZN, META, TSLA, GOOGL, JPM

این‌ها فقط preset هستند؛ Symbol Search خود TradingView برای جستجوی سایر نمادها فعال است.

## دقت زمانی و کندل
- بازه زمانی مستقیماً به intervalهای TradingView نگاشت می‌شود: 1m, 3m, 5m, 15m, 30m, 1H, 4H, 1D, 1W, 1M.
- زمان نمایش روی exchange تنظیم شده تا timezone با بازار همان نماد هماهنگ شود.
- برنامه در این حالت کندل‌سازی، resample یا interpolation دستی انجام نمی‌دهد.
- دسترسی real-time هر بازار وابسته به data entitlement / feed در TradingView است؛ در صورت نبود دسترسی، نباید برنامه آن را به عنوان live بدون منبع کافی گزارش کند.

## Native fallback
فایل native_trading_desk.py همچنان در پروژه باقی است و برای مسیر native بدون WebView نگهداری می‌شود. این مسیر برای smoke test و fallback داخلی مفید است، ولی TradingView Pro مسیر مرجع تست دقت کندل‌ها و رفتار رابط TradingView است.

## Home / Glass / AI / Journal / Weekly
- Windows Acrylic/Mica در glass_theme.py
- ساعت دیجیتال اصلی + چهار ساعت سشن روی Home
- Snapshot صفحه اول شامل زمان محلی، اجرای کارهای امروز، پیشرفت هفته، Net R هفته و وضعیت AI Agent
- Journal مستقل برای هر profile/market
- Weekly Planner با جابه‌جایی هفته و ورود مستقیم به روز
- AI Command Center با Master Agent، Form Coach، Strategy Coach، Psychology Coach، Routine Coach، Academy Tutor و Product Strategist
- Google/Gmail Statement برای گزارش ژورنال

## Build
Workflow:
1. self-hosted Windows x64 runner
2. bootstrap isolated Python 3.14.8
3. syntax checks
4. pytest
5. PyInstaller one-file EXE
6. EXE self-test
7. Inno Setup installer
8. verified artifact upload
