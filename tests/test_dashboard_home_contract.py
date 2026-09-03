from __future__ import annotations


def test_launcher_uses_journal_separated_dashboard():
    import run_v5
    from app.ui import views

    assert run_v5.DashboardHomeView is views.HomeView
    assert run_v5.DashboardHomeView.__name__ == "DashboardHomeView"
    assert "Journal-only trade-entry controls" in run_v5.DashboardHomeView.__doc__
