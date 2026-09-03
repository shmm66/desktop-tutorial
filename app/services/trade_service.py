from __future__ import annotations

from app.core.models import Trade
from app.repositories.trades import TradeRepository


class TradeService:
    def __init__(self, repository: TradeRepository) -> None:
        self.repository = repository

    def record_trade(self, trade: Trade) -> int:
        if trade.market not in {"forex", "crypto"}:
            raise ValueError("market must be forex or crypto")
        if trade.direction not in {"long", "short"}:
            raise ValueError("direction must be long or short")
        if not trade.symbol.strip():
            raise ValueError("symbol is required")
        return self.repository.add(trade)

    def recent(self, market: str) -> list:
        if market not in {"forex", "crypto"}:
            raise ValueError("unsupported market")
        return self.repository.list_by_market(market)
