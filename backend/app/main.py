from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.api.router import api_router
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.services.seed import seed_if_empty


def _ensure_reject_category_column() -> None:
    """Idempotent lightweight migration for databases created before reject
    tiers existed (create_all does not alter existing tables)."""
    inspector = inspect(engine)
    if "reject_records" not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns("reject_records")}
    if "category" not in columns:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE reject_records ADD COLUMN category VARCHAR(20)"
                )
            )
            conn.execute(
                text("CREATE INDEX ix_reject_records_category ON reject_records (category)")
            )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _ensure_reject_category_column()
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
