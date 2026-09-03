from datetime import datetime, timezone
from decimal import Decimal

from app.core.database import connect, initialize
from app.core.migrations import migrate
from app.domains.journal.models import AssetClass, JournalEntry, TradeDirection, TradeOutcome
from app.repositories.sqlite_journal_repository import SQLiteJournalRepository


def make_entry(asset_class: AssetClass) -> JournalEntry:
    return JournalEntry(
        asset_class=asset_class,
        symbol="EURUSD" if asset_class is AssetClass.FOREX else "BTCUSDT",
        direction=TradeDirection.LONG,
        entry_price=Decimal("100"),
        quantity=Decimal("2"),
        exit_price=Decimal("105"),
        outcome=TradeOutcome.WIN,
        setup="breakout",
        thesis="test thesis",
        emotion="calm",
        notes="persisted",
        image_refs=["local://chart.png"],
        opened_at=datetime.now(timezone.utc),
    )


def test_sqlite_round_trip_and_market_filter(tmp_path) -> None:
    path = tmp_path / "journal.db"
    initialize(path)
    conn = connect(path)
    try:
        assert migrate(conn) == 2
        repo = SQLiteJournalRepository(conn)
        forex = repo.save(make_entry(AssetClass.FOREX))
        repo.save(make_entry(AssetClass.CRYPTO))

        loaded = repo.get(forex.id)
        assert loaded is not None
        assert loaded.asset_class is AssetClass.FOREX
        assert loaded.outcome is TradeOutcome.WIN
        assert loaded.image_refs == ["local://chart.png"]
        assert loaded.net_pnl == Decimal("10")
        assert len(repo.list("forex")) == 1
        assert len(repo.list("crypto")) == 1
        assert repo.delete(forex.id) is True
        assert repo.get(forex.id) is None
    finally:
        conn.close()
