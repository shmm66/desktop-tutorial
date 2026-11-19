# Crypto Volume Scanner — Telegram Bot

Read-only scheduled scanner; no exchange account keys, wallet access, order placement or transfers.

## Current starter
- Retrieves up to 100 market-cap-ranked assets from CoinGecko; falls back to CoinMarketCap if configured.
- Matches them to Binance USDT Spot markets.
- Compares the latest completed 1h quote-volume candle with the median of up to the previous 7 days.
- Sends surge/collapse candidates and coverage/data-health details to Telegram hourly.

## Configure GitHub Actions Secrets
In repository Settings → Secrets and variables → Actions, add:
- `TELEGRAM_BOT_TOKEN`: BotFather token (never commit or send in chat).
- `TELEGRAM_CHAT_ID`: numeric ID of the private chat. Send `/start` to your bot first; obtain the ID from Telegram `getUpdates` or a trusted bot-management method.
- Optional `COINGECKO_DEMO_API_KEY`: free Demo key, recommended.
- Optional `COINMARKETCAP_API_KEY`: fallback market universe provider.

Then open Actions, enable workflows if prompted, and run **Crypto Volume Telegram Scanner** once using Run workflow. Later runs are scheduled hourly (GitHub schedule is best-effort).

## Limitations — not the complete research spec
- Current volume scanner covers Binance USDT Spot only; coverage is explicitly reported.
- Derivatives volume, OI, funding, liquidations, direct Coin/BTC pairs, BTC relative-strength calculations, historical universe membership, persistent history, deduplication, weekly reports and backtesting are not implemented in this starter.
- The baseline is a simple rolling median, not seasonality-adjusted.
- Do not treat a volume anomaly as proof of capital inflow/outflow or as a trade instruction.

Keep all credentials in GitHub Actions Secrets. Never put secrets in source files or logs.
