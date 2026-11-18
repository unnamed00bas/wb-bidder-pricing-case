from fractions import Fraction as F

import pytest

from wb_case import data as D
from wb_case.pricing import (price_chain, is_pretty, next_pretty, bases_for, suggest_pretty,
                             spp_sensitivity, reduction_plan, in_quarantine, pre_price_range_for_wallet)


@pytest.mark.parametrize("good, wallet", [("А", 181), ("Б", 198), ("В", 856)])
def test_current_wallet_price(good, wallet):
    b, d, s, _ = D.GOODS[good]
    assert price_chain(b, d, s)[2] == wallet


def test_alt_rounding_changes_only_v():
    assert [price_chain(b, d, s, round_pre=True)[2] for b, d, s, _ in D.GOODS.values()] == [181, 198, 855]


@pytest.mark.parametrize("good, expected", [
    ("А", (189, "up", 1865, 1874)),
    ("Б", (199, "up", 2242, 2252)),
    ("В", (849, "down", 4751, 4756)),
])
def test_suggest_pretty(good, expected):
    b, d, s, cap = D.GOODS[good]
    assert suggest_pretty(b, d, s, cap) == expected


def test_v_up_leaves_promo():
    bs = bases_for(899, 75, 27)
    assert (min(bs), max(bs)) == (5031, 5035)
    assert price_chain(min(bs), 75, 27)[0] == F("1257.75") > 1250


@pytest.mark.parametrize("good, base, sens", [("А", 1874, (192, 187)), ("Б", 2252, (202, 197)), ("В", 4756, (861, 838))])
def test_spp_sensitivity(good, base, sens):
    _, d, s, _ = D.GOODS[good]
    assert spp_sensitivity(base, d, s) == sens


def test_pretty_rules():
    assert is_pretty(189) and is_pretty(849) and is_pretty(899) and is_pretty(1299)
    assert not is_pretty(244) and not is_pretty(850) and not is_pretty(1249)
    assert next_pretty(244, -1) == 239 and next_pretty(244, +1) == 249


def test_b_minus_35_needs_two_steps():
    pre0 = price_chain(2238, 87, 30)[0]
    assert in_quarantine(pre0, pre0 * F(65, 100))
    plan = reduction_plan(2238, 87, 30, [1800, 1454])
    assert [p["wallet"] for p in plan] == [159, 129]
    assert [round(float(p["ratio"]), 3) for p in plan] == [1.243, 1.238]
    assert not any(p["quarantine"] for p in plan)
    assert round(float(plan[-1]["change"]) * 100, 2) == -35.03
    assert bases_for(129, 87, 30) == list(range(1451, 1462))


def test_pretty_neighbours_of_244():
    assert pre_price_range_for_wallet(239, 30) == (F("348.58"), F("349.99"))
    assert pre_price_range_for_wallet(249, 30) == (F("364.29"), F("365.71"))
