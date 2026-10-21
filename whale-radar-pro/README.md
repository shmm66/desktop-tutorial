# Whale Radar Pro

A clean Windows desktop rebuild focused on three areas: exchange connection profiles, a ranked watchlist of up to 10 Hyperliquid traders, and per-trade margin/risk sizing. Copying is not automatic.

## Current implementation status
- Hyperliquid: public leaderboard retrieval is best-effort. Missing ROI, win rate, and trade-count fields remain **Unknown** rather than being fabricated as zero. Unknown ROI or win rate excludes a trader from the performance-filtered list. The public leaderboard does not guarantee that every field needed for win-rate ranking is available.
- Bitunix: API profiles support create, edit, select, delete, and paste. The connection test now signs and sends a **read-only** request to the pending-positions endpoint using the official REST double-SHA256 procedure. It never places, edits, or cancels orders. See the [official signature guide](https://www.bitunix.com/api-docs/futures/common/sign.html) and [read-only endpoint](https://www.bitunix.com/api-docs/futures/position/get_pending_positions.html).
- Live trader position-change monitoring and copy execution are not implemented yet. The review action is a placeholder; no order is sent.
- The current UI uses a dark theme. A light-theme toggle is not yet implemented.
- API secrets must not be committed to source control. The app uses Windows Credential Manager through `keyring` when available.

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

## Build
GitHub Actions workflow `Windows Build` builds a standalone `WhaleRadarPro.exe` and an Inno Setup installer, then uploads both as workflow artifacts. Pushes to this branch and manual dispatch trigger the workflow.

## Repository layout
- `app.py` — compact desktop UI (three main sections)
- `radar/` — models, risk calculations, Bitunix read-only authentication, Hyperliquid public data adapter, credential profile storage
- `tests/` — deterministic unit tests
- `.github/workflows/windows-build.yml` — reproducible Windows build

## Risk note
Leverage calculations are sizing estimates, not a guarantee of liquidation distance or exchange order validity. Fees, slippage, funding, tick size, lot size, and venue margin rules may change the real outcome. Use API keys with the minimum required permissions and never enable withdrawals for this app.

Build workflow policy: all GitHub Actions are pinned to full commit SHAs to satisfy repository security settings.
