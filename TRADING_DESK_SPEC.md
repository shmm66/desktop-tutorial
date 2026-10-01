# Trader Planner Pro V10 — Trading Desk Technical Specification

## Purpose
The Trading Desk is an online-first market-analysis workspace embedded in the native Windows application. Its visual target is a TradingView-style professional terminal while keeping the surrounding application native.

## Chart engine
- TradingView Advanced Chart Widget is embedded from TradingView's official widget endpoint.
- Candles, timeframes, zoom/pan, drawing toolbar, indicators, symbol search/change, date ranges, chart details and fullscreen are provided by the embedded chart.
- The chart symbol is changed by rebuilding the widget configuration with the selected symbol.
- Drawing tools remain price/time anchored because they are rendered by the chart engine rather than on a fixed application canvas.
- The application does not claim to ship TradingView's proprietary Charting Library or Trading Platform; the integration uses the official embeddable widget.

## Crypto universe
The left market browser loads the top 100 assets by market capitalization:
1. CoinGecko /coins/markets?per_page=100
2. CoinPaprika /v1/tickers?limit=100 fallback
3. Browser localStorage cache fallback

The watchlist exposes ranking, symbol, name, price and 24h percentage change. Selecting an asset opens the preferred Binance symbol in the TradingView chart.

Macro charts:
- CRYPTOCAP:BTC.D
- CRYPTOCAP:USDT.D
- CRYPTOCAP:TOTAL
- CRYPTOCAP:TOTAL2
- CRYPTOCAP:TOTAL3

Macro cards read current global market metrics from CoinGecko /global and cache the last successful snapshot.

## Forex / traditional markets
The Forex mode exposes:
- Gold: OANDA:XAUUSD
- Silver: OANDA:XAGUSD
- Copper: FXCM:COPPER
- Major FX: EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD, NZDUSD
- Dollar/indices: DXY, S&P 500, Nasdaq 100, Dow 30
- Energy: WTI and Brent
- US stocks: AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA, AVGO, JPM, BRK.B

The chart data for these instruments is supplied by the TradingView feed available to the embedded widget.

## Reliability model
The Trading Desk avoids synthetic/demo candles. If the online chart feed cannot connect, the UI exposes the connection state rather than inventing market candles. Crypto list and macro values may use the most recent cached API snapshot when the corresponding public API is temporarily unavailable.

## Refresh policy
- Crypto top-100 snapshot: on startup, mode switch and manual refresh.
- Global macro snapshot: on startup, mode switch and manual refresh.
- Chart: rebuilt on symbol/timeframe change and manual refresh.
- Status labels identify the active data path (live API, cache, or unavailable).

## Build / installer
The existing GitHub Actions pipeline remains the release source of truth:
1. Windows x64 quality checks
2. Python syntax and pytest
3. PyInstaller one-file EXE
4. startup smoke test
5. Inno Setup installer
6. silent install / uninstall smoke test
7. release assets

The V10 pipeline is pinned to the supported windows-2022 GitHub-hosted runner.