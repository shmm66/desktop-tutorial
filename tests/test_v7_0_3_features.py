from TraderPlannerPro_v7_0_3 import empty_profile, empty_db, migrate_payload, PLAN_FIELDS

def test_fresh_profile_has_required_domains():
    p = empty_profile("Test", "Crypto", "USD", 1250)
    assert p["name"] == "Test"
    assert p["initial_balance"] == 1250.0
    assert set(p["journals"]) == {"Forex", "Crypto"}
    assert len(p["checklist"]) > 0
    assert set(p["plan_draft"]) == set(PLAN_FIELDS)

def test_legacy_payload_migrates_without_losing_journal_and_plan():
    old = {
        "version": 7,
        "market": "Forex",
        "journals": {"Forex": [{"Symbol": "EURUSD", "Result (R)": "1.5"}], "Crypto": []},
        "plan": {"شرایط ورود": "BOS + FVG"},
        "check": {"جهت و ساختار بازار مشخص است": True},
        "profile": {"name": "Swing 2026", "starting_balance": "5000", "account_currency": "USD"},
    }
    db = migrate_payload(old)
    p = db["profiles"][0]
    assert p["name"] == "Swing 2026"
    assert p["initial_balance"] == 5000.0
    assert p["journals"]["Forex"][0]["Symbol"] == "EURUSD"
    assert p["plan_draft"]["شرایط ورود"] == "BOS + FVG"
    assert p["checklist"][0]["done"] is True

def test_empty_db_has_persistent_profile_shell():
    db = empty_db()
    assert db["profiles"]
    assert db["active_profile_id"] == db["profiles"][0]["id"]


def test_language_setting_is_persistent_and_bilingual():
    from TraderPlannerPro_v7_0_3 import empty_db, I18N, LANGUAGE_OPTIONS
    db = empty_db()
    assert db["settings"]["language"] == "fa"
    assert dict(LANGUAGE_OPTIONS) == {"fa": "فارسی", "en": "English"}
    assert I18N["fa"]["settings_title"] == "تنظیمات"
    assert I18N["en"]["settings_title"] == "Settings"


def test_session_clock_configuration_has_four_major_sessions():
    from TraderPlannerPro_v7_0_3 import SESSION_CLOCKS
    assert [x["abbr"] for x in SESSION_CLOCKS] == ["SYD", "TYO", "LON", "NY"]
    assert len(SESSION_CLOCKS) == 4
    assert all(x["start"] < x["end"] and x["tz"] for x in SESSION_CLOCKS)


def test_academy_content_is_populated():
    from academy_content import SMART_MONEY_STRATEGIES, ICT_STRATEGIES, CANDLE_PLAYBOOK, GLOSSARY
    assert len(SMART_MONEY_STRATEGIES) == 5
    assert len(ICT_STRATEGIES) == 7
    assert len(CANDLE_PLAYBOOK) >= 16
    assert any(x[0] == "Bullish Engulfing" for x in CANDLE_PLAYBOOK)
    assert any(x[0] == "Bearish Engulfing" for x in CANDLE_PLAYBOOK)
    assert len(GLOSSARY) >= 100
    assert any(x["term"] == "Fair Value Gap (FVG)" or x["term"] == "FVG" for x in GLOSSARY)
    assert any(x["term"] == "FVG" or x["term"].startswith("Fair Value Gap") for x in GLOSSARY)
    assert any(x["term"] == "BOS" for x in GLOSSARY)


def test_icon_generator_exists():
    from pathlib import Path
    assert Path("build_icon.py").is_file()


def test_language_options_include_persian_and_english():
    from TraderPlannerPro_v7_0_3 import LANGUAGE_OPTIONS
    assert dict(LANGUAGE_OPTIONS) == {"fa": "فارسی", "en": "English"}


def test_visual_generator_and_source_mapping_exist():
    from pathlib import Path
    from academy_visuals import EDUCATION_SOURCES, visual_key_for, source_for_visual
    assert Path("academy_visuals.py").is_file()
    assert "candlestick" in EDUCATION_SOURCES
    assert "structure" in EDUCATION_SOURCES
    assert "liquidity" in EDUCATION_SOURCES
    assert visual_key_for("Fair Value Gap", "Imbalance", "") == "fvg"
    assert visual_key_for("Order Block", "PD Array", "") == "order_block"
    assert source_for_visual("candlestick")[0].startswith("TradingView Support")


def test_english_static_ui_labels_do_not_contain_persian():
    from TraderPlannerPro_v7_0_3 import I18N
    for value in I18N["en"].values():
        assert not any("\u0600" <= ch <= "\u06FF" for ch in str(value)), value


def test_visual_render_smoke(tmp_path, monkeypatch):
    import academy_visuals
    class FakeResponse:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return b"0" * 7000
    monkeypatch.setattr(academy_visuals, "urlopen", lambda *args, **kwargs: FakeResponse())
    out = academy_visuals.render_visual(tmp_path / "structure.jpg", "structure", "Market Structure", "Highs, lows and structure break")
    assert out.exists()
    assert out.suffix == ".webp"
    assert out.stat().st_size > 5000


def test_v740_visual_sources_are_original_remote_assets():
    from TraderPlannerPro_v7_0_3 import VERSION
    from academy_visuals import REMOTE_IMAGES, EDUCATION_SOURCES, image_url_for_visual
    assert VERSION == "8.0.0"
    for key in ("candlestick","structure","liquidity","fvg","order_block","breaker","timing","smt"):
        assert key in REMOTE_IMAGES
        assert REMOTE_IMAGES[key].startswith("https://")
        assert image_url_for_visual(key) == REMOTE_IMAGES[key]
        assert key in EDUCATION_SOURCES
        assert "TradingView" in EDUCATION_SOURCES[key][0] or "CME" in EDUCATION_SOURCES[key][0]


def test_v740_market_data_configuration():
    from market_data import CRYPTO_FALLBACK, FOREX_SYMBOLS, CRYPTO_ENDPOINT, YAHOO_ENDPOINT, FEAR_GREED_ENDPOINT
    assert len(CRYPTO_FALLBACK) == 10
    assert len(FOREX_SYMBOLS) >= 10
    assert "coingecko.com/api/v3/coins/markets" in CRYPTO_ENDPOINT
    assert "/v8/finance/chart/{symbol}" in YAHOO_ENDPOINT
    assert "alternative.me/fng" in FEAR_GREED_ENDPOINT


def test_v740_home_shortcut_and_auto_hide_are_present():
    from pathlib import Path
    source = Path("TraderPlannerPro_v7_0_3.py").read_text(encoding="utf-8")
    assert 'self.bind_all("<Home>"' in source
    assert "self.menu_hide_job" in source
    assert "_schedule_menu_hide" in source
    assert "MARKET TAPE" in source


def test_v750_calendar_conversion_has_all_three_calendars():
    from calendar_utils import calendar_snapshot, display_date
    from datetime import date
    snap = calendar_snapshot(date(2026, 9, 21))
    assert snap["gregorian"] == "2026-09-21"
    assert snap["weekday_en"] == "Monday"
    assert snap["jalali_iso"]
    assert snap["hijri_iso"]
    assert "Monday" in display_date(date(2026, 9, 21), "en")


def test_v750_candlestick_sources_are_pattern_specific():
    from academy_visuals import visual_key_for, image_url_for_visual, EDUCATION_SOURCES
    assert visual_key_for("Bullish Engulfing", "Candlestick", "") == "bullish_engulfing"
    assert visual_key_for("Bearish Engulfing", "Candlestick", "") == "bearish_engulfing"
    assert image_url_for_visual("bullish_engulfing").endswith(".png?1594035480=")
    assert image_url_for_visual("bearish_engulfing").endswith(".png?1594035191=")
    assert image_url_for_visual("long_legged_doji").endswith("48g0fJv6_mid.webp")
    assert "Engulfing" in EDUCATION_SOURCES["bullish_engulfing"][0]


def test_v750_market_indicators_exist_for_both_modes():
    from market_data import fetch_market
    # Deterministic test: only configuration is asserted; network calls are not required here.
    import market_data
    assert hasattr(market_data, "fetch_market")
    assert "btc_dominance" in market_data._global_indicators.__code__.co_consts or "btc_dominance" in market_data._global_indicators.__code__.co_names
    assert "usdt_dominance" in market_data._global_indicators.__code__.co_consts or "usdt_dominance" in market_data._global_indicators.__code__.co_names


def test_v750_navigation_ai_news_calculators_and_theme_are_present():
    from pathlib import Path
    source = Path("TraderPlannerPro_v7_0_3.py").read_text(encoding="utf-8")
    for key in ("ai", "news", "calculators"):
        assert f'"{key}"' in source
    assert "def go_home(self):" in source
    assert "def apply_theme(self, initial=False):" in source
    assert "def render_market_indicators(self, payload=None):" in source
    assert "def open_webview(self, url, title=" in source


def test_v760_market_engine_has_exchange_and_cache_fallbacks():
    from market_data import BINANCE_TICKER_ENDPOINTS, YAHOO_ENDPOINTS, CRYPTO_ENDPOINT, GLOBAL_ENDPOINT
    assert len(BINANCE_TICKER_ENDPOINTS) >= 2
    assert len(YAHOO_ENDPOINTS) >= 2
    assert "coingecko.com/api/v3/coins/markets" in CRYPTO_ENDPOINT
    assert "coingecko.com/api/v3/global" in GLOBAL_ENDPOINT


def test_v760_news_uses_multiple_live_feeds():
    from news_data import FEEDS, COINTELEGRAPH_RSS, CRYPTOSLATE_RSS
    assert len(FEEDS) >= 4
    assert COINTELEGRAPH_RSS in [url for _, url in FEEDS]
    assert CRYPTOSLATE_RSS in [url for _, url in FEEDS]


def test_v760_modern_skins_and_ai_chat_hooks():
    from TraderPlannerPro_v7_0_3 import SKINS, I18N
    from pathlib import Path
    source = Path("TraderPlannerPro_v7_0_3.py").read_text(encoding="utf-8")
    assert {"obsidian","aurora","graphite","pearl"} <= set(SKINS)
    assert "def open_ai_chat(self):" in source
    assert "<Control-K>" in source
    assert "def _rounded_rect(" in source
    assert I18N["fa"]["ai"].startswith("🤖")


def test_v760_academy_strategy_maps_are_exact_and_distinct():
    from academy_visuals import strategy_visual_key, glossary_visual_key, source_for_visual
    assert strategy_visual_key("ICT 2022 Model") == "ict_2022"
    assert strategy_visual_key("ICT Silver Bullet") == "ict_silver_bullet"
    assert strategy_visual_key("Power of Three (AMD)") == "ict_amd"
    assert strategy_visual_key("Judas Swing / Killzone Reversal") == "ict_judas"
    assert strategy_visual_key("ICT Unicorn Model") == "unicorn"
    assert strategy_visual_key("Liquidity Sweep + BOS") == "smc_liquidity"
    assert glossary_visual_key("BOS", "Structure") == "smc_overview"
    assert glossary_visual_key("Silver Bullet", "Model") == "ict_silver_bullet"
    assert glossary_visual_key("OTE", "Range") == "ict_ote"
    assert glossary_visual_key("Fair Value Gap", "Imbalance") == "fvg"
    assert glossary_visual_key("Order Block (Bullish)", "PD Array") == "order_block"
    assert glossary_visual_key("Breaker Block", "PD Array") == "breaker"
    assert source_for_visual("ict_2022")[0].startswith("TradingView")
    assert source_for_visual("ict_silver_bullet")[0].startswith("TradingView")


def test_v760_persistent_navigation_and_embedded_ai_are_present():
    from pathlib import Path
    source = Path("TraderPlannerPro_v7_0_3.py").read_text(encoding="utf-8")
    assert "def set_market_mode(self, market):" in source
    assert "self._nav_token" in source
    assert "self.quickbar" in source
    assert "def _render_page(self, key, token):" in source
    assert "def _replace_page_ai_waiting(self,chat,answer):" in source
    assert "def ai(self):" in source and "ai_quick_strategy" in source


def test_v770_google_ai_and_statement_services_exist():
    from google_oauth import GOOGLE_SCOPES, google_status, candidate_client_paths
    from statement_report import summarize
    from ai_assistant import ROLES, cloud_status
    assert "openid" in GOOGLE_SCOPES
    assert "https://www.googleapis.com/auth/gmail.send" in GOOGLE_SCOPES
    assert callable(google_status)
    assert callable(candidate_client_paths)
    assert {"form","strategy","psychology","planner","academy","product"} <= set(ROLES)
    stats = summarize([{"Result (R)": "2"}, {"Result (R)": "-1"}, {"Result (R)": "0"}])
    assert stats["trades"] == 3
    assert stats["wins"] == 1
    assert stats["losses"] == 1
    assert round(stats["net_r"], 2) == 1.0
    assert "enabled" in cloud_status()


def test_v770_statement_email_and_settings_hooks_are_present():
    from pathlib import Path
    source = Path("TraderPlannerPro_v7_0_3.py").read_text(encoding="utf-8")
    assert "def email_statement(self):" in source
    assert "send_gmail(" in source
    assert "google_account" in source
    assert "ai_cloud" in source
    assert "Product Strategist" in source


def test_v770_home_market_mode_navigation_is_hardwired():
    from pathlib import Path
    source = Path("TraderPlannerPro_v7_0_3.py").read_text(encoding="utf-8")
    assert 'self.show("home")' in source
    assert "def set_market_mode(self, market):" in source
    assert "self.market_data.set_market(market)" in source

def test_v780_glass_and_academy_semantics():
    from glass_theme import apply_glass, set_widget_glass
    from academy_diagrams import draw_setup, draw_candlestick
    from academy_visuals import strategy_visual_key
    assert callable(apply_glass)
    assert callable(set_widget_glass)
    assert callable(draw_setup)
    assert callable(draw_candlestick)
    assert strategy_visual_key("5) Liquidity + Displacement + Retest") == "smc_liquidity"


def test_v780_smart_money_is_not_ict_premium_ote_model():
    from academy_content import SMART_MONEY_STRATEGIES
    names = {item["name_en"] for item in SMART_MONEY_STRATEGIES}
    assert "5) Liquidity + Displacement + Retest" in names
    assert "5) Premium/Discount + OTE + Liquidity" not in names


def test_v780_installer_and_launcher_metadata():
    from pathlib import Path
    iss = Path("TraderPlannerPro.iss").read_text(encoding="utf-8")
    launcher = Path("launcher.py").read_text(encoding="utf-8")
    assert 'MyAppVersion "8.0.0"' in iss
    assert "DefaultDirName={localappdata}\\Programs\\Trader Planner Pro" in iss
    assert "VERSION = \"8.0.0\"" in launcher


def test_v780_news_webview_has_fallback():
    from pathlib import Path
    text = Path("webview_runner.py").read_text(encoding="utf-8")
    assert "webbrowser.open(url)" in text


def test_v800_ai_uses_supported_master_model():
    from ai_assistant import DEFAULT_MODEL, ROLES
    assert DEFAULT_MODEL == "gpt-5.6-sol"
    assert "academy" in ROLES
    assert "product" in ROLES


def test_v79_academy_visuals_are_family_specific():
    from academy_visuals import strategy_visual_key, glossary_visual_key, pattern_visual_key
    assert strategy_visual_key("1) ICT 2022 Model") == "ict_2022"
    assert strategy_visual_key("2) ICT Silver Bullet") == "ict_silver_bullet"
    assert strategy_visual_key("3) ICT Unicorn Model") == "unicorn"
    assert strategy_visual_key("7) SMT Divergence") == "smt"
    assert pattern_visual_key("Bullish Engulfing") == "bullish_engulfing"
    assert pattern_visual_key("Bearish Engulfing") == "bearish_engulfing"
    assert glossary_visual_key("SMT Divergence", "ICT") == "smt"


def test_v79_google_scopes_include_gmail_send():
    from google_oauth import GOOGLE_SCOPES
    assert "https://www.googleapis.com/auth/gmail.send" in GOOGLE_SCOPES


def test_v79_market_payload_never_sticks_as_loading():
    from market_data import cached_market_payload
    payload = cached_market_payload("Crypto")
    assert payload.get("status") in {"cache", "unavailable"}


def test_v79_navigation_and_glass_hooks_present():
    from pathlib import Path
    text = Path("TraderPlannerPro_v7_0_3.py").read_text(encoding="utf-8")
    assert "def _hard_home(self):" in text
    assert "command=self._hard_home" in text
    assert "apply_glass(self" in text
    assert "set_widget_glass(top" in text


def test_v800_navigation_uses_single_home_renderer():
    from pathlib import Path
    source = Path("TraderPlannerPro_v7_0_3.py").read_text(encoding="utf-8")
    assert "self.show(\"home\")" in source
    assert "self.after_idle(self._hard_home)" in source
    assert "self.after_idle(self.market_data.refresh_now)" in source
    assert 'status = "loading"' in source or '["status"] = "loading"' in source


def test_v800_ai_uses_flagship_model_and_web_fallback():
    from ai_assistant import DEFAULT_MODEL, MODEL_FALLBACKS, CHATGPT_WEB_URL
    assert DEFAULT_MODEL == "gpt-5.6-sol"
    assert MODEL_FALLBACKS[0] == "gpt-5.6-sol"
    assert CHATGPT_WEB_URL.startswith("https://")


def test_v800_academy_has_distinct_smc_ict_diagram_dispatch():
    from academy_diagrams import draw_setup
    import inspect
    source = inspect.getsource(draw_setup)
    assert "_smc_liquidity_bos" in source
    assert "_smc_ob_fvg" in source
    assert "_smc_breaker" in source
    assert "_ict_2022" in source
    assert "_ict_silver_bullet" in source
    assert "_ict_unicorn" in source


def test_v800_google_gmail_and_statement_modules_exist():
    from pathlib import Path
    assert Path("google_oauth.py").is_file()
    assert Path("statement_report.py").is_file()
    source = Path("google_oauth.py").read_text(encoding="utf-8")
    assert "gmail.send" in source
    assert "login_google" in source
    assert "send_gmail" in source
