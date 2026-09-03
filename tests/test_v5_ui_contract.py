from __future__ import annotations

import inspect


def test_v5_launcher_imports():
    import run_v5
    assert callable(run_v5.main)


def test_v5_views_import():
    from app.ui.views import CalculatorView, HomeView, JournalView, MarketView, ReportsView, SessionsView
    assert all(cls is not None for cls in (CalculatorView, HomeView, JournalView, MarketView, ReportsView, SessionsView))


def test_home_is_dashboard_only():
    # The production launcher owns the Home presentation contract and removes
    # Journal-only trade-entry controls from the shared Home view.
    import run_v5
    source = inspect.getsource(run_v5.DashboardHomeView)
    assert "JournalPanel" not in source
    assert "ثبت معامله" in source
    assert "نمای بازار" not in source  # market content belongs to the underlying dashboard
    assert "_remove_journal_controls" in source


def test_journal_panel_owns_trade_form_and_table():
    from app.ui.journal_panel import JournalPanel
    source = inspect.getsource(JournalPanel)
    assert "self.form" in source
    assert "self.table" in source
    assert "add_image" in source
    assert "def save" in source
