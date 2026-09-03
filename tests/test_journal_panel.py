def test_dedicated_journal_panel_imports() -> None:
    from app.ui.journal_panel import JournalPanel

    assert JournalPanel.FOREX_FIELDS != JournalPanel.CRYPTO_FIELDS
    assert "Lot" in JournalPanel.FOREX_FIELDS
    assert "Leverage" in JournalPanel.CRYPTO_FIELDS
    assert "Liquidation" in JournalPanel.CRYPTO_FIELDS


def test_journal_panel_uses_application_service() -> None:
    from app.ui.journal_panel import JournalPanel
    import inspect

    source = inspect.getsource(JournalPanel)
    assert "JournalService" in source
    assert "SQLiteJournalRepository" in source
