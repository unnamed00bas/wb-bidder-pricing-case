"""Цена покупателя с СПП и WB Кошельком, «красивая» цена, карантин.

Цены считаются в точной арифметике (Fraction), чтобы округление «вниз до рубля»
не ломалось на границах из-за ошибок float.
"""
import math
from fractions import Fraction as F

from .data import WALLET_FACTOR_PCT, SPP_THRESHOLD, QUARANTINE_RATIO


def price_chain(base, disc_pct, spp_pct, round_pre=False):
    """База -> (цена до СПП, цена после СПП, цена с кошельком).

    до СПП      = база × (1 − скидка)             (по умолчанию без округления)
    после СПП   = ⌊до СПП × (1 − СПП)⌋
    с кошельком = ⌊после СПП × 0,98⌋

    round_pre=True - альтернативное допущение: цена до СПП тоже округляется вниз.
    """
    pre = F(base) * (1 - F(disc_pct, 100))
    if round_pre:
        pre = F(math.floor(pre))
    after = math.floor(pre * (1 - F(spp_pct, 100)))
    wallet = math.floor(after * F(WALLET_FACTOR_PCT, 100))
    return pre, after, wallet


def is_pretty(w):
    """Красивая цена: до 300 ₽ оканчивается на 9, 300–999 ₽ - на 49/99, от 1000 ₽ - на 99."""
    if w < 300:
        return w % 10 == 9
    if w < 1000:
        return w % 100 in (49, 99)
    return w % 100 == 99


def next_pretty(w, step):
    """Ближайшая красивая цена вверх (step=+1) или вниз (step=-1), включая саму w."""
    while not is_pretty(w):
        w += step
    return w


def bases_for(target_wallet, disc, spp, hi=20000, round_pre=False):
    """Все целые базы, дающие заданную цену с кошельком при данной скидке и СПП."""
    return [b for b in range(1, hi) if price_chain(b, disc, spp, round_pre)[2] == target_wallet]


def quarantine_ratio(old_pre, new_pre):
    """Кратность снижения «старая / новая цена до СПП». >= 1,5 - карантин."""
    return F(old_pre) / F(new_pre)


def in_quarantine(old_pre, new_pre):
    return quarantine_ratio(old_pre, new_pre) >= F(QUARANTINE_RATIO).limit_denominator()


def suggest_pretty(base, disc, spp, promo_cap=None, threshold=SPP_THRESHOLD):
    """Подбор красивой цены.

    Сначала ищу ближайшую красивую вверх; вниз иду, только если вверх товар выходит
    из акции (цена до СПП выше потолка) или переходит порог 1200 ₽. Отсекаю базы,
    при которых снижение попадает в карантин.

    Возвращает (красивая цена, направление 'up'/'down', min база, max база).
    Рекомендую max базу: покупатель платит столько же, а цена до СПП выше.
    """
    pre0, _, w0 = price_chain(base, disc, spp)
    for step, direction in ((+1, "up"), (-1, "down")):
        target = next_pretty(w0, step)
        ok = [
            b for b in bases_for(target, disc, spp)
            if (promo_cap is None or price_chain(b, disc, spp)[0] <= promo_cap)
            and price_chain(b, disc, spp)[0] <= threshold
            and not in_quarantine(pre0, price_chain(b, disc, spp)[0])
        ]
        if ok:
            return target, direction, min(ok), max(ok)
    return None


def spp_sensitivity(base, disc, spp, delta=1):
    """Цена с кошельком при СПП на delta п.п. ниже и выше текущей."""
    return price_chain(base, disc, spp - delta)[2], price_chain(base, disc, spp + delta)[2]


def reduction_plan(base, disc, spp, steps_bases):
    """План снижения по шагам: для каждой базы - цена до СПП, изменение к исходной,
    кратность к предыдущему шагу, цена после СПП и с кошельком."""
    pre0 = price_chain(base, disc, spp)[0]
    prev = pre0
    plan = []
    for b in steps_bases:
        pre, after, wallet = price_chain(b, disc, spp)
        plan.append(dict(base=b, pre=pre, change=pre / pre0 - 1,
                         ratio=quarantine_ratio(prev, pre), after=after, wallet=wallet,
                         quarantine=in_quarantine(prev, pre)))
        prev = pre
    return plan


def pre_price_range_for_wallet(target_wallet, spp, lo=1, hi=2000):
    """Диапазон цены до СПП (с шагом 0,01 ₽), дающий заданную цену с кошельком."""
    found = [F(c, 100) for c in range(lo * 100, hi * 100)
             if price_chain(F(c, 100), 0, spp)[2] == target_wallet]
    return (min(found), max(found)) if found else None
