from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.domains.crypto.journal import CryptoTrade
from app.domains.forex.journal import ForexTrade
from app.repositories.trades import TradeRepository


class JournalService:
    """Application boundary for journal operations; UI never writes to SQLite directly."""

    def __init__(self, repository: TradeRepository) -> None:
        self.repository = repository

    def save_forex(self, entry: ForexTrade) -> int:
        data = asdict(entry)
        data["market"] = "forex"
        data["direction"] = data["direction"].lower()
        data["quantity"] = data.pop("lot_size")
        data["entry_price"] = data.pop("entry")
        data["stop_loss"] = data.pop("stop_loss")
        data["take_profit"] = data.pop("take_profit")
        return self.repository.create(data)

    def save_crypto(self, entry: CryptoTrade) -> int:
        data = asdict(entry)
        data["market"] = "crypto"
        data["direction"] = data["direction"].lower()
        data["entry_price"] = data.pop("entry")
        data["stop_loss"] = data.pop("stop_loss")
        data["take_profit"] = data.pop("take_profit")
        return self.repository.create(data)

    def list_trades(self, market: str | None = None) -> list[dict[str, Any]]:
        return self.repository.list_all(market=market)
