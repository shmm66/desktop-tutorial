# Build status

Production packaging is being verified on the Windows self-hosted runner.

- Runner mode: Windows Service
- System Python: C:\Program Files\Python314\python.exe
- Build strategy: system Python -> isolated venv -> EXE -> Inno Setup
- TradingView Pro: official TradingView chart path, no synthetic OHLC
- Target: verified EXE + installer artifact
