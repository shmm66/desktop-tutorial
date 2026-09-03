# V5 Architecture Migration Plan

## Phase 0 — Foundation (current)
- [x] Create `app/` package boundary.
- [x] Centralize configuration.
- [x] Add SQLite persistence and schema versioning.
- [x] Separate Forex and Crypto domain models.
- [x] Add service layer and risk calculations.
- [x] Add UI shell with stable entry point.
- [x] Add smoke/unit tests.
- [x] Move CI packaging to `app/main.py`.

## Phase 1 — Data model
- [ ] Add migrations directory and migration runner.
- [ ] Add repositories for profiles, accounts, trades and daily plans.
- [ ] Add immutable trade event/audit records.
- [ ] Add import/export data contract.

## Phase 2 — Product shell
- [ ] Replace temporary tabs with production shell + hamburger navigation.
- [ ] Add Persian/English localization and RTL/LTR switching.
- [ ] Add Home dashboard cards and session clock.
- [ ] Add responsive layouts and accessibility keyboard navigation.

## Phase 3 — Trading domains
- [ ] Complete Forex journal fields: pair, lot, pip value, spread, commission, swap, session, setup.
- [ ] Complete Crypto journal fields: exchange, quantity, leverage, margin, fees, funding, liquidation.
- [ ] Add pre-trade checklist and trading plan versioning.
- [ ] Add risk manager with validation against daily/weekly limits.

## Phase 4 — Market data
- [ ] Provider interface with caching and offline fallback.
- [ ] Forex/Crypto quotes and percentage changes.
- [ ] Session clock with timezone/DST handling.
- [ ] Forex Factory browser integration; do not scrape without permission.

## Phase 5 — Evidence and reports
- [ ] Screenshot attachments stored locally with stable IDs.
- [ ] Optional Google Drive upload through OAuth; never store credentials in source.
- [ ] PDF/Excel/CSV reports from one shared report model.
- [ ] Monthly/weekly performance charts and trade statistics.

## Phase 6 — AI and QA
- [ ] Agent interfaces for Journal Analyst, Risk Guardian, Psychology Coach and Weekly Review.
- [ ] AI features opt-in, explainable and never able to place trades.
- [ ] Unit, integration, UI smoke and installer tests.
- [ ] Crash-safe backups and database integrity checks.

## Phase 7 — Release
- [ ] Signed Windows build.
- [ ] Installer upgrade/uninstall tests.
- [ ] Versioned release notes.
- [ ] Final Windows 11 installer only after all release gates pass.

## Non-negotiable architecture rules
1. UI never executes SQL directly.
2. Forex and Crypto remain independent domains.
3. External market providers are adapters behind interfaces.
4. Reports consume a shared read model, not UI widgets.
5. Credentials/tokens stay outside Git.
6. Every feature has tests and a rollback path.
7. `main` receives changes through reviewed pull requests.
