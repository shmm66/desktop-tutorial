from pathlib import Path
import math

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def test_primary_routes_remove_academy_chat_and_tradingview():
    app = read("TraderPlannerPro_v7_0_3.py")
    launcher = read("launcher.py")
    for method in (
        "def home(self):", "def daily(self):", "def weekly(self):",
        "def plan(self):", "def check(self):", "def journal(self):",
        "def insights(self):", "def resources(self):", "def news(self):",
        "def calculators(self):", "def settings(self):",
    ):
        assert method in app
    for removed in ("def academy(self):", "def ai_page(self):", "def chart(self):",
                    "def open_ai_chat(self):", "def open_tradingview(",
                    "AIOrchestrator", "from academy_content import", "from native_trading_desk import"):
        assert removed not in app
    assert '"insights","resources","news","calculators","settings"' in app
    assert '"--tradingview"' not in launcher
    assert '"--webview"' not in launcher


def test_goal_manager_keeps_week_month_year_dates_and_editing():
    app = read("TraderPlannerPro_v7_0_3.py")
    assert '"goals": []' in app
    assert "def _goal_period_range(self, period, reference=None):" in app
    assert "def goal_dialog(self, goal=None):" in app
    assert "def edit_goal(self):" in app
    assert 'self.tr("goal_weekly")' in app
    assert 'self.tr("goal_monthly")' in app
    assert 'self.tr("goal_yearly")' in app
    assert "date.fromisoformat(start_var.get().strip())" in app


def test_profiles_remain_in_topbar_and_settings():
    app = read("TraderPlannerPro_v7_0_3.py")
    assert 'self.profile_combo = ttk.Combobox(status, state="readonly"' in app
    assert "def refresh_profile_selector(self):" in app
    assert "def profile_panel(self, parent):" in app
    assert "self.profile_panel(self.content)" in app
    assert "def on_profile_change(self, _=None):" in app


def test_settings_highlight_current_selection_and_clock_variants():
    app = read("TraderPlannerPro_v7_0_3.py")
    assert 'bg=C["accent"], fg="#061019"' in app
    assert '"digital", "classic", "wrist"' in app
    assert "def set_clock_style(self, style):" in app
    assert "self.session_clock_container = clocks" in app
    assert "apply_glass_after_map(self" in app


def test_hamburger_autohide_uses_global_pointer_position():
    app = read("TraderPlannerPro_v7_0_3.py")
    assert 'self.bind_all("<Motion>", self._shell_motion, add="+")' in app
    assert "def _shell_motion(self, event):" in app
    assert "def _schedule_menu_hide(self, delay=1200):" in app


def test_no_expensive_ai_or_education_dependencies_in_package_requirements():
    requirements = read("requirements.txt").lower()
    for removed in ("pywebview", "matplotlib", "openai-agents", "\nopenai"):
        assert removed not in requirements
    for needed in ("pillow", "pywinstyles", "reportlab", "google-api-python-client"):
        assert needed in requirements


def test_glass_callbacks_are_bounded_and_never_recurse(monkeypatch):
    import glass_theme

    class FakeWindow:
        def __init__(self):
            self.jobs = {}
            self.after_count = 0
            self.cancel_count = 0
        def winfo_exists(self): return True
        def wm_attributes(self, *_args): return None
        def configure(self, **_kwargs): return None
        def after(self, _delay, callback):
            self.after_count += 1
            job = f"job-{self.after_count}"
            self.jobs[job] = callback
            return job
        def after_cancel(self, job):
            self.cancel_count += 1
            self.jobs.pop(job, None)

    monkeypatch.setattr(glass_theme, "is_windows", lambda: True)
    monkeypatch.setattr(glass_theme, "_configure_window_transparency", lambda *_a: None)
    monkeypatch.setattr(glass_theme, "_set_dwm_backdrop", lambda *_a, **_k: False)
    monkeypatch.setattr(glass_theme, "_apply_pywinstyles", lambda *_a, **_k: False)
    window = FakeWindow()

    for _ in range(100):
        glass_theme.apply_glass(window)
    assert window.after_count == 0
    for _ in range(100):
        assert glass_theme.apply_glass_after_map(window)
    assert window.after_count == 1
    callback = next(iter(window.jobs.values()))
    callback()
    assert window.after_count == 1
    assert window._tpp_glass_after_map_done is True
    assert window._tpp_glass_after_id is None


def test_local_journal_analyst_is_deterministic_and_has_behavior_breakdowns():
    from journal_agent import analyse_journal
    rows = [
        {"Result (R)": "2", "Result": "WIN", "Setup": "FVG", "Session": "London", "Emotion During": "Calm"},
        {"Result (R)": "-1", "Result": "LOSS", "Setup": "FVG", "Session": "London", "Emotion During": "FOMO", "Mistake": "Early entry"},
        {"Result (R)": "3", "Result": "WIN", "Setup": "BOS", "Session": "New York", "Emotion During": "Calm"},
        {"Result (R)": "0", "Result": "BE", "Setup": "BOS", "Session": "Asia", "Emotion During": "Neutral"},
    ]
    result = analyse_journal(rows)
    assert result["count"] == 4
    assert result["wins"] == 2
    assert result["losses"] == 1
    assert result["breakeven"] == 1
    assert math.isclose(result["win_rate"], 50.0)
    assert math.isclose(result["net_r"], 4.0)
    assert math.isclose(result["expectancy_r"], 1.0)
    assert math.isclose(result["profit_factor"], 5.0)
    assert result["max_losing_streak"] == 1
    assert result["by_setup"][0]["name"] in {"BOS", "FVG"}
    assert result["mistakes"][0] == ("Early entry", 1)


def test_missing_r_values_are_reported_instead_of_hidden():
    from journal_agent import analyse_journal
    result = analyse_journal([{"Result": "WIN", "Setup": "A"}])
    assert result["missing_r_count"] == 1
    assert result["count"] == 1
    assert result["net_r"] == 0
