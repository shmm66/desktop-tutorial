from app.domains.forex.calculator import ForexCalculator


def test_risk_amount_and_lots():
    c = ForexCalculator()
    assert c.risk_amount(10_000, 1) == 100
    assert c.lots_for_risk(10_000, 1, 20, 10) == 0.5


def test_pip_value_and_rr():
    c = ForexCalculator()
    assert c.pip_value(100_000, 0.0001) == 10
    assert c.reward_risk(1.1000, 1.0950, 1.1100) == 2
