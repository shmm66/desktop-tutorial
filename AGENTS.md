# AGENTS.md — Trader Planner Pro

## Mission
Build a polished, reliable Windows 11 trading workspace for discretionary traders. The app must feel like a lightweight trading terminal, not a collection of forms.

## Non-negotiable product rules
1. Home is the primary screen. Secondary modules are reached through the hamburger menu.
2. Persian and English are first-class languages. RTL must be correct in Persian; do not hard-code user-facing strings.
3. Forex and Crypto journals are separate domains with separate schemas, validation and analytics. Do not implement them as one generic form with a market dropdown.
4. User data is local-first. Network features must degrade gracefully when offline.
5. Never store API keys, OAuth client secrets, refresh tokens, or credentials in Git.
6. Exports are user-owned records: PDF, XLSX and CSV must include profile metadata, date range, market and relevant charts where technically possible.
7. Every destructive action requires confirmation. Saving should be explicit and reliable.
8. UI code must not directly manipulate database internals or HTTP clients. Use services/repositories.
9. Time/session logic must be timezone-aware and DST-aware.
10. Financial calculations must use Decimal where precision matters and must have tests.

## Architecture rules
- Prefer a modular Python desktop architecture with clear domain/service/UI boundaries.
- Keep modules small and testable.
- Use dependency injection for external services where practical.
- Define interfaces around market data, cloud storage, browser launching and reporting.
- Do not introduce a new dependency unless its purpose and Windows packaging impact are understood.

## Agent workflow
- Read `ARCHITECTURE.md` and `docs/AGENT_CONTRACT.md` before changing code.
- Work on a dedicated branch. Never push directly to `main` unless explicitly instructed by the maintainer.
- One logical feature per branch/PR.
- Add or update tests for behavior changes.
- Run syntax checks and the relevant test suite before opening a PR.
- Do not rewrite unrelated files or revert another agent's work.
- If architecture must change, update `ARCHITECTURE.md` in the same PR.
- If a requirement is ambiguous, document the assumption in the PR rather than silently inventing behavior.

## Definition of Done
- Feature works in both Persian and English where applicable.
- No blocking UI/network call on the main UI thread.
- Error states are user-readable.
- Data survives app restart.
- Tests cover critical logic and regressions.
- Windows packaging remains reproducible.
- PR description lists changed modules, tests run, known limitations and migration impact.

## Security
Treat imported journal screenshots, links and cloud credentials as untrusted input. Validate file paths, restrict uploads to intended folders, and never log secrets.
