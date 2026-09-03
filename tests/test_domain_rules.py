from app.domains.forex.rules import ForexRules
from app.domains.forex.sessions import SESSIONS
from app.domains.crypto.rules import CryptoRules
from app.domains.crypto.instrument import CryptoInstrument, CryptoMarketType


def test_forex_pips_and_position_size():
    rules = ForexRules()
    assert rules.pip_distance(1.1000, 1.0950) == 50
    assert rules.position_lots(100, 1.1000, 1.0950) > 0


def test_forex_sessions_exist():
    assert {s.name for s in SESSIONS} == {"Sydney", "Tokyo", "London", "New York"}


def test_crypto_futures_margin_and_net_pnl():
    rules = CryptoRules()
    assert rules.notional(0.5, 60000) == 30000
    assert rules.margin_required(0.5, 60000, 10) == 3000
    assert rules.net_pnl(500, 20, 5) == 475


def test_crypto_instrument_market_type():
    item = CryptoInstrument("BTCUSDT", "Binance", CryptoMarketType.FUTURES)
    assert item.market_type is CryptoMarketType.FUTURES
