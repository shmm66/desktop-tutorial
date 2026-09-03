from pathlib import Path
import tempfile

from app.core.config import AppConfig
from app.core.database import connect, initialize
from app.services.risk import position_size, risk_amount


def test_database_initializes_and_has_expected_tables():
    # Explicitly close the SQLite connection: sqlite3's context manager commits/rolls back
    # but does not close the connection, which can leave the database locked on Windows.
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "test.sqlite3"
        initialize(path)
        conn = connect(path)
        try:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            conn.close()
        assert {"profiles", "trading_accounts", "trades", "daily_plans", "settings"} <= tables


def test_config_creates_data_directory():
    with tempfile.TemporaryDirectory() as tmp:
        cfg = AppConfig(data_dir=Path(tmp) / "data", db_path=Path(tmp) / "data" / "app.sqlite3")
        cfg.data_dir.mkdir(parents=True, exist_ok=True)
        assert cfg.data_dir.exists()


def test_risk_amount():
    assert risk_amount(10_000, 1.5) == 150


def test_position_size_is_positive():
    assert position_size(10_000, 1, 100, 99, 1) == 100
