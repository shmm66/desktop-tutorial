# Trader Planner Pro — Architecture

## 1. Target architecture
Trader Planner Pro is a local-first Windows 11 desktop application with a modular domain/service architecture. The UI is a shell around stable application services; it is not the source of business logic.

```text
UI Shell
  ├─ Home / Dashboard
  ├─ Daily Planner
  ├─ Trading Plan
  ├─ Checklist
  ├─ Forex Journal
  ├─ Crypto Journal
  ├─ Risk Manager
  ├─ Sessions / Market Clock
  ├─ Forex Factory
  ├─ Analytics
  ├─ Reports
  └─ Settings / Profile
        │
Application Services
        │
Domain Models + Validation + Calculators
        │
Repositories / Persistence
        ├─ SQLite/local files
        └─ encrypted/secure OS storage for tokens when required
        │
External Adapters
 ├─ Market Data
 ├─ Google Drive
 ├─ Browser / Forex Factory
 └─ Report generation
```

## 2. Proposed repository layout
```text
app/
  main.py
  core/          # config, database, models, events, errors
  ui/             # shell and feature screens
  domains/
    forex/        # Forex entities, validation, analytics
    crypto/       # Crypto entities, validation, analytics
    planning/     # daily routine, trading plan, checklist
    risk/         # position sizing and risk rules
  services/       # orchestration/use cases
  market_data/    # providers, normalization, caching
  integrations/   # Google Drive, browser
  reports/        # PDF/XLSX/CSV and chart rendering
  i18n/           # translation catalogs and RTL helpers
  storage/        # repositories and migrations
tests/
  unit/
  integration/
  smoke/
assets/
docs/
.github/workflows/
```

The existing v3/v4 files are transitional compatibility artifacts. New features should go into modules, then the legacy entry points can be retired after parity is verified.

## 3. Core domain separation
### Forex
Entities include trade, pair, session, lot size, pip distance/value, spread, setup, market structure, news context, risk and execution review.

### Crypto
Entities include trade, symbol, spot/futures, side, exchange, leverage, margin, fees, funding rate, liquidation price, setup, market structure, risk and execution review.

A shared analytics layer may consume normalized trade outcomes, but source-domain fields remain distinct.

## 4. Persistence
Use SQLite for structured local data with migrations. Suggested top-level tables:
- user_profile
- daily_tasks
- trading_plan
- checklist_items
- forex_trades
- crypto_trades
- attachments
- settings
- market_snapshots

Store attachment metadata separately from trade records. Files should live in an app-controlled data directory or configured Google Drive folder.

## 5. External data
Market data providers are adapters. The UI only consumes normalized snapshots. Providers must expose timestamps, source and stale/offline status. Cache the last successful snapshot and show its age.

Session clocks use IANA time zones and calculate DST dynamically. Never hard-code London/New York UTC offsets.

Forex Factory is opened in the user's browser; do not scrape or bypass site protections. Any calendar data displayed inside the app must come from a permitted source/API.

## 6. Google Drive
Use OAuth Desktop flow. Credentials are selected by the user and must never be committed. Tokens belong in OS-appropriate secure storage. Upload operations must be asynchronous, cancellable where practical, and report progress/errors.

## 7. Reporting
A report service builds a snapshot from repositories, then renders:
- profile page
- period summary
- KPI cards
- equity curve
- R distribution
- win/loss analysis
- setup/session/day breakdown
- trade table
- selected screenshots

PDF and XLSX are generated from the same report model so numbers cannot diverge between formats.

## 8. UI/UX
Home contains only high-value information: today's plan, current session, performance KPIs, risk state, recent trades, mini equity chart and market ticker. Secondary screens live in the hamburger menu.

Use reusable components: KPI card, section card, data table, validated field, date range picker, market selector, chart card and confirmation dialog.

Persian uses RTL layout and Persian labels; English uses LTR. Translation keys must be centralized.

## 9. Concurrency and reliability
Never perform HTTP, Google Drive upload, PDF generation or large imports on the UI thread. Use worker tasks and marshal results back to the UI. Every background task needs success, failure and cancellation handling.

## 10. Testing strategy
- Unit: calculations, validation, session/DST logic, analytics.
- Integration: SQLite repositories, import/export, cloud adapter with mocks.
- UI smoke: startup, navigation, language switch, journal save/reload.
- Packaging smoke: EXE launches on a clean Windows runner and installer creates/uninstalls the app.

Critical financial calculations require deterministic tests with edge cases.

## 11. Release strategy
Semantic versioning. Every release must pass tests and Windows packaging. Release artifacts are immutable and include SHA256 checksums. Do not ship a build that has not passed startup smoke testing.
