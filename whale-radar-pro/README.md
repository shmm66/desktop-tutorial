# Whale Radar Pro 2.3.0

English-only Windows desktop app for monitoring Hyperliquid traders and optionally copying fresh fills to Bitunix USDT futures with isolated margin and saved risk controls.

## New in 2.3.0
- Starts maximized/full-screen by default.
- Multiple selection in the trader table (Ctrl/Shift), up to 10 traders monitored concurrently by one polling worker and one shared risk/state ledger.
- **Copy Trade History** window with per-trade milestones: Pending, Order Confirmed, Position Opened, SL Confirmed, Closed and Failed; saved exchange identifiers, margin, leverage, stop and recorded P&L where available.
- Cumulative realized-P&L chart based only on P&L fields actually recorded in the history. Missing P&L is shown as blank rather than fabricated.
- Export full history to CSV; create a printable A4-landscape HTML statement that opens in the browser, where Print → Save as PDF is available.
- Simple whale mark in the app header.

## Auto-copy safety
Live trading is disabled by default. Before enabling it, save a Bitunix profile and explicitly confirm the one-time capital/risk setup. New fills from selected wallets are processed automatically after setup; there is no per-trade confirmation. Copy only supported COINUSDT symbols. The app refuses to change leverage/margin or open a new copied position if an existing position/order for the same symbol is detected. Isolated margin is mandatory, and a protective stop is attached and then checked against exchange position/TP-SL data.

User-defined authorized capital limits bot-tracked allocated margin; each trade uses the configured percentage of that capital. The stop target aims for a price movement corresponding to 50% of allocated margin. The aggregate risk budget reserves the planned stop risk of existing copied positions and stops new entries when the configured loss limit is reached. These controls do not guarantee a hard maximum loss: slippage, fees, funding, liquidation, API errors or exchange outages can exceed the target.

## API credentials
Use a Bitunix key with only the required futures trading permissions; never enable withdrawals or share API secrets. Secrets are stored through Windows Credential Manager when available. No live private order was submitted as part of CI.

## Tests and build
Run `python -m unittest discover -s tests -v` in `whale-radar-pro`. GitHub Actions workflow `Windows Build` builds the EXE and Inno Setup installer and uploads them as artifacts. See https://github.com/shmm66/desktop-tutorial/actions.
