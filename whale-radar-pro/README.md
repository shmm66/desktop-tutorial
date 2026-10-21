# Whale Radar Pro 2.2.0

An English-only Windows desktop app for screening Hyperliquid traders and optionally copying new wallet fills to Bitunix USDT-margined futures. The UI has three main sections: Bitunix connection, trader screening, and saved auto-copy capital/risk controls.

## Automatic copy-trading status

Automatic Bitunix order submission is implemented in radar/copytrade.py and wired into the main UI. It is **disabled by default**. The user must explicitly enable it in the one-time setup dialog before auto-copy starts. After enablement, fresh fills from the selected public Hyperliquid wallet are handled automatically without asking for each trade. Stopping the monitor stops future signal handling; it does not automatically close existing positions, and exchange-side stop orders remain in place.

Before the first live copy session, select/save a Bitunix API profile and select a Hyperliquid trader. Click **Start auto-copy**, set the authorized futures capital, percentage of that capital allocated per trade, cumulative loss limit, and maximum leverage, then explicitly confirm live trading. These settings persist locally and can be changed through **Edit copy settings**. The worker reloads changed settings while monitoring.

## Capital and isolated-risk controls

- **Authorized capital** caps the sum of bot-tracked allocated margin. Example: with $20 authorized capital and 20% margin per trade, an order is planned for up to $4 margin, subject to available Futures USDT, venue minimums and contract precision.
- **Per-trade margin** is limited to the user-configured percentage of authorized capital. The app does not transfer funds, add margin after entry, or deliberately use the rest of the wallet as cross collateral.
- **Isolated margin is mandatory.** For a symbol, the app refuses to change margin/leverage or open a copied position when an existing Bitunix position or pending order is detected. It requests ISOLATION, verifies the exchange response, then verifies leverage before sending an order. If an opened position is unexpectedly reported as non-isolated, the app requests an emergency close and reports an error.
- **Per-trade stop target** is designed so a move from entry to the exchange-side market stop equals approximately 50% of the position's actual allocated initial margin. Example: $4 margin implies about $2 planned stop-loss risk, before fees and execution effects. Stop placement uses the Bitunix order endpoint's attached market stop.
- **Aggregate stop-risk budget** limits combined planned stop risk across bot-tracked open positions to the remaining cumulative loss budget. As prior losses accumulate, or other open positions reserve the budget, the next position is reduced or skipped.
- **Cumulative loss circuit breaker** tracks PnL of bot-managed positions and disables new entries once the configured loss limit is reached. It attempts to close tracked positions using their Bitunix position IDs; if a close request fails, the exchange-side stop remains the fallback protection.
- **Fail-closed behavior:** invalid/unmapped symbols, unsupported Bitunix contracts, missing market prices, insufficient margin, minimum-size violations, missing order IDs, unknown fill directions, duplicate fills, unverified isolated mode, and pre-existing positions/orders cause an order to be skipped or an error to be reported.
- **Close events:** a source close is only copied against a tracked local position ID. It closes the local copied position rather than sending an unprotected opposite-side order. Source partial closes are not mirrored proportionally; a recognized source close closes the tracked copied position in full.
- **Trading scope:** only assets that map to Bitunix USDT futures symbols (COINUSDT) are eligible. Other Hyperliquid symbols (including dex-specific forms or spot-only tokens) are skipped. At most one bot-tracked position per symbol is allowed to avoid unintended pyramiding or interference with manual positions.
- **Win-rate statistics:** when leaderboard win-rate metrics are missing, the app uses a labeled seven-day closed-fill proxy. Partial exits can count as multiple fills, so it is not a verified position-level win rate.

## Important risk notice

The stop target and loss circuit breaker are risk controls, **not a guarantee of maximum possible loss**. Market gaps, slippage, latency, fees, funding, liquidation rules, an exchange/API outage, a rejected stop, or a sudden position closure can cause actual loss to exceed the planned value. The circuit breaker is checked periodically and cannot remove these risks. Do not enable live copy until credentials and settings have been reviewed.

Use a Bitunix API key with the minimum Futures permissions required for live order creation/closing. **Never grant withdrawal permission and never share API secrets in chat.** Secrets are kept through Windows Credential Manager (keyring) when available. Connection testing uses a read-only endpoint; live copy requires a separate API key with trading permissions. No private live-order test was performed as part of the build; tests must use mocks and never submit orders to an exchange.

## Run from source

Python 3.12+ on Windows. Create a virtual environment, install requirements.txt, and run python app.py.

## Tests

Run python -m unittest discover -s tests -v. Tests include deterministic position-size/stop-risk checks, aggregate risk budget limits, fill identity, trader ranking and signature verification. Network-dependent order tests should be mocked; tests must not call private trading endpoints or submit real orders.

## Build

The GitHub Actions workflow Windows Build runs tests, builds WhaleRadarPro.exe and a Windows Inno Setup installer, and uploads both as workflow artifacts. Pushes to the whale-radar-pro-rebuild branch or manual dispatch trigger the build. See the [Actions page](https://github.com/shmm66/desktop-tutorial/actions).

## Repository layout

- app.py — three-section desktop UI and automatic copy monitor.
- radar/copytrade.py — saved user settings, Bitunix signing, isolated order flow, stop sizing, deduplication, PnL tracking and circuit breaker.
- radar/bitunix.py — read-only connection test and signature helper.
- radar/hyperliquid.py and radar/monitor.py — public leaderboard and wallet fill monitoring.
- radar/credentials.py — API profile metadata and OS credential storage.
- tests/ — deterministic offline tests.
- .github/workflows/windows-build.yml — Windows build pipeline.
