"""Задание 5. Безубыточный CPM и экономика удержания места."""


def breakeven_cpm(ctr, cr, buyout, profit_per_buyout):
    """Максимальная цена 1000 показов, при которой реклама окупается в ноль:
    1000 × CTR × CR × выкуп × прибыль на выкуп."""
    return 1000 * ctr * cr * buyout * profit_per_buyout


def ad_economics(ctr, cr, buyout, profit, bid):
    """Результат рекламы на 1000 показов при ставке bid (CPM)."""
    be = breakeven_cpm(ctr, cr, buyout, profit)
    clicks = 1000 * ctr
    orders = clicks * cr
    buyouts = orders * buyout
    return dict(
        clicks=clicks, orders=orders, buyouts=buyouts, breakeven_cpm=be,
        result=be - bid, romi=be / bid - 1,
        ad_cost_per_buyout=bid / buyouts,
        breakeven_cpc=cr * buyout * profit, cpc=bid / clicks,
        needed_multiplier=bid / be,
    )


def loss_limited_impressions(loss_limit, bid, be, orders_per_1000):
    """Сколько показов можно купить при заданном лимите убытка и сколько это заказов."""
    imps = loss_limit / (bid - be) * 1000
    return imps, imps / 1000 * orders_per_1000
