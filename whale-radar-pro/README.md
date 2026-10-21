# Whale Radar Pro

An English-only Windows desktop app with three primary sections: exchange connection profiles, a ranked watchlist of up to 10 Hyperliquid traders, and margin/risk sizing. The current interface uses a dark theme.

## Current implementation status
- **Hyperliquid screening:** reads the public leaderboard, then requests recent fill history for at most 15 higher-return wallets with a small concurrency cap. Missing leaderboard win rates are estimated from non-zero realized `closedPnl` values on close/liquidation fills over the last 7 days. This is a **closed-fill win-rate proxy**, not a true position-level win rate: partial exits may count as multiple fills. The UI labels it accordingly and shows the proxy sample size. API failures or no closed fills leave the metric Unknown rather than fabricating zero.
- **Public wallet alerts:** select a row and click **Watch selected wallet**. The app polls that public wallet's recent fills every 20 seconds and prompts for review when new fills appear. Monitoring is opt-in and read-only. The first poll establishes a baseline to avoid alerting on old fills already visible at startup.
- **Copy orders:** not implemented. The alert explicitly states that no order can be submitted by this build. This is not yet a complete copy-trading product.
- **Bitunix profiles:** create/edit, select, paste, and delete are supported. Secrets are stored through Windows Credential Manager (`keyring`) when available. The connection test signs a read-only request to the pending-positions endpoint using the official double-SHA256 signing procedure and runs in a background thread. It never places, edits, or cancels orders. See the [official signature guide](https://www.bitunix.com/api-docs/futures/common/sign.html) and [read-only endpoint](https://www.bitunix.com/api-docs/futures/position/get_pending_positions.html).
- **Risk sizing:** estimates notional and leverage from margin, risk amount and entry-to-stop distance. It excludes fees, slippage, funding, lot/tick sizes, exchange leverage caps and liquidation constraints.
- **Themes:** dark theme only; light-theme toggle is not yet implemented.

## Run from source
Python 3.12+ on Windows:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

## Tests

```powershell
python -m unittest discover -s tests -v
```

Tests mock network-dependent API calls; they do not require credentials or send live orders.

## Build

The GitHub Actions workflow `Windows Build` builds `WhaleRadarPro.exe` and an Inno Setup installer, then uploads both as workflow artifacts. Pushes to the rebuild branch and manual dispatch trigger the workflow. Download the artifact from the latest successful run on the [Actions page](https://github.com/shmm66/desktop-tutorial/actions).

## Repository layout
- `app.py` — compact desktop UI (three main sections)
- `radar/` — models, risk calculations, Bitunix read-only authentication, Hyperliquid screening and wallet monitor, credential profile storage
- `tests/` — deterministic unit tests
- `.github/workflows/windows-build.yml` — reproducible Windows build

## Security
Never commit API secrets or send them in chat. Use a Bitunix API key with minimum read-only permissions; never enable withdrawals for this app. Risk calculations are estimates, not guarantees of liquidation distance or exchange order validity.

GitHub Actions are pinned to full commit SHAs to satisfy repository security settings.
