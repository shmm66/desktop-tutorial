# Trader Planner Pro — V5 Foundation

## Goal
Build a maintainable Windows 11 trading workspace. The application must be modular, testable, local-first, and safe to extend without returning to a monolithic Python file.

## Architecture rules
- `app/core`: infrastructure and cross-cutting concerns only.
- `app/domains`: business rules. Forex and Crypto remain separate domains.
- `app/services`: application use-cases; UI never owns business calculations.
- `app/integrations`: external systems such as market APIs, browser, and Google Drive.
- `app/reports`: report generation from domain/report DTOs; PDF and Excel share the same source model.
- `app/ui`: presentation only; views call services and render state.
- `tests`: unit, integration, and smoke tests.

## Data rules
SQLite is the local source of truth for user-entered data. Schema changes require migrations. Dates are stored in ISO format; monetary values use Decimal-safe serialization. Never store API keys in the database unless explicitly encrypted and required.

## Domain boundaries
Forex and Crypto journals have distinct schemas and services. Shared concepts (trade id, timestamps, notes, screenshots, R result) may use common primitives, but market-specific fields must remain in their own domain models.

## UI rules
One Home screen is visible at startup. Secondary features live behind a hamburger menu. Persian is RTL and English is LTR. The UI must remain responsive while network requests execute in background services.

## Release rules
No merge to `main` without CI. CI must run tests and a Windows packaging check. Installer builds are versioned and must be reproducible.

## V5 phases
1. Core/database/repository foundation.
2. Domain services and journal persistence.
3. Modern shell and Home dashboard.
4. Forex/Crypto journals and screenshots.
5. Risk, checklist, planner and analytics.
6. Market data, sessions and Forex Factory browser tab.
7. Reports and Drive integration.
8. Localization, accessibility, QA and Windows installer.
