from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app, ensure_schema
from app.models.models import DeliveryRoute, RejectRecord, SubscriberStop
from app.services.pack_engine import RejectCategory


def _seed_route_with_three_rejects():
    """造一条上限 8kg/18L 的路线，三档拒收各一条 + 正常件一条。"""
    db = SessionLocal()
    try:
        db.query(RejectRecord).delete()
        db.query(SubscriberStop).delete()
        db.query(DeliveryRoute).delete()
        route = DeliveryRoute(name="测试线", max_weight_kg=8.0, max_volume_l=18.0)
        db.add(route)
        db.flush()
        db.add_all(
            [
                SubscriberStop(route_id=route.id, seq=1, name="仅超重", weight_kg=9.5, volume_l=6.0),
                SubscriberStop(route_id=route.id, seq=2, name="仅超体积", weight_kg=3.0, volume_l=22.0),
                SubscriberStop(route_id=route.id, seq=3, name="双超", weight_kg=9.0, volume_l=20.0),
                SubscriberStop(route_id=route.id, seq=4, name="正常", weight_kg=2.0, volume_l=4.0),
            ]
        )
        db.commit()
        return route.id
    finally:
        db.close()


def test_rejects_filter_returns_only_requested_category():
    ensure_schema()
    rid = _seed_route_with_three_rejects()
    client = TestClient(app)

    # 触发装袋，生成三档拒收记录
    resp = client.post("/api/pack", json={"route_id": rid})
    assert resp.status_code == 200

    # 不带筛选：三档都在
    all_rows = client.get("/api/rejects").json()
    assert {r["category"] for r in all_rows} == {
        RejectCategory.WEIGHT_ONLY.value,
        RejectCategory.VOLUME_ONLY.value,
        RejectCategory.WEIGHT_AND_VOLUME.value,
    }

    # 每档筛选只返回该档
    for cat in RejectCategory:
        rows = client.get("/api/rejects", params={"category": cat.value}).json()
        assert rows, f"{cat.value} 应至少有一条"
        assert all(r["category"] == cat.value for r in rows), (
            f"筛选 {cat.value} 混入了其他档: {[r['category'] for r in rows]}"
        )

    # 非法分档参数应被拒绝（422），而不是返回全部
    bad = client.get("/api/rejects", params={"category": "bogus"})
    assert bad.status_code == 422
