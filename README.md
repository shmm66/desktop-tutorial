# Trader Planner Pro 2.0

Windows 11 desktop trading planner with a single Home dashboard and hamburger navigation.

## Features
- Home dashboard: trade count, win rate, net R, P&L, discipline and recent trades.
- 30-day routine starting from the current day; editable tasks and drag-to-reorder.
- Fixed core routine: 09:00–13:00 MARK UP and 15:30–19:00 TRADING.
- Trading Plan with blank user-editable fields.
- Pre-trade checklist with reset.
- Separate Forex and Crypto journals with different field sets.
- Screenshot upload to Google Drive using the user's own OAuth credentials.
- Position sizing / risk calculator.
- Live Sydney, Tokyo, London, New York and Crypto clocks with DST-aware time zones.
- Forex Factory page with bull-vs-bear visual and browser launch button.
- Persian/English and Dark/Light settings.
- Local data stored in `%USERPROFILE%\TraderPlannerPro`.

## Google Drive
Create a Google OAuth Desktop application, download `credentials.json`, then select it in Settings. The first upload opens Google's consent flow. The token is stored locally for future uploads.

## Windows build
GitHub Actions builds both `TraderPlannerPro.exe` and `TraderPlannerPro_Setup.exe` as artifacts after a push to `main` or a manual workflow run.
