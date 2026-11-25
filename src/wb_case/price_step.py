"""Эффект шага цены и решение о следующем шаге."""
import math
import statistics as st

from . import data as D
from .pricing import price_chain


def mean_over(idx, values):
    return sum(values[i] for i in idx) / len(idx)


def step_effect(orders=D.ORDERS, wallet=D.WALLET, pre=D.PRE_DAYS, post=D.POST_DAYS,
                profit_before=D.PROFIT_BEFORE, profit_after=D.PROFIT_AFTER):
    """Средние до/после шага. Дни распродажи (10-11) не входят ни в один период:
    повышенная СПП вернула цену с кошельком почти к старой, а трафик распродажи
    смешивает два эффекта."""
    o0, o1 = mean_over(pre, orders), mean_over(post, orders)
    w0, w1 = mean_over(pre, wallet), mean_over(post, wallet)
    p0, p1 = o0 * profit_before, o1 * profit_after
    sd0 = st.stdev([orders[i] for i in pre])
    sd1 = st.stdev([orders[i] for i in post])
    se = math.sqrt(sd0 ** 2 / len(pre) + sd1 ** 2 / len(post))
    return dict(
        orders_before=o0, orders_after=o1, orders_change=o1 / o0 - 1,
        wallet_before=w0, wallet_after=w1, wallet_change=w1 / w0 - 1,
        profit_before=p0, profit_after=p1, profit_change=p1 / p0 - 1,
        unit_profit_change=profit_after / profit_before - 1,
        max_orders_drop=1 - profit_before / profit_after,   # шаг выгоден, пока падение меньше
        sd_before=sd0, sd_after=sd1, diff=o1 - o0, se=se, t=(o1 - o0) / se,
    )


def next_step_forecast(eff, next_price=D.NEXT_PRICE, spp=D.NEXT_SPP, profit_next=D.PROFIT_NEXT):
    """Прогноз заказов и прибыли на следующем шаге двумя моделями спроса
    (по двум наблюдённым точкам кривую не определить, поэтому даю диапазон)."""
    o0, o1 = eff["orders_before"], eff["orders_after"]
    w0, w1 = eff["wallet_before"], eff["wallet_after"]
    w2 = price_chain(next_price, 0, spp)[2]
    elasticity = math.log(o1 / o0) / math.log(w1 / w0)
    o_el = o1 * (w2 / w1) ** elasticity              # постоянная эластичность
    slope = (o1 - o0) / (w1 - w0)
    o_lin = o1 + slope * (w2 - w1)                   # линейный спрос
    breakeven = eff["profit_after"] / profit_next
    return dict(
        wallet_next=w2, elasticity=elasticity, slope=slope,
        orders_elastic=o_el, profit_elastic=o_el * profit_next,
        orders_linear=o_lin, profit_linear=o_lin * profit_next,
        breakeven_orders=breakeven, allowed_drop=breakeven / o1 - 1,
        early_rollback_avg=breakeven - eff["sd_before"] / math.sqrt(3),
        early_rollback_sum=math.floor((breakeven - eff["sd_before"] / math.sqrt(3)) * 3),
        stock_days_now=D.STOCK / o1, stock_days_next=D.STOCK / o_el,
    )
