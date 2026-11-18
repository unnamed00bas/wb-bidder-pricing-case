from pytest import approx

from wb_case.price_step import step_effect, next_step_forecast


def test_step_effect():
    e = step_effect()
    assert round(e["orders_before"], 2) == 20.29 and e["orders_after"] == approx(16.8)
    assert round(e["orders_change"] * 100, 1) == -17.2
    assert round(e["wallet_before"], 1) == 197.4 and round(e["wallet_after"], 1) == 220.4
    assert round(e["profit_before"], 1) == 1054.9 and round(e["profit_after"], 1) == 1226.4
    assert round(e["profit_change"] * 100, 1) == 16.3
    assert round(e["max_orders_drop"] * 100, 1) == 28.8
    assert round(e["t"], 1) == -4.5


def test_next_step_forecast():
    f = next_step_forecast(step_effect())
    assert f["wallet_next"] == 244
    assert round(f["elasticity"], 2) == -1.71
    assert round(f["orders_elastic"], 2) == 14.11 and round(f["profit_elastic"], 1) == 1298.4
    assert round(f["orders_linear"], 2) == 13.22 and round(f["profit_linear"], 1) == 1216.1
    assert round(f["breakeven_orders"], 2) == 13.33
    assert round(f["allowed_drop"] * 100, 1) == -20.7
    assert f["early_rollback_sum"] == 36
    assert round(f["stock_days_now"], 1) == 53.6
