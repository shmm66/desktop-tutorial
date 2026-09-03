# V5 Next Phase Roadmap

## Quality gate
- Keep CI green before feature work is promoted.
- Financial calculations use Decimal and explicit rounding policies.
- SQLite connections have explicit lifecycle ownership and Windows-safe cleanup.

## Domain/Application
- Forex: pip, lot, spread, swap, sessions, risk and journal entities.
- Crypto: spot/futures, leverage, margin, funding, liquidation and journal entities.
- Application services must depend on domain contracts/repositories, not UI code.

## UI
- Modern responsive desktop shell.
- Home dashboard with configurable cards.
- Hamburger navigation with only Home visible in the primary shell.
- Persian/English localization.

## Trading workflow
- Daily planner.
- Trading plan.
- Pre-trade checklist.
- Forex journal and Crypto journal as independent modes.
- Forex calculator and risk manager.

## Market data
- Session clock.
- Internet-backed calendar/market data.
- Forex Factory tab as an external web view/link.
- Context-aware market ticker: crypto mode shows top 10 crypto plus BTC/USDT dominance; forex mode shows major FX pairs, gold, silver, copper, oil and selected leading equities.

## Reporting
- Monthly analytics on Home.
- PDF/Excel/CSV exports with trader profile.
- Charts included in reports.
- Google Drive image upload integration with user-controlled OAuth.

## Community and release
- GitHub Discussions and issue templates.
- Telegram support @Hadimm66.
- Optional X/Telegram release announcements through Actions secrets.
- Windows 11 QA and installer validation before public release.

## Ownership
Copyright © Seyed Hadi Mir Mohammad (سید هادی میر محمد). The project's license should explicitly preserve attribution while allowing the chosen open-source fork/contribution model.
