from decimal import Decimal

import pytest

from app.domains.journal import AssetClass, JournalEntry, TradeDirection, TradeOutcome


def test_forex_journal_entry_calculates_long_net_pnl() -> None:
    trade = JournalEntry(
        asset_class=AssetClass.FOREX,
        symbol="EURUSD",
        direction=TradeDirection.LONG,
        entry_price="1.1000",
        quantity="10000",
        exit_price="1.1050",
        fees="2",
        funding="1",
        outcome=TradeOutcome.WIN,
    )
    assert trade.gross_pnl == Decimal("50.0000")
    assert trade.net_pnl == Decimal("47.0000")


def test_crypto_journal_entry_calculates_short_pnl() -> None:
    trade = JournalEntry(
        asset_class=AssetClass.CRYPTO,
        symbol="BTCUSDT",
        direction=TradeDirection.SHORT,
        entry_price="65000",
        quantity="0.1",
        exit_price="64000",
    )
    assert trade.gross_pnl == Decimal("100.0")
    assert trade.net_pnl == Decimal("100.0")


def test_invalid_journal_entry_is_rejected() -> None:
    with pytest.raises(ValueError, match="symbol is required"):
        JournalEntry(
            asset_class=AssetClass.FOREX,
            symbol="   ",
            direction=TradeDirection.LONG,
            entry_price="1",
            quantity="1",
        )
