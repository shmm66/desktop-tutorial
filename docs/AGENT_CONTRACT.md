# Multi-Agent Contract

## Roles
- **Architect/Lead:** owns architecture, interfaces, cross-domain decisions and acceptance criteria.
- **UI/UX:** owns shell, navigation, visual system, RTL/LTR and accessibility.
- **Trading Domain:** owns Forex/Crypto journal models, planning, checklist, risk and analytics.
- **Market Data:** owns provider adapters, normalization, caching, session clocks and online/offline behavior.
- **Cloud/Integrations:** owns Google Drive OAuth/upload and browser integration.
- **Reports:** owns PDF/XLSX/CSV and chart generation.
- **QA:** owns tests, regression checks and release gates.
- **Release:** owns PyInstaller/Inno Setup, artifact validation and release notes.

## Contract
1. Read `AGENTS.md` and `ARCHITECTURE.md` before coding.
2. State the task scope and files likely to change before implementation.
3. Do not modify another agent's branch.
4. Do not commit secrets, credentials, local databases, tokens or personal data.
5. Preserve backward compatibility unless the task explicitly permits a breaking change.
6. Business rules belong in domain/services, not widgets.
7. External services must be mockable in tests.
8. Every new persisted field needs migration handling and validation.
9. Every new user-facing string needs a translation key.
10. Every calculation needs unit tests, including zero, negative, boundary and precision cases.
11. Every network integration needs timeout, retry policy where appropriate, stale-data indication and offline fallback.
12. Do not silently swallow exceptions. Convert technical failures to actionable user messages and log safe diagnostics.
13. PRs must contain: Summary, Design, Tests, Screenshots for UI changes, Packaging impact, Known limitations.

## Handoff format
```text
Task:
Changed:
Design decision:
Tests run:
Known limitations:
Migration/compatibility:
Next agent action:
```

## Merge gates
QA must confirm tests pass. For UI work, startup/navigation smoke must pass. For report work, a generated report must be opened/validated. For packaging work, the EXE and installer must be checked for existence and launch/install behavior on Windows CI.
