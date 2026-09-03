# Final Release Gates

The product must NOT be labelled Final or ship a public installer until every gate below passes.

## Functional
- [ ] Home dashboard loads without crash
- [ ] Hamburger navigation is the only secondary navigation on Home
- [ ] Persian and English UI are complete, including RTL layout
- [ ] Daily planner is editable/reorderable for a full month
- [ ] Trading Plan and pre-trade Checklist persist
- [ ] Forex Journal has Forex-specific fields and screenshot attachments
- [ ] Crypto Journal has Spot/Futures-specific fields and screenshot attachments
- [ ] Forex Calculator covers risk, lots, pip value and R:R
- [ ] Risk Manager persists rules and validates position sizing
- [ ] Session clock displays Sydney/Tokyo/London/New York clearly
- [ ] Forex Factory opens through the user's browser/in-app web surface
- [ ] Market mode filters the ticker to Forex or Crypto universe
- [ ] Reports export PDF, XLSX and CSV with trader profile and charts
- [ ] Google Drive folder integration is explicit and permission-safe
- [ ] Offline personal data remains available
- [ ] Online market data failure degrades gracefully

## Quality
- [ ] Unit tests pass
- [ ] Repository/service integration tests pass
- [ ] Startup smoke test passes
- [ ] Packaging test passes
- [ ] Clean Windows 11 install test passes
- [ ] Upgrade from previous version is tested
- [ ] Uninstall leaves user data only when explicitly chosen
- [ ] No API keys or secrets are bundled

## Release
- [ ] Version and build number are visible
- [ ] Installer is signed when a signing certificate is available
- [ ] SHA-256 checksum is published
- [ ] Release notes are published
- [ ] GitHub Actions artifact is downloadable
- [ ] Installer was manually launched on Windows 11
