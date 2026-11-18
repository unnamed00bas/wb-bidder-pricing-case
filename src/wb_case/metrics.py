"""Задание 6. Показатели для руководителя (по товару, за вчера и среднее за 7 дней)."""


def profit_after_ads(buyouts, profit_per_buyout, ad_spend):
    """1. Прибыль после рекламы = Σ(выкупы × прибыль до рекламы) − расход на рекламу."""
    return buyouts * profit_per_buyout - ad_spend


def cpm_margin(breakeven_cpm, actual_cpm):
    """2. Запас по CPM. Отрицательный - реклама в убытке: снизить ставку или выйти."""
    return breakeven_cpm - actual_cpm


def change_vs(current, base):
    """3. Изменение заказов / цены с кошельком к 7 дням назад."""
    return current / base - 1


def share_in_target(positions, target_max=8):
    """4. Доля снимков с местом в цели среди снимков при активной кампании.
    positions - места по снимкам активной кампании (None = нет в выдаче)."""
    if not positions:
        return 0.0
    return sum(1 for p in positions if p is not None and p <= target_max) / len(positions)


def days_of_stock(stock, avg_orders_7d):
    """5. Дни запаса = остаток / средние заказы за 7 дней."""
    return stock / avg_orders_7d
