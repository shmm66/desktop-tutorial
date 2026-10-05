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
        "def ai(self):",
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
    ]
    for name in expected:
        assert (ROOT / name).is_file()


def test_native_trading_desk_has_no_browser_chart_dependency():
    source = (ROOT / "native_trading_desk.py").read_text(encoding="utf-8").lower()
    assert "class nativetradingdesk" in source
    assert "figurecanvastkagg" in source
    assert "navigationtoolbartk2" in source
    assert "webview" not in source
    assert "tradingview" not in source
