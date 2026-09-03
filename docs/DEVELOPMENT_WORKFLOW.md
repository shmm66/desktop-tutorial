# V5 Development Workflow

1. Start from `v5-architecture-migration` until the foundation is accepted.
2. Every feature gets a focused branch: `feature/<area>-<short-name>`.
3. Agent reads `AGENTS.md`, `ARCHITECTURE.md`, and the relevant domain contract before editing.
4. Agent adds/updates tests with the implementation.
5. Run unit tests and a smoke test before opening a PR.
6. PR must describe architecture impact, data migration impact, user-visible changes, and rollback path.
7. QA reviews the PR independently.
8. Only the maintainer merges to `main`.
9. Windows installer is built from a tagged/release commit, not from arbitrary feature branches.

## Agent roles
- Architect: boundaries, schemas, ADRs, review.
- UI: presentation, accessibility, localization; no direct DB writes.
- Trading: Forex/Crypto domain rules and calculations.
- Market Data: provider interfaces, caching, timezone/DST behavior.
- Reports: PDF/XLSX/CSV from shared report models.
- Cloud: Drive integration, OAuth boundaries, file lifecycle.
- QA: tests, regression, startup, packaging validation.
- Release: versioning, installer, artifacts, release notes.

## Definition of Done
A task is done only when behavior is implemented, persisted data is compatible/migrated, tests cover the changed logic, localization is considered, and CI is green.
