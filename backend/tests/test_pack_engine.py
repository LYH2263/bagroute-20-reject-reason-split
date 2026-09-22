from app.services.pack_engine import (
    RejectCategory,
    StopItem,
    classify_reject,
    pack_route,
)


def test_packs_in_route_order_splitting_bags():
    stops = [
        StopItem(1, 1, 2.0, 3.0),
        StopItem(2, 2, 2.5, 3.0),
        StopItem(3, 3, 1.0, 1.0),
    ]
    result = pack_route(stops, max_weight=4.0, max_volume=10.0)
    assert len(result.bags) == 2
    assert [i.stop_id for i in result.bags[0].items] == [1]
    assert [i.stop_id for i in result.bags[1].items] == [2, 3]
    assert not result.rejects


def test_volume_cap_triggers_new_bag():
    stops = [StopItem(1, 1, 1.0, 4.0), StopItem(2, 2, 1.0, 4.0)]
    result = pack_route(stops, max_weight=10.0, max_volume=5.0)
    assert len(result.bags) == 2


# —— 拒收三档：仅超重 / 仅超体积 / 同时超重超体积，各至少一条 ——

def test_reject_weight_only():
    stops = [StopItem(1, 1, 9.0, 1.0, "超重件"), StopItem(2, 2, 1.0, 1.0)]
    result = pack_route(stops, max_weight=5.0, max_volume=5.0)
    assert len(result.rejects) == 1
    rej = result.rejects[0]
    assert rej.item.stop_id == 1
    assert rej.category is RejectCategory.WEIGHT_ONLY
    assert "超重" in rej.reason and "超体积" not in rej.reason
    assert len(result.bags) == 1
    assert result.bags[0].items[0].stop_id == 2


def test_reject_volume_only():
    stops = [StopItem(1, 1, 1.0, 9.0, "泡货")]
    result = pack_route(stops, max_weight=5.0, max_volume=5.0)
    assert len(result.rejects) == 1
    rej = result.rejects[0]
    assert rej.category is RejectCategory.VOLUME_ONLY
    assert "超体积" in rej.reason and "超重" not in rej.reason
    assert not result.bags


def test_reject_weight_and_volume():
    stops = [StopItem(1, 1, 9.0, 9.0, "双超件")]
    result = pack_route(stops, max_weight=5.0, max_volume=5.0)
    assert len(result.rejects) == 1
    rej = result.rejects[0]
    assert rej.category is RejectCategory.WEIGHT_AND_VOLUME
    assert "超重" in rej.reason and "超体积" in rej.reason
    assert not result.bags


def test_three_tiers_in_one_run_are_distinctly_worded():
    stops = [
        StopItem(1, 1, 9.0, 1.0, "仅超重"),
        StopItem(2, 2, 1.0, 9.0, "仅超体积"),
        StopItem(3, 3, 9.0, 9.0, "双超"),
        StopItem(4, 4, 1.0, 1.0, "正常"),
    ]
    result = pack_route(stops, max_weight=5.0, max_volume=5.0)
    by_id = {r.item.stop_id: r for r in result.rejects}
    assert set(by_id) == {1, 2, 3}
    assert by_id[1].category is RejectCategory.WEIGHT_ONLY
    assert by_id[2].category is RejectCategory.VOLUME_ONLY
    assert by_id[3].category is RejectCategory.WEIGHT_AND_VOLUME
    # 三种文案互不相同，不允许含糊地写成同一句
    reasons = {by_id[i].reason for i in (1, 2, 3)}
    assert len(reasons) == 3
    assert result.bags[0].items[0].stop_id == 4


def test_threshold_unchanged_at_exact_cap_is_not_rejected():
    # 恰好等于阈值不拒收（现网判定：> 才超限）
    assert classify_reject(StopItem(1, 1, 5.0, 5.0), 5.0, 5.0) is None
    assert classify_reject(StopItem(2, 2, 5.000001, 1.0), 5.0, 5.0) is RejectCategory.WEIGHT_ONLY
