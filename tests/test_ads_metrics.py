from pytest import approx

from wb_case.ads import breakeven_cpm, ad_economics, loss_limited_impressions
from wb_case.metrics import profit_after_ads, cpm_margin, share_in_target, days_of_stock, change_vs


def test_breakeven_cpm():
    assert breakeven_cpm(0.03, 0.04, 0.90, 180) == approx(194.4)


def test_ad_economics_700():
    e = ad_economics(0.03, 0.04, 0.90, 180, 700)
    assert round(e["result"], 1) == -505.6 and round(e["romi"] * 100, 1) == -72.2
    assert round(e["ad_cost_per_buyout"], 1) == 648.1
    assert round(e["breakeven_cpc"], 2) == 6.48 and round(e["cpc"], 2) == 23.33
    assert round(e["needed_multiplier"], 1) == 3.6
    assert round(ad_economics(0.03, 0.04, 0.90, 180, 290)["romi"] * 100, 1) == -33.0
    imps, orders = loss_limited_impressions(3000, 700, e["breakeven_cpm"], e["orders"])
    assert round(imps) == 5934 and round(orders) == 7


def test_metrics():
    assert profit_after_ads(10, 180, 1000) == 800
    assert cpm_margin(194.4, 700) == approx(-505.6)
    assert share_in_target([8, 7, 9, None, 6]) == approx(0.6)
    assert round(days_of_stock(900, 16.8), 1) == 53.6
    assert change_vs(110, 100) == approx(0.1)
