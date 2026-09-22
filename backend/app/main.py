from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.api.router import api_router
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.services.seed import seed_if_empty


def ensure_schema() -> None:
    """create_all 只建新表；对既有开发库补齐后加的列（幂等、跨方言）。"""
    Base.metadata.create_all(bind=engine)
    insp = inspect(engine)
    if "reject_records" not in insp.get_table_names():
        return
    columns = {c["name"] for c in insp.get_columns("reject_records")}
    if "category" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE reject_records ADD COLUMN category VARCHAR(32)"))
    # 按旧版 reason 文案回填历史记录的分档
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE reject_records SET category = CASE "
                "WHEN reason LIKE '%超重%' AND reason LIKE '%超体积%' THEN 'weight_and_volume' "
                "WHEN reason LIKE '%超重%' THEN 'weight_only' "
                "WHEN reason LIKE '%超体积%' THEN 'volume_only' "
                "ELSE category END WHERE category IS NULL"
            )
        )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_schema()
    if settings.seed_on_empty:
        db = SessionLocal()
        try:
            seed_if_empty(db)
        finally:
            db.close()
    yield


app = FastAPI(title="BagRoute", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api")
