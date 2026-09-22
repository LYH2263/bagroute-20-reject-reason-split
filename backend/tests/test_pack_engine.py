from app.services.pack_engine import (
    RejectCategory,
    StopItem,
    pack_route,
)

MAX_W, MAX_V = 5.0, 5.0


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


def test_reject_weight_only():
    """仅超重：重量超、体积不超。"""
    stops = [StopItem(1, 1, 9.0, 1.0, "超重件")]
    result = pack_route(stops, max_weight=MAX_W, max_volume=MAX_V)
    assert len(result.rejects) == 1
    rej = result.rejects[0]
    assert rej.item.stop_id == 1
    assert rej.category is RejectCategory.WEIGHT_ONLY
    assert "超重" in rej.reason and "超体积" not in rej.reason
    assert not result.bags


def test_reject_volume_only():
    """仅超体积：体积超、重量不超。"""
    stops = [StopItem(2, 1, 1.0, 9.0, "泡沫箱")]
    result = pack_route(stops, max_weight=MAX_W, max_volume=MAX_V)
    assert len(result.rejects) == 1
    rej = result.rejects[0]
    assert rej.item.stop_id == 2
    assert rej.category is RejectCategory.VOLUME_ONLY
    assert "超体积" in rej.reason and "超重" not in rej.reason
    assert not result.bags


def test_reject_weight_and_volume():
    """同时超重超体积：两项均超。"""
    stops = [StopItem(3, 1, 9.0, 9.0, "冰柜")]
    result = pack_route(stops, max_weight=MAX_W, max_volume=MAX_V)
    assert len(result.rejects) == 1
    rej = result.rejects[0]
    assert rej.item.stop_id == 3
    assert rej.category is RejectCategory.WEIGHT_AND_VOLUME
    assert "超重" in rej.reason and "超体积" in rej.reason
    assert not result.bags


def test_three_categories_in_one_route():
    """同一条路线三档各至少一条，分档互不混淆。"""
    stops = [
        StopItem(1, 1, 9.0, 1.0, "仅超重"),
        StopItem(2, 2, 1.0, 9.0, "仅超体积"),
        StopItem(3, 3, 9.0, 9.0, "双超"),
        StopItem(4, 4, 1.0, 1.0, "正常"),
    ]
    result = pack_route(stops, max_weight=MAX_W, max_volume=MAX_V)
    by_id = {r.item.stop_id: r for r in result.rejects}
    assert set(by_id) == {1, 2, 3}
    assert by_id[1].category is RejectCategory.WEIGHT_ONLY
    assert by_id[2].category is RejectCategory.VOLUME_ONLY
    assert by_id[3].category is RejectCategory.WEIGHT_AND_VOLUME
    # 正常件不被拒收且装入唯一一袋
    assert len(result.bags) == 1
    assert [i.stop_id for i in result.bags[0].items] == [4]


def test_threshold_unchanged_boundary():
    """恰好等于阈值不算超限（现网阈值判定不变）。"""
    stops = [StopItem(1, 1, MAX_W, MAX_V, "临界件")]
    result = pack_route(stops, max_weight=MAX_W, max_volume=MAX_V)
    assert not result.rejects
    assert len(result.bags) == 1


def test_volume_cap_triggers_new_bag():
    stops = [StopItem(1, 1, 1.0, 4.0), StopItem(2, 2, 1.0, 4.0)]
    result = pack_route(stops, max_weight=10.0, max_volume=5.0)
    assert len(result.bags) == 2
