# Whale Radar Pro — Windows build pipeline

This document describes how the English-only **Whale Radar Pro** Windows desktop
application is built and published. It is separate from the Trader Planner Pro
application that also lives in this repository.

## 1. Why the build looks the way it does

Whale Radar Pro is packaged for Windows x64 with PyInstaller (one-file EXE) and
Inno Setup (installer). The build runs on a **self-hosted Windows runner**, and
the runner keeps a local copy of the baseline application source tree under:

```
C:\Users\Public\Documents\WhaleRadarProBuild\WhaleRadarPro_BitunixOnly
```

Everything the build produces from that tree is driven by **one reviewed source
payload** stored on the `whaleradarpro-v150-payload` branch under
`build-source-patch/`.

### The problem this replaced

Until 1.5.0 the build assembled the application from four separate base64
archives and then rewrote the result with roughly a dozen in-workflow text and
AST patches. That design had several failure modes:

| Failure mode | Consequence |
| --- | --- |
| A payload archive with a wrong CRC (`v1.4.1`) | `Expand-Archive` could abort the build |
| A payload file containing a syntax error (`whaleradar/http.py`, `whaleradar/trade_manager.py`) | The file only worked because the YAML repaired it at package time |
| The workflow expanded the reviewed `http.py` and then immediately overwrote it with the older baseline copy | The reviewed transport was silently discarded and shipped as dead code |
| The workflow deleted `tests/test_trader_discovery.py` | A failing test was hidden instead of fixed |
| The version was patched independently in five places | Version drift between the EXE, the installer and the documentation |

### The rules that apply now

1. **The payload is the reviewed source.** The build never patches application
   source. Everything that ships is in the payload archive and is covered by the
   test suite.
2. **One payload, one checksum.** `build-source-patch/v1.5.0.manifest.json`
   lists the archive parts and the SHA-256 of the reconstructed archive. The
   workflow refuses to build when the checksum does not match.
3. **One version definition.** `BUILD_VERSION.txt` inside the payload defines
   the version. The workflow verifies that `whaleradar/__init__.py`,
   `setup.iss` and the payload itself agree, and fails the build when they do
   not.
4. **No test is deleted.** The full suite runs, including
   `tests/test_trader_discovery.py`.
5. **Every module must import.** `tests/test_import_smoke.py` imports each
   module of the package, so a missing symbol fails the build instead of the
   installed application.

## 2. Repository layout of the payload

```
build-source-patch/
  v1.5.0.manifest.json        # version, SHA-256, ordered list of archive parts
  v1.5.0.part00.txt           # base64 of one slice of the source archive
  ...
  v1.5.0.part10.txt
```

Each part file contains the base64 text of one slice of the source archive. The
workflow concatenates the decoded parts, decodes the result, verifies the
SHA-256 and expands the archive over the baseline tree.

To rebuild the payload:

```powershell
# From a checkout of the corrected source tree
python -m zipfile -c v1.5.0-source.zip app.py whaleradar tests docs `
  BUILD_VERSION.txt CHANGELOG.md README_EN.md START_HERE_EN.txt requirements.txt setup.iss
```

The archive must be built deterministically (fixed timestamps) so the SHA-256
only changes when the source changes.

## 3. What the payload contains

| Path | Purpose |
| --- | --- |
| `app.py` | The Tk application and its three screens |
| `whaleradar/http.py` | The HTTP transport, with the trading-safety rules |
| `whaleradar/hyperliquid.py` | Read-only Hyperliquid public data client |
| `whaleradar/traders.py` | Leaderboard ranking and the trader service |
| `whaleradar/copycalc.py` | Copy-trade sizing math (exact decimal arithmetic) |
| `whaleradar/risk_profile.py` | Automatic guardrails derived from account equity |
| `whaleradar/rtl.py` | Persian display adapter for Tk |
| `whaleradar/trade_manager.py` | Position utility and Excel/PDF reporting |
| `tests/` | The full unit test suite |

The modules that are **not** in the payload
(`analysis.py`, `backtest.py`, `bitunix.py`, `evm.py`, `exchanges.py`,
`marketdata.py`, `models.py`, `notifications.py`, `risk.py`, `storage.py`) come
from the runner's baseline tree. They are compiled and imported by the build, so
a missing symbol in the baseline is reported as a build failure.

### Compatibility with the baseline transport

The payload replaces the baseline `whaleradar/http.py`. Before the payload is
applied, the build copies the baseline module to
`whaleradar/_http_legacy.py`. The reviewed `whaleradar/http.py` forwards any
attribute it does not define to that legacy module, so a helper the baseline
provided stays importable and cannot break an import elsewhere in the package.

## 4. Pipeline stages

| Stage | What it does | Fails when |
| --- | --- | --- |
| Prepare the reviewed source | Waits for the baseline tree, preserves the legacy transport, downloads and verifies the payload, expands it, verifies the version and the required files | The baseline is missing after the wait, the checksum differs, the version disagrees, a required file is missing |
| Diagnose public endpoint reachability | Probes the Hyperliquid and Bitunix public endpoints and reports the result | Never — this step is informational (`continue-on-error`) |
| Inspect safe API UI integration points | Prints the credential-UI anchors of the shipped source for review | The source file is missing |
| Install dependencies | Creates a virtual environment and installs `requirements.txt` plus PyInstaller, trying several PyPI mirrors | Every mirror fails |
| Test and package | Compiles every module, generates the icon, runs the full test suite, builds the one-file EXE | A module does not compile, a test fails, PyInstaller fails, the EXE is missing or implausibly small |
| Build and verify the installer | Compiles `setup.iss` with Inno Setup | Inno Setup is unavailable, the compile fails, the installer is missing or implausibly small |
| Stage and publish | Copies the artifacts, writes the SHA-256 file, creates or updates the draft release and publishes it | A verified artifact is missing, or the release is already published |

## 5. Release procedure

1. Prepare the corrected source tree and the payload on a feature branch.
2. Rebuild the payload archive, recompute the SHA-256 and update
   `PAYLOAD_SHA256` in `.github/workflows/whaleradar-build.yml`.
3. Push the payload branch and the feature branch.
4. Run the workflow (`workflow_dispatch`) and confirm every stage passed.
5. The release `whaleradarpro-v1.5.0` is created and published automatically.

A published release is immutable: the workflow refuses to overwrite it and asks
for a new version tag instead.

## 6. Known limitations

- The baseline source tree still only exists on the self-hosted runner. Until it
  is committed to this repository, a rebuild depends on that machine. The
  pipeline now fails with an actionable message instead of silently building
  from an incomplete tree.
- Dependency ranges are bounded but not locked to exact versions with hashes, so
  a build is not bit-for-bit reproducible across machines.
- The leaderboard feed at `stats-data.hyperliquid.xyz` is not the documented
  stable Hyperliquid `/info` API and can change its response schema.
