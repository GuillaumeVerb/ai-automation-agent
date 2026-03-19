from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes_metrics import router as metrics_router
from app.api.routes_runs import router as runs_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    init_db()
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(runs_router)
app.include_router(metrics_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}
