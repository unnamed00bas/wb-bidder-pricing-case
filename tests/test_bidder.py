from wb_case.bidder import decide, replay, holding_bids, spend_summary, tmin


def snap(t="12:00", pos=7, active=True, age=0, spend=15, stop=False, budget=3000):
    return dict(time_min=tmin(t), pos=pos, age_min=age, campaign_active=active,
                spend_5m=spend, stop_flag=stop, budget_left=budget)


def test_holding_bids_and_spend():
    assert holding_bids() == ([432, 445], [475, 490])
    spent, rate_h = spend_summary()
    assert spent == 152 and round(rate_h) == 220


def test_replay_freezes_on_pause_and_restores_after():
    r = {x["time"]: x for x in replay()}
    assert r["12:00"]["decision"] == 375            # место 14: +12 %
    assert r["12:10"]["decision"] == 437            # место 10: +8 %
    assert r["12:35"]["decision"] == 419 and "ПАУЗА" in r["12:35"]["reason"]
    assert r["12:40"]["decision"] == 445 and "ПАУЗА" in r["12:40"]["reason"]   # на паузе не повышаем
    assert "после паузы" in r["12:45"]["reason"]


def test_rollback_after_own_decrease():
    s = {"bid": 419, "before_down": 432}
    assert decide(s, snap("12:30", pos=9), cap_be=1100)[0] == 432


def test_stop_flag_wins():
    s = {"bid": 448}
    assert decide(s, snap(pos=15, stop=True), cap_be=1100) == (448, "СТОП: флаг/бюджет - ставку не трогаем")


def test_cap_by_breakeven_cpm_alerts():
    assert decide({"bid": 480}, snap(pos=12), cap_be=500)[0] == 500   # упёрлись в потолок
    new, why = decide({"bid": 500}, snap(pos=12), cap_be=500)
    assert new == 500 and "алерт" in why


def test_stale_snapshot_and_missing_with_spend():
    assert "устарели" in decide({"bid": 400}, snap(pos=20, age=15), 1100)[1]
    assert "ошибка снимка" in decide({"bid": 400}, snap(pos=None, spend=10), 1100)[1]


def test_decrease_after_three_calm_snapshots_not_below_min():
    s = {"bid": 295}
    for t in ("12:00", "12:05"):
        assert decide(s, snap(t, pos=5), 1100)[0] == 295
    assert decide(s, snap("12:10", pos=5), 1100)[0] == 290

