from pathlib import Path
import math

from TraderPlannerPro_v7_0_3 import empty_db, empty_profile, migrate_payload, PLAN_FIELDS, I18N, LANGUAGE_OPTIONS

ROOT = Path(__file__).resolve().parents[1]


def test_fresh_profile_has_required_domains():
    profile = empty_profile("Test", "Crypto", "USD", 1250)
    assert profile["name"] == "Test"
    assert profile["initial_balance"] == 1250.0
    assert set(profile["journals"]) == {"Forex", "Crypto"}
    assert profile["checklist"]
    assert set(profile["plan_draft"]) == set(PLAN_FIELDS)
    assert profile["goals"] == []


def test_legacy_payload_migrates_without_losing_journal_plan_or_goals():
    old = {
        "version": 7,
        "market": "Forex",
        "journals": {"Forex": [{"Symbol": "EURUSD", "Result (R)": "1.5"}], "Crypto": []},
        "plan": {"شرایط ورود": "BOS + FVG"},
        "check": {"جهت و ساختار بازار مشخص است": True},
        "profile": {"name": "Swing 2026", "starting_balance": "5000", "account_currency": "USD"},
    }
    db = migrate_payload(old)
    profile = db["profiles"][0]
    assert profile["name"] == "Swing 2026"
    assert profile["initial_balance"] == 5000.0
    assert profile["journals"]["Forex"][0]["Symbol"] == "EURUSD"
    assert profile["plan_draft"]["شرایط ورود"] == "BOS + FVG"
    assert profile["checklist"][0]["done"] is True
    assert profile["goals"] == []


def test_empty_db_has_persistent_profile_shell():
    db = empty_db()
    assert db["profiles"]
    assert db["active_profile_id"] == db["profiles"][0]["id"]
    assert db["settings"]["clock_style"] == "digital"


def test_language_setting_is_persistent_and_bilingual():
    db = empty_db()
    assert db["settings"]["language"] == "fa"
    assert dict(LANGUAGE_OPTIONS) == {"fa": "فارسی", "en": "English"}
    assert I18N["fa"]["settings_title"] == "تنظیمات"
    assert I18N["en"]["settings_title"] == "Settings"
    assert "insights" in I18N["fa"] and "insights" in I18N["en"]
    assert "resources" in I18N["fa"] and "resources" in I18N["en"]


def test_session_clock_configuration_has_four_major_sessions():
    from TraderPlannerPro_v7_0_3 import SESSION_CLOCKS
    assert [item["abbr"] for item in SESSION_CLOCKS] == ["SYD", "TYO", "LON", "NY"]
    assert len(SESSION_CLOCKS) == 4
    assert all(item["start"] < item["end"] and item["tz"] for item in SESSION_CLOCKS)


def test_english_static_ui_labels_do_not_contain_persian():
    for value in I18N["en"].values():
        assert not any("\u0600" <= char <= "\u06FF" for char in str(value)), value


def test_market_data_has_cache_and_multiple_source_fallbacks():
    from market_data import COINCAP_ENDPOINT, cached_market_payload, _crypto_from_coincap
    assert "coincap.io/v2/assets" in COINCAP_ENDPOINT
    assert callable(_crypto_from_coincap)
    payload = cached_market_payload("Crypto")
    assert isinstance(payload, dict)
    assert "items" in payload and "indicators" in payload


def test_news_service_exposes_cache_and_source_fallbacks():
    import news_data
    assert callable(news_data.cached_news)
    assert news_data.COINDESK_HOME.startswith("https://")
    assert news_data.CRYPTO_NEWS_HOME.startswith("https://")
    assert news_data.FOREX_FACTORY.startswith("https://")


def test_main_navigation_contains_only_the_redesigned_pages():
    app = (ROOT / "TraderPlannerPro_v7_0_3.py").read_text(encoding="utf-8")
    launcher = (ROOT / "launcher.py").read_text(encoding="utf-8")
    route_list = app.split("allowed={", 1)[1].split("}", 1)[0]
    for required in ('"academy"', '"coach"', '"weekly"', '"settings"'):
        assert required in route_list
    for obsolete in ('"ai"', '"chart"'):
        assert obsolete not in route_list
    pages = launcher.split('    pages = (', 1)[1].split('    )', 1)[0]
    for required in ('"academy"', '"coach"', '"weekly"', '"settings"'):
        assert required in pages
    for removed_route in ('"--tradingview"', '"--webview"'):
        assert removed_route not in launcher


def test_goal_manager_keeps_week_month_year_periods_and_editable_dates():
    app = (ROOT / "TraderPlannerPro_v7_0_3.py").read_text(encoding="utf-8")
    assert "def _goal_period_range(self, period, reference=None):" in app
    assert "def goal_dialog(self, goal=None):" in app
    assert "def edit_goal(self):" in app
    assert "date.fromisoformat(start_var.get().strip())" in app
    for period in ('self.tr("goal_weekly")', 'self.tr("goal_monthly")', 'self.tr("goal_yearly")'):
        assert period in app


def test_profiles_remain_selectable_and_editable():
    app = (ROOT / "TraderPlannerPro_v7_0_3.py").read_text(encoding="utf-8")
    assert 'self.profile_combo = ttk.Combobox(status, state="readonly"' in app
    assert "def refresh_profile_selector(self):" in app
    assert "def profile_panel(self, parent):" in app
    assert "self.profile_panel(self.content)" in app
    assert "def on_profile_change(self, _=None):" in app
    assert "def profile_dialog(self, profile=None):" in app


def test_logo_revision_is_used_by_shortcut_generator():
    logo = (ROOT / "logo_3d.py").read_text(encoding="utf-8")
    icon = (ROOT / "build_icon.py").read_text(encoding="utf-8")
    assert 'LOGO_REVISION = "3"' in logo
    assert "create_logo_image(source, 512)" in icon
    assert 'format="ICO"' in icon


def test_google_and_statement_services_stay_separately_available():
    from google_oauth import login_google, logout_google, google_status, send_gmail
    from statement_report import create_statement
    assert all(callable(x) for x in (login_google, logout_google, google_status, send_gmail, create_statement))


def test_installer_is_update_safe_and_non_admin():
    installer = (ROOT / "TraderPlannerPro.iss").read_text(encoding="utf-8")
    assert 'MyAppVersion "10.3.0"' in installer
    assert 'OutputBaseFilename=TraderPlannerPro_Setup_v10.3.0' in installer
    assert "PrivilegesRequired=lowest" in installer
    assert "UsePreviousAppDir=yes" in installer
    assert 'DefaultDirName={localappdata}\\Programs\\Trader Planner Pro' in installer


def test_callback_error_logger_never_formats_unbounded_recursive_traceback():
    app = (ROOT / "TraderPlannerPro_v7_0_3.py").read_text(encoding="utf-8")
    handler = app.split("def report_callback_exception(", 1)[1].split("def _home_shortcut(", 1)[0]
    assert "traceback.format_exception" not in handler
    assert "len(frames) < 32" in handler
    assert "_tpp_reporting_callback_error" in handler


def test_native_glass_callback_is_debounced_and_non_recursive(monkeypatch):
    import glass_theme

    class FakeWindow:
        def __init__(self):
            self.jobs = {}
            self.after_count = 0
        def winfo_exists(self): return True
        def wm_attributes(self, *_args): return None
        def configure(self, **_kwargs): return None
        def after(self, _delay, callback):
            self.after_count += 1
            job_id = f"job-{self.after_count}"
            self.jobs[job_id] = callback
            return job_id
        def after_cancel(self, job_id): self.jobs.pop(job_id, None)

    monkeypatch.setattr(glass_theme, "is_windows", lambda: True)
    monkeypatch.setattr(glass_theme, "_configure_window_transparency", lambda *_a: None)
    monkeypatch.setattr(glass_theme, "_set_dwm_backdrop", lambda *_a, **_k: False)
    monkeypatch.setattr(glass_theme, "_apply_pywinstyles", lambda *_a, **_k: False)
    window = FakeWindow()
    for _ in range(50):
        glass_theme.apply_glass(window)
    assert window.after_count == 0
    for _ in range(50):
        assert glass_theme.apply_glass_after_map(window)
    assert window.after_count == 1
    next(iter(window.jobs.values()))()
    assert window.after_count == 1
    assert window._tpp_glass_after_map_done is True


def test_versions_are_consistent():
    app = (ROOT / "TraderPlannerPro_v7_0_3.py").read_text(encoding="utf-8")
    launcher = (ROOT / "launcher.py").read_text(encoding="utf-8")
    installer = (ROOT / "TraderPlannerPro.iss").read_text(encoding="utf-8")
    assert 'VERSION = "10.3.0"' in app
    assert 'VERSION = "10.3.0"' in launcher
    assert 'MyAppVersion "10.3.0"' in installer
