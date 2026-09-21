from __future__ import annotations

import json
from pathlib import Path

from market_data import fetch_market

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "market_seed.json"


def main():
    markets = {}
    for market in ("Crypto", "Forex"):
        try:
            payload = fetch_market(market)
        except Exception:
            payload = {}
        if isinstance(payload, dict) and payload.get("items") and payload.get("status") == "live":
            snapshot = dict(payload)
            snapshot["status"] = "snapshot"
            snapshot["source"] = f"Build snapshot • {snapshot.get('source', 'public feed')}"
            snapshot["message"] = "Build snapshot only. Live refresh is attempted at startup."
            markets[market] = snapshot

    OUT.write_text(
        json.dumps({"markets": markets}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Created {OUT} with {len(markets)} market snapshots.")


if __name__ == "__main__":
    main()
