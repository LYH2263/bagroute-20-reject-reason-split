from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.models import DeliveryRoute, SubscriberStop


def _seed_route_with_three_tier_stops() -> int:
    db = SessionLocal()
    try:
        route = DeliveryRoute(name="测试线", max_weight_kg=5.0, max_volume_l=5.0)
        db.add(route)
        db.flush()
        db.add_all(
            [
                # 仅超重
                SubscriberStop(route_id=route.id, seq=1, name="超重件", weight_kg=9.0, volume_l=1.0),
                # 仅超体积
                SubscriberStop(route_id=route.id, seq=2, name="泡货", weight_kg=1.0, volume_l=9.0),
                # 同时超重超体积
                SubscriberStop(route_id=route.id, seq=3, name="双超件", weight_kg=9.0, volume_l=9.0),
                # 正常件
                SubscriberStop(route_id=route.id, seq=4, name="正常件", weight_kg=1.0, volume_l=1.0),
            ]
        )
        db.commit()
        return route.id
    finally:
        db.close()


def test_rejects_filter_returns_only_requested_tier():
    with TestClient(app) as client:
        rid = _seed_route_with_three_tier_stops()
        resp = client.post("/api/pack", json={"route_id": rid})
        assert resp.status_code == 200

        # 不筛选：三档齐全
        all_rows = client.get("/api/rejects").json()
        assert len(all_rows) == 3
        assert {r["category"] for r in all_rows} == {
            "weight_only",
            "volume_only",
            "weight_volume",
        }

        # 每个分档筛选只返回该档
        for cat in ("weight_only", "volume_only", "weight_volume"):
            rows = client.get(f"/api/rejects?category={cat}").json()
            assert len(rows) == 1, cat
            assert rows[0]["category"] == cat
            # 筛选结果与接口数据一致：其余分档绝不混入
            assert all(r["category"] == cat for r in rows)

        wo = client.get("/api/rejects?category=weight_only").json()[0]
        assert wo["stop_name"] == "超重件"
        assert "超重" in wo["reason"] and "超体积" not in wo["reason"]

        vo = client.get("/api/rejects?category=volume_only").json()[0]
        assert vo["stop_name"] == "泡货"
        assert "超体积" in vo["reason"] and "超重" not in vo["reason"]

        wv = client.get("/api/rejects?category=weight_volume").json()[0]
        assert wv["stop_name"] == "双超件"
        assert "超重" in wv["reason"] and "超体积" in wv["reason"]


def test_rejects_filter_invalid_category_400():
    with TestClient(app) as client:
        resp = client.get("/api/rejects?category=overweight")
        assert resp.status_code == 400
