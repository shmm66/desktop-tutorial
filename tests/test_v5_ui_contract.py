from __future__ import annotations


def test_v5_launcher_imports():
    import run_v5
    assert callable(run_v5.main)


def test_v5_views_import():
    from app.ui.views import CalculatorView, HomeView, JournalView, MarketView, ReportsView, SessionsView
    assert all(cls is not None for cls in (CalculatorView, HomeView, JournalView, MarketView, ReportsView, SessionsView))
