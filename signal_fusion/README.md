# Signal Fusion Desktop

Windows desktop scanner for the strategy bank:
- ICT2025
- ICT2022
- SMC Photon
- SMC Philip

The engine monitors ten liquid crypto pairs, detects independent setups, fuses compatible signals by time/price overlap, raises Windows notifications, explains the setup in Persian, and tracks TP/SL outcomes.

Important: the star is a confluence classification, not a win-probability score. The engine never claims a guaranteed outcome.

## Star rules
- ★ one strategy confirms
- ★★ two independent strategies agree and their entry zones overlap
- ★★★ three or more agree and overlap

The app uses confirmed candles for signals and does not execute trades.

## CI build verification
The GitHub Actions workflow builds a Windows one-file executable named `SignalFusion.exe` and publishes it as the `SignalFusion-Windows` workflow artifact.
