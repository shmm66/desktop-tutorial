# V5 Release Automation

Release automation is intentionally gated. A public release must not be created from a failing test suite.

## Pipeline

1. Run unit/domain/application tests.
2. Run architecture checks.
3. Build the Windows application.
4. Build the Windows installer.
5. Validate installer metadata and artifact presence.
6. Publish the GitHub Release.
7. Notify configured community channels (Telegram/X) using GitHub Actions secrets.

## Required secrets

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- X OAuth credentials required by the selected publisher implementation.

Secrets must never be committed to the repository or printed in workflow logs.

## Release rule

Only tagged, tested, release-ready builds are eligible for public distribution. Development branches and failed CI runs must not trigger public announcements.
