# Whale Radar Pro

A clean, isolated Windows desktop rebuild focused on three areas: exchange connection profiles, a ranked watchlist of up to 10 Hyperliquid traders, and per-trade margin/risk sizing. Alerts are informational; copying a trade always requires explicit user confirmation.

## Scope and safety
- Hyperliquid public leaderboard scanning is best-effort and must show data freshness/errors honestly.
- Bitunix API profile management supports create, edit, select, delete, and paste. Private API connectivity must be validated against current Bitunix signing documentation before enabling trading.
- No automatic order is sent by this initial build. Trade-copy actions are confirmation-only placeholders until exchange-specific execution tests pass.
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
- `radar/` — models, risk calculations, Hyperliquid public data adapter, credential profile storage
- `tests/` — deterministic unit tests
- `.github/workflows/windows-build.yml` — reproducible Windows build

## Risk note
Leverage calculations are sizing estimates, not a guarantee of liquidation distance or exchange order validity. Verify tick size, lot size, fees, funding, and exchange margin rules before trading.