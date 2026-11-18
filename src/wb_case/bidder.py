"""Задание 3. Биддер: держать карточку на местах 1–8 с минимальной ставкой (CPM).

Решение принимается на каждом 5-минутном снимке выдачи. Порядок проверок важен:
сначала защиты (стоп, пауза, устаревшие данные), потом ставка.

Параметры стартовые: в условии их нет, они выведены из снимков и подбираются
по истории ставок и мест.
"""
from . import data as D

PARAMS = dict(
    target_max=8,              # цель: место <= 8
    comfort=6,                 # зона комфорта: место <= 6 (гистерезис, на 7-8 не дёргаем ставку)
    min_bid=D.MIN_BID,         # минимальная ставка WB
    wb_cap=D.WB_MAX_BID,       # потолок WB
    up_pct=0.08,               # шаг набора при месте 9-12
    up_far_pct=0.12,           # шаг набора при месте ниже 12 / нет в выдаче
    down_pct=0.03,             # шаг снижения
    min_step=10,               # минимальный шаг, ₽
    hold_snaps_before_down=3,  # снижаем после 3 спокойных снимков подряд
    max_snapshot_age_min=10,   # снимок старше - заморозка
    lost_bid_memory_min=60,    # «память о потере» места
)


def tmin(hhmm):
    """'12:35' -> минуты от полуночи."""
    h, m = map(int, hhmm.split(":"))
    return h * 60 + m


def decide(state, snap, cap_be, params=PARAMS):
    """Одно решение биддера на один снимок.

    state  - изменяемое состояние (dict), в нём обязательно 'bid' - текущая ставка;
    snap   - снимок: time_min, pos (None = нет в выдаче), age_min, campaign_active,
             spend_5m, stop_flag, budget_left;
    cap_be - безубыточный CPM карточки (ограничение сверху вместе с потолком WB).

    Возвращает (новая ставка, причина).
    """
    P = params
    s = state
    bid = s["bid"]
    cap = min(P["wb_cap"], cap_be)
    # 1. Флаг «стоп» / бюджет: проверяется прямо перед каждой записью ставки
    if snap["stop_flag"] or snap["budget_left"] <= 0:
        return bid, "СТОП: флаг/бюджет - ставку не трогаем"
    # 2. Пауза кампании: «нет в выдаче» вызвано паузой, а не ставкой
    if not snap["campaign_active"]:
        s["paused"] = True
        return bid, "ПАУЗА кампании - заморозка"
    # 3. Устаревшие данные
    if snap["age_min"] > P["max_snapshot_age_min"]:
        return bid, "данные устарели - заморозка"
    # 4. Первый снимок после включения - последняя рабочая ставка
    if s.get("paused"):
        s["paused"] = False
        s["cooldown"] = 1
        s["good_streak"] = 0
        return max(bid, s.get("last_good_bid", bid)), "после паузы: последняя рабочая ставка"
    if snap["pos"] is None and snap["spend_5m"] > 0:
        return bid, "нет в выдаче при расходе > 0 - ошибка снимка, алерт"
    # ставку меняем не чаще раза в 2 снимка, чтобы увидеть эффект
    if s.get("cooldown", 0) > 0:
        s["cooldown"] -= 1
        if snap["pos"] is not None and snap["pos"] <= P["target_max"]:
            s["last_good_bid"] = bid
        return bid, "ждём эффект прошлого изменения"
    pos = snap["pos"] if snap["pos"] is not None else 99
    # 5. Место > 8: набор или откат своего снижения, не выше потолка
    if pos > P["target_max"]:
        s["good_streak"] = 0
        s["lost_bid"], s["lost_t"] = bid, snap["time_min"]
        back = s.pop("before_down", None)
        if back is not None:
            new = min(cap, back)
        else:
            pct = P["up_far_pct"] if pos > 12 else P["up_pct"]
            new = min(cap, bid + max(P["min_step"], round(bid * pct)))
        if new == bid:
            return bid, "на потолке и ниже цели - алерт, решение человека"
        s["cooldown"] = 1
        if back is not None:
            return new, f"место {pos} > 8 после нашего снижения: откат"
        return new, f"место {pos} > 8: повышаем"
    # 6-7. Место в цели: держим; <= 6 три снимка подряд - осторожно снижаем
    s["last_good_bid"] = bid
    s.pop("before_down", None)
    s["good_streak"] = s.get("good_streak", 0) + 1 if pos <= P["comfort"] else 0
    if s["good_streak"] >= P["hold_snaps_before_down"]:
        floor = P["min_bid"]
        if "lost_bid" in s and snap["time_min"] - s["lost_t"] < P["lost_bid_memory_min"]:
            floor = max(floor, s["lost_bid"] + P["min_step"])
        new = max(floor, bid - max(P["min_step"], round(bid * P["down_pct"])))
        if new < bid:
            s["good_streak"] = 0
            s["cooldown"] = 1
            s["before_down"] = bid
            return new, f"место {pos} <= 6 три снимка: пробуем снизить"
    return bid, f"место {pos} в цели: держим"


def is_paused(hhmm, pause=D.PAUSE):
    return tmin(pause[0]) <= tmin(hhmm) < tmin(pause[1])


def replay(snapshots=D.SNAPSHOTS, cap_be=D.WB_MAX_BID, budget=D.TEST_BUDGET):
    """Прогон биддера по снимкам из условия: что бы он решил на каждом снимке
    (ставка в каждом снимке берётся фактическая)."""
    s, spent, out = {}, 0, []
    for t, bid, pos, _k1, _k2, _k3, spend in snapshots:
        s["bid"] = bid
        snap = dict(time_min=tmin(t), pos=pos, age_min=0, campaign_active=not is_paused(t),
                    spend_5m=spend, stop_flag=False, budget_left=budget - spent)
        new, why = decide(s, snap, cap_be)
        spent += spend
        out.append(dict(time=t, bid=bid, pos=pos, spend=spend,
                        impressions=round(spend / bid * 1000), decision=new, reason=why))
    return out


def holding_bids(snapshots=D.SNAPSHOTS, target_max=8):
    """Ставки, на которых место <= 8 держалось при активной кампании: до паузы и после."""
    before, after = set(), set()
    for t, bid, pos, *_rest in snapshots:
        if pos is None or pos > target_max or is_paused(t):
            continue
        (before if tmin(t) < tmin(D.PAUSE[0]) else after).add(bid)
    return sorted(before), sorted(after)


def spend_summary(snapshots=D.SNAPSHOTS, last_n=3):
    """Потрачено за час и оценка расхода в час на последних ставках (475-490 ₽)."""
    spent = sum(r[6] for r in snapshots)
    rate_h = sum(r[6] for r in snapshots[-last_n:]) / last_n * 12
    return spent, rate_h
