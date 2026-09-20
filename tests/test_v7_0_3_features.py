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
    assert len(ICT_STRATEGIES) == 5
    assert len(CANDLE_PLAYBOOK) >= 10
    assert len(GLOSSARY) >= 100
    assert any(x["term"] == "FVG" or x["term"].startswith("Fair Value Gap") for x in GLOSSARY)
    assert any(x["term"] == "BOS" for x in GLOSSARY)


def test_icon_generator_exists():
    from pathlib import Path
    assert Path("build_icon.py").is_file()


def test_language_options_include_persian_and_english():
    from TraderPlannerPro_v7_0_3 import LANGUAGE_OPTIONS
    assert dict(LANGUAGE_OPTIONS) == {"fa": "فارسی", "en": "English"}


def test_3d_session_clock_face_renders_high_resolution():
    from TraderPlannerPro_v7_0_3 import build_3d_clock_face
    img = build_3d_clock_face(180)
    assert img.size == (180, 180)
    assert img.mode == "RGBA"
