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
