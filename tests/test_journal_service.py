from decimal import Decimal

from app.domains.journal.models import AssetClass, JournalEntry, TradeDirection
from app.repositories.journal_repository import InMemoryJournalRepository
from app.services.journal import JournalService


_counter = 0


def entry(asset_class: AssetClass, direction: TradeDirection, entry_price: str, exit_price: str) -> JournalEntry:
    global _counter
    _counter += 1
    return JournalEntry(
        id=f"test-{_counter}",
        asset_class=asset_class,
        symbol="EURUSD" if asset_class is AssetClass.FOREX else "BTCUSDT",
        direction=direction,
        entry_price=Decimal(entry_price),
        exit_price=Decimal(exit_price),
        quantity=Decimal("1"),
    )


def test_service_keeps_forex_and_crypto_independent() -> None:
    service = JournalService(InMemoryJournalRepository())
    service.record(entry(AssetClass.FOREX, TradeDirection.LONG, "1.1000", "1.1050"))
    service.record(entry(AssetClass.CRYPTO, TradeDirection.SHORT, "60000", "59000"))

    assert len(service.entries(AssetClass.FOREX)) == 1
    assert len(service.entries(AssetClass.CRYPTO)) == 1
    assert service.summary(AssetClass.FOREX).net_pnl == Decimal("0.0050")
    assert service.summary(AssetClass.CRYPTO).net_pnl == Decimal("1000")


def test_service_summary_counts_winners_and_losers() -> None:
    service = JournalService(InMemoryJournalRepository())
    service.record(entry(AssetClass.FOREX, TradeDirection.LONG, "1.1000", "1.1050"))
    service.record(entry(AssetClass.FOREX, TradeDirection.LONG, "1.1050", "1.1000"))

    summary = service.summary(AssetClass.FOREX)
    assert summary.trades == 2
    assert summary.winners == 1
    assert summary.losers == 1
