"""Печатает все ключевые цифры решения. Запуск: python run_all.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from wb_case import data as D                                  # noqa: E402
from wb_case.pricing import (price_chain, suggest_pretty, bases_for, spp_sensitivity,  # noqa: E402
                             reduction_plan, quarantine_ratio, pre_price_range_for_wallet)
from wb_case.price_step import step_effect, next_step_forecast  # noqa: E402
from wb_case.bidder import replay, holding_bids, spend_summary, decide, tmin  # noqa: E402
from wb_case.ads import breakeven_cpm, ad_economics, loss_limited_impressions  # noqa: E402
from wb_case.metrics import days_of_stock                         # noqa: E402


def n(x, d=0):
    """Число в русском формате: пробел - разделитель тысяч, запятая - десятичная."""
    s = f"{float(x):,.{d}f}".replace(",", " ").replace(".", ",")
    return s.replace("-", "−")


def pct(x, d=1):
    return ("+" if x > 0 else "") + n(x * 100, d) + " %"


def h(title):
    print(f"\n=== {title} ===")


def task1():
    h("Задание 1. Цена с СПП и кошельком, красивая цена")
    for k, (b, d, s, cap) in D.GOODS.items():
        pre, after, w = price_chain(b, d, s)
        tgt, direction, bmin, bmax = suggest_pretty(b, d, s, cap)
        p2, a2, w2 = price_chain(bmax, d, s)
        lo, hi = spp_sensitivity(bmax, d, s)
        alt = price_chain(b, d, s, round_pre=True)[2]
        bmin_alt = min(bases_for(tgt, d, s, round_pre=True))
        print(f"{k}: до СПП {n(pre, 2)} ₽, после СПП {after} ₽, с кошельком {w} ₽ "
              f"(если округлять и цену до СПП: {alt} ₽)")
        print(f"   красивая {tgt} ₽ ({'вверх' if direction == 'up' else 'вниз'}), базы {bmin}–{bmax}, "
              f"беру {bmax}: до СПП {n(p2, 2)} ₽ ({pct(p2 / pre - 1, 2)}); "
              f"СПП −1/+1 п.п. -> {lo}/{hi} ₽; при округлении до СПП база от {bmin_alt}")
    b899 = bases_for(899, 75, 27)
    print(f"В вверх: 899 ₽ дают базы {min(b899)}–{max(b899)}, до СПП от "
          f"{n(price_chain(min(b899), 75, 27)[0], 2)} ₽ > потолка акции 1 250 ₽ -> идём вниз")
    b, d, s, _ = D.GOODS["Б"]
    pre0 = price_chain(b, d, s)[0]
    target = pre0 * 65 / 100
    print(f"Б −35 %: цель до СПП {n(target, 3)} ₽, кратность {n(quarantine_ratio(pre0, target), 3)} "
          f">= 1,5 -> одним шагом карантин")
    for i, st in enumerate(reduction_plan(b, d, s, [1800, 1454]), 1):
        print(f"   шаг {i}: база {st['base']}, до СПП {n(st['pre'], 2)} ₽ ({pct(st['change'], 2)}), "
              f"кратность {n(st['ratio'], 3)}, после СПП {st['after']} ₽, с кошельком {st['wallet']} ₽")
    b129 = bases_for(129, d, s)
    alt_pre = price_chain(max(b129), d, s)[0]
    print(f"   цену 129 ₽ дают базы {min(b129)}–{max(b129)}; при {max(b129)} до СПП "
          f"{n(alt_pre, 2)} ₽ ({pct(alt_pre / pre0 - 1)}); для покупателя 198 -> 129 ₽ ({pct(129 / 198 - 1)})")


def task2():
    h("Задание 2. Эффект шага цены")
    e = step_effect()
    f = next_step_forecast(e)
    print(f"Заказы {n(e['orders_before'], 2)} -> {n(e['orders_after'], 2)} шт/день ({pct(e['orders_change'])})")
    print(f"Цена с кошельком {n(e['wallet_before'], 1)} -> {n(e['wallet_after'], 1)} ₽ ({pct(e['wallet_change'])})")
    print(f"Прибыль {n(e['profit_before'], 1)} -> {n(e['profit_after'], 1)} ₽/день ({pct(e['profit_change'])}); "
          f"прибыль на ед. {pct(e['unit_profit_change'])}; шаг выгоден, пока падение заказов < {n(e['max_orders_drop'] * 100, 1)} %")
    print(f"Значимость: разница {n(e['diff'], 2)} шт, ст. ошибка {n(e['se'], 2)}, t = {n(e['t'], 2)}")
    print(f"Шаг до {D.NEXT_PRICE} ₽ (с кошельком {f['wallet_next']} ₽): эластичность {n(f['elasticity'], 2)} -> "
          f"{n(f['orders_elastic'], 2)} заказа, {n(f['profit_elastic'], 1)} ₽/день; линейно ({n(f['slope'], 3)} на 1 ₽) -> "
          f"{n(f['orders_linear'], 2)} заказа, {n(f['profit_linear'], 1)} ₽/день")
    print(f"Безубыточность: {n(f['breakeven_orders'], 2)} заказа/день (падение не больше {n(-f['allowed_drop'] * 100, 1)} %); "
          f"ранний откат: за 3 дня <= {f['early_rollback_sum']} заказов (среднее < {n(f['early_rollback_avg'], 1)})")
    print(f"Запас 900 шт: {n(f['stock_days_now'], 1)} дня сейчас, {n(f['stock_days_next'], 1)} дня после шага")
    r239, r249 = pre_price_range_for_wallet(239, 30), pre_price_range_for_wallet(249, 30)
    print(f"Красивые рядом с 244 ₽: 239 ₽ (до СПП {n(r239[0], 2)}–{n(r239[1], 2)} ₽), "
          f"249 ₽ ({n(r249[0], 2)}–{n(r249[1], 2)} ₽)")


def task3():
    h("Задание 3. Удержание места в поиске")
    before, after = holding_bids()
    spent, rate_h = spend_summary()
    print(f"Место <= 8 держали: до паузы {before} ₽, после включения {after} ₽")
    print(f"Потрачено за час {spent} ₽ из {n(D.TEST_BUDGET)} ₽; на 475–490 ₽ около {n(rate_h)} ₽/час")
    print("Прогон биддера по снимкам:")
    for r in replay():
        print(f"   {r['time']}  ставка {r['bid']:>4}  место {str(r['pos'] or '—'):>2}  "
              f"показы ~{r['impressions']:>2}  -> {r['decision']:>4}  {r['reason']}")
    s = {"bid": 419, "before_down": 432}
    new, why = decide(s, dict(time_min=tmin("12:30"), pos=9, age_min=0, campaign_active=True,
                              spend_5m=15, stop_flag=False, budget_left=3000), cap_be=1100)
    print(f"Если бы снижение 432 -> 419 ₽ делал биддер: в 12:30 откат к {new} ₽ ({why})")


def task5():
    h("Задание 5. Безубыточный CPM")
    be = breakeven_cpm(D.CTR, D.CR, D.BUYOUT, D.PROFIT_PER_BUYOUT)
    e290 = ad_economics(D.CTR, D.CR, D.BUYOUT, D.PROFIT_PER_BUYOUT, D.MIN_BID)
    e700 = ad_economics(D.CTR, D.CR, D.BUYOUT, D.PROFIT_PER_BUYOUT, D.BID_TO_HOLD)
    print(f"Безубыточный CPM = 1000 × {n(D.CTR*100)} % × {n(D.CR*100)} % × {n(D.BUYOUT*100)} % × {D.PROFIT_PER_BUYOUT} ₽ = {n(be, 1)} ₽")
    print(f"На 1000 показов: {n(e700['clicks'])} кликов, {n(e700['orders'], 2)} заказа, {n(e700['buyouts'], 2)} выкупа")
    print(f"При 290 ₽: {n(e290['result'], 1)} ₽ (ROMI {n(e290['romi'] * 100, 1)} %)")
    print(f"При 700 ₽: {n(e700['result'], 1)} ₽ (ROMI {n(e700['romi'] * 100, 1)} %), "
          f"реклама на 1 выкуп {n(e700['ad_cost_per_buyout'], 1)} ₽")
    print(f"CPC: безубыточный {n(e700['breakeven_cpc'], 2)} ₽, при 700 ₽ {n(e700['cpc'], 2)} ₽; "
          f"нужно в {n(e700['needed_multiplier'], 1)} раза лучше")
    imps, ords = loss_limited_impressions(3000, D.BID_TO_HOLD, be, e700["orders"])
    print(f"Лимит убытка 3 000 ₽ при 700 ₽: ~{n(imps)} показов, ~{n(ords)} заказов")


def task6():
    h("Задание 6. Метрики для руководителя (пример)")
    e = step_effect()
    print(f"Дни запаса: 900 / {n(e['orders_after'], 2)} = {n(days_of_stock(D.STOCK, e['orders_after']), 1)}")
    be = breakeven_cpm(D.CTR, D.CR, D.BUYOUT, D.PROFIT_PER_BUYOUT)
    print(f"Запас по CPM при ставке 700 ₽: {n(be - 700, 1)} ₽")


if __name__ == "__main__":
    task1(); task2(); task3(); task5(); task6()
