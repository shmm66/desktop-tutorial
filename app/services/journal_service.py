from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.domains.crypto.journal import CryptoJournalEntry
from app.domains.forex.journal import ForexJournalEntry
from app.repositories.trades import TradeRepository


class JournalService:
    """Application boundary for journal operations; UI never writes to SQLite directly."""

    def __init__(self, repository: TradeRepository) -> None:
        self.repository = repository

    def save_forex(self, entry: ForexJournalEntry) -> int:
        return self.repository.create(asdict(entry))

    def save_crypto(self, entry: CryptoJournalEntry) -> int:
        return self.repository.create(asdict(entry))

    def list_trades(self, market: str | None = None) -> list[dict[str, Any]]:
        return self.repository.list_all(market=market)
