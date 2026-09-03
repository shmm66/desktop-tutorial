from pathlib import Path

from app.core.database import connect
from app.core.migrations import migrate
from app.core.models import Trade
from app.repositories.trades import TradeRepository
from app.services.trade_service import TradeService


def test_migrations_are_idempotent(tmp_path: Path):
    db_path = tmp_path / "test.db"
    with connect(db_path) as conn:
        # V5 currently has migrations 1 and 2. The first call applies both;
        # the second call must be a no-op and return the same latest version.
        assert migrate(conn) == 2
        assert migrate(conn) == 2
        assert conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 2


def test_trade_round_trip(tmp_path: Path):
    db_path = tmp_path / "test.db"
    with connect(db_path) as conn:
        migrate(conn)
        service = TradeService(TradeRepository(conn))
        trade_id = service.record_trade(Trade(market="forex", symbol="EURUSD", direction="long", pnl=25.0))
        row = TradeRepository(conn).get(trade_id)
        assert row is not None
        assert row["market"] == "forex"
        assert row["symbol"] == "EURUSD"
        assert row["pnl"] == 25.0


def test_service_rejects_invalid_market(tmp_path: Path):
    db_path = tmp_path / "test.db"
    with connect(db_path) as conn:
        migrate(conn)
        service = TradeService(TradeRepository(conn))
        try:
            service.record_trade(Trade(market="stocks", symbol="AAPL", direction="long"))
        except ValueError as exc:
            assert "market" in str(exc)
        else:
            raise AssertionError("invalid market was accepted")
