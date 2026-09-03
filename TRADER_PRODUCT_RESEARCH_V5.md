# Trader Planner Pro — V5 Product Research & Build Blueprint

Research date: 2026-09-03

This document translates trader-community feedback and open-source trading-journal patterns into the product roadmap. It is a product/engineering blueprint, not financial advice.

## Research signals

### Trader community
- Reddit day traders repeatedly emphasize low-friction journaling, post-trade reflection, execution quality, recurring mistake detection, and psychology rather than collecting endless fields.
- Forex traders commonly record entry reason, risk, emotion, mistakes, screenshots, and whether they would take the trade again.
- Community feedback also favors daily plans, setup-specific plans, automatic/bulk trade import, flexible filtering, and reviewing performance by session, weekday, setup, and instrument.
- Crypto traders specifically need fees, funding, leverage, margin, liquidation price, and coin-level performance.

### Open-source products
- eJournal demonstrates local-first privacy, FIFO fill matching, P&L calendar, per-trade candlestick charts, sortable logs, CSV import, and light/dark themes.
- Tradicted demonstrates multiple portfolios, rule-based Trading Plan/checklist, analytics, psychology tags, inline trade editing, and offline SQLite storage.
- RR Metrics demonstrates screenshot attachments with markup, P&L calendar/heatmaps, advanced statistics, and local-first storage.
- Deltalytix demonstrates broker/statement imports plus AI-assisted CSV field mapping and AI-agent-oriented analytics.
- Community-built journals increasingly combine psychology analysis, live prices, setup/session/weekday breakdowns, and prop-firm compliance metrics.

## V5 product principles
1. Home is the command center; other pages live behind the hamburger menu.
2. Journal entry must be fast enough to finish in under a minute for the core fields.
3. Advanced fields are collapsible, not forced on every trade.
4. Forex and Crypto have separate schemas and analytics.
5. Local-first by default. Cloud features are opt-in.
6. No trading signal generation. AI analyzes the user's own data and notes.
7. Every important number is traceable to source trade records.
8. Export must be professional enough to archive as a work record.
9. UI must be calm, fast, keyboard-friendly, and RTL/LTR correct.
10. Network failures never block journaling or opening the app.

## V5 modules

### Home
- Large session clock board with DST-aware Sydney/Tokyo/London/New York.
- Current session indicator and countdown.
- Today's routine progress.
- Today's P&L, R, trades, win rate, discipline score.
- Daily loss/risk guard.
- Equity curve mini-chart.
- Calendar heatmap mini-view.
- Best/worst setup cards.
- Recent trades.
- Bottom ticker: mode-aware Forex or Crypto instruments.
- Market mode switch persists globally.

### Journal — Forex
Core: date/time, pair, buy/sell, entry, stop, target, exit, lots, risk %, risk $, R:R, result R, P&L, setup, timeframe.
Advanced: session, spread, commission, pips risk, pips result, market structure, liquidity, BOS/CHoCH, FVG/OB/custom setup tags, news event, execution grade, emotion, mistake, lesson, pre/post screenshots, notes.

### Journal — Crypto
Core: date/time, symbol, long/short, exchange, spot/futures, entry, stop, target, exit, position size, risk %, risk $, leverage, margin, R:R, result R, P&L.
Advanced: fees, funding, liquidation price, realized/unrealized P&L, timeframe, setup, market structure, liquidity, emotion, mistake, lesson, pre/post screenshots, notes.

### Import
- Generic CSV mapper.
- Preview before commit.
- Duplicate detection.
- Validation report.
- Save reusable mappings by broker/exchange.
- MT5/MT4 CSV/HTML statement support as a staged adapter.
- Future adapters: cTrader, Binance, Bybit, Interactive Brokers, etc.

### Analytics
- Net P&L and Net R.
- Win rate, average win/loss, expectancy, profit factor.
- Max drawdown and recovery.
- Equity curve and daily P&L calendar.
- Performance by setup, session, weekday, hour, symbol, direction, timeframe.
- R-multiple distribution.
- Streaks.
- Execution-quality statistics.
- Psychology-to-performance correlation.
- Rule-adherence score.
- Risk violations and revenge/overtrade flags.

### Trading Plan
- Multiple named plans/setups.
- Rule sections: market conditions, allowed instruments, entry, invalidation, stop, target, management, no-trade conditions, risk rules, psychology rules.
- Each journal trade can reference one plan.
- Versioned plan history.

### Checklist
- Pre-market checklist.
- Pre-trade checklist.
- Post-trade checklist.
- Configurable per market and setup.
- Score and rule-violation log.

### Market sessions
- Large visual clocks.
- User timezone + UTC.
- DST-aware session boundaries.
- Session overlap highlighting.
- Market holiday/news notes can be added later.

### Forex Factory
- Dedicated tab/page with external browser launch.
- Do not scrape or republish content without respecting the site's terms.
- Use the network only to open the official page and optionally show a lightweight embedded browser if technically/legal constraints permit.

### Reports
- PDF professional report with user profile, period, market, statistics, charts, trade table, setup breakdown, psychology summary, risk compliance, and lessons.
- Excel workbook with Profile, Trades, Analytics, Daily Summary, Setup Analysis, and Equity Curve sheets.
- CSV raw export.
- Report naming includes trader name, market, and date range.
- Report templates should be printable and suitable for archiving.

### Profile
- Full name, professional title, country, timezone, trading style, broker/exchange, account type, base currency, starting balance, optional avatar/logo, report footer.
- Never require sensitive credentials.

## Internal AI agents (optional, user-controlled)

These should analyze user-owned data only. They should never place trades or give personalized financial instructions.

1. Journal Analyst — finds recurring patterns in setup/session/symbol/results.
2. Risk Guardian — flags breaches of user-defined risk limits.
3. Psychology Coach — detects FOMO, revenge, fear, greed, overtrading, and discipline signals from the user's notes.
4. Execution Reviewer — compares planned vs actual entry/SL/TP and grades execution.
5. Weekly Review Agent — produces a concise weekly review with wins, leaks, and next-week process goals.
6. Report Builder — converts selected period data into a polished PDF/Excel narrative.

AI should be disabled by default if no API key is configured. The application remains fully functional without AI.

## Architecture recommendation

The current Tkinter prototype should not be expanded indefinitely. For the polished V5 UI, migrate to a modern Windows desktop stack (Electron + React + TypeScript + SQLite, or .NET/WPF/WinUI). Keep the data layer portable so the user's SQLite database can be backed up and migrated.

Recommended layers:
- UI: React + TypeScript + Tailwind/shadcn-style components.
- Desktop shell: Electron or WinUI/WPF.
- Data: SQLite with migrations.
- Charts: Recharts/ECharts.
- PDF: ReportLab or a browser print pipeline.
- Excel: openpyxl/xlsxwriter.
- Images: local attachments + optional Google Drive sync.
- Market data: pluggable providers with caching and graceful offline fallback.

## Quality gates before shipping Installer
- App starts cleanly on a clean Windows 11 VM.
- No console window for normal use.
- Persian RTL and English LTR verified screen-by-screen.
- Journal create/edit/delete/search/filter verified for both markets.
- Database backup/restore tested.
- PDF and Excel exports opened successfully.
- Screenshot attachment and Google Drive opt-in tested.
- Network-offline behavior tested.
- Installer uninstall/reinstall tested.
- No API keys or credentials committed to the repository.
- Smoke tests cover startup, new trade, edit trade, export, language switch, and market switch.
