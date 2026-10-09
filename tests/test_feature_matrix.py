from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_core_desktop_feature_matrix():
    source = (ROOT / "TraderPlannerPro_v7_0_3.py").read_text(encoding="utf-8")
    required_methods = [
        "def home(self):",
        "def daily(self):",
        "def plan(self):",
        "def check(self):",
        "def journal(self):",
        "def academy(self):",
        "def ai_page(self):",
        "def news(self):",
        "def calculators(self):",
        "def settings(self):",
        "def email_statement(self):",
        "def open_ai_chat(self):",
        "def set_market_mode(self, market):",
    ]
    for method in required_methods:
        assert method in source


def test_desktop_services_and_native_chart_files_exist():
    expected = [
        "ai_assistant.py",
        "google_oauth.py",
        "statement_report.py",
        "news_data.py",
        "market_data.py",
        "glass_theme.py",
        "native_trading_desk.py",
        "tradingview_runner.py",
    ]
    for name in expected:
        assert (ROOT / name).is_file()


def test_native_trading_desk_has_no_browser_chart_dependency():
    source = (ROOT / "native_trading_desk.py").read_text(encoding="utf-8").lower()
    assert "class nativetradingdesk" in source
    assert "figurecanvastkagg" in source
    assert "navigationtoolbar2tk" in source
    assert "webview" not in source
    assert "tradingview" not in source


def test_tradingview_pro_embed_is_official_and_real_time_or_fail_safe():
    source = (ROOT / "tradingview_runner.py").read_text(encoding="utf-8")
    assert "def tradingview_url" in source
    assert "https://www.tradingview.com/chart/?symbol=" in source
    assert "&interval=" in source
    assert "webview.create_window" in source
    assert 'gui="edgechromium"' in source
    assert "https://www.tradingview.com/chart/" in source
    # The chart path must not generate synthetic OHLC data.
    assert "fake candle" not in source.lower()
    assert "synthetic candle" not in source.lower()
    assert "random" not in source.lower()



def test_glass_theme_does_not_accumulate_map_callbacks():
    source = (ROOT / "glass_theme.py").read_text(encoding="utf-8")
    assert 'window.bind("<Map>"' not in source
    assert "_tpp_glass_after_id" in source
    assert "after_cancel" in source
    assert "_tpp_glass_applying" in source
    apply_body = source.split("def apply_glass(", 1)[1].split(
        "def apply_glass_to_toplevel(", 1
    )[0]
    assert "window.after(" not in apply_body
    assert "window.after(50, lambda:" not in source


def test_glass_callbacks_are_bounded_when_theme_is_applied_repeatedly(monkeypatch):
    import glass_theme

    class FakeWindow:
        def __init__(self):
            self.jobs = {}
            self.after_count = 0
            self.cancel_count = 0

        def winfo_exists(self):
            return True

        def wm_attributes(self, *_args):
            return None

        def configure(self, **_kwargs):
            return None

        def after(self, _delay, callback):
            self.after_count += 1
            job_id = f"job-{self.after_count}"
            self.jobs[job_id] = callback
            return job_id

        def after_cancel(self, job_id):
            self.cancel_count += 1
            self.jobs.pop(job_id, None)

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


def test_ai_status_checks_are_cache_first_and_sdk_load_is_lazy():
    source = (ROOT / "ai_assistant.py").read_text(encoding="utf-8")
    assert "ollama_online, ollama_models = _cached_ollama_status()" in source
    sdk_loader = source.split("def _ensure_agents_sdk()", 1)[1].split("def ", 1)[0]
    assert "from agents import Agent" in sdk_loader
    assert "def _cached_ollama_status()" in source


def test_native_chart_is_lazy_loaded_and_startup_is_deferred():
    source = (ROOT / "TraderPlannerPro_v7_0_3.py").read_text(encoding="utf-8")
    class_start = source.index("class App(")
    assert "from native_trading_desk import NativeTradingDesk" not in source[:class_start]
    assert "def _load_native_trading_desk(self, holder):" in source
    assert "self.after(80, self._finish_startup)" in source


def test_logo_render_is_cached_and_tk_callback_errors_are_logged():
    logo_source = (ROOT / "logo_3d.py").read_text(encoding="utf-8")
    app_source = (ROOT / "TraderPlannerPro_v7_0_3.py").read_text(encoding="utf-8")
    assert "cached.verify()" in logo_source
    assert "def report_callback_exception(self, exc, value, tb):" in app_source
    assert "ui_errors.log" in app_source



def test_launcher_exposes_real_tk_page_smoke_test():
    source = (ROOT / "launcher.py").read_text(encoding="utf-8")
    expected_pages = (
        '"home", "daily", "weekly", "plan", "check", "journal",',
        '"academy", "ai", "news", "calculators", "chart", "settings",',
    )
    assert 'sys.argv[1] == "--ui-smoke-test"' in source
    assert "def _run_ui_smoke_test():" in source
    assert "SAFE RECOVERY" in source
    for page_list_fragment in expected_pages:
        assert page_list_fragment in source



def test_splash_waits_for_app_preload_instead_of_closing_early():
    source = (ROOT / "launcher.py").read_text(encoding="utf-8")
    assert "def show_splash(ready_event=None):" in source
    assert "def _preload_app_class(result, ready_event):" in source
    assert "name=\"TraderPlannerModulePreload\"" in source
    assert "show_splash(preload_ready)" in source
    assert "elif ready_event is not None and not ready_event.is_set():" in source
    assert source.index("target=_preload_app_class") < source.index("show_splash(preload_ready)")


def test_weekly_and_journal_page_helpers_are_implemented():
    source = (ROOT / "TraderPlannerPro_v7_0_3.py").read_text(encoding="utf-8")
    assert "def _week_dates(self, offset=0):" in source
    assert "def _week_task_stats(self, dates):" in source
    assert "def _trade_metrics(self, rows):" in source
    assert '"profit_factor": profit_factor' in source
    assert '"avg_r": net_r / count if count else 0.0' in source


def test_ai_page_routes_around_ai_service_name_collision():
    source = (ROOT / "TraderPlannerPro_v7_0_3.py").read_text(encoding="utf-8")
    assert "self.ai = AIOrchestrator()" in source
    assert "renderer = self.ai_page if key == \"ai\" else getattr(self, key)" in source
    assert "def ai_page(self):" in source



def test_home_and_journal_render_helpers_exist():
    source = (ROOT / "TraderPlannerPro_v7_0_3.py").read_text(encoding="utf-8")
    assert "def render_home_summary(self, parent, rows):" in source
    assert "def _metric_card(self, parent, title, value, accent):" in source
    assert "Journal Snapshot • Recent Trades" in source
    assert "def _trade_metrics(self, rows):" in source
