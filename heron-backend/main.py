"""Heron API — FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import _connect, init_db, seed_rules
from app.api.routes import auth, billing, freemium, health, report, scan

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("heron")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    db = await _connect()
    try:
        inserted = await seed_rules(db)
        if inserted:
            logger.info("Seeded %d EmpCo rules", inserted)
    finally:
        await db.close()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Heron API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for router in (health.router, auth.router, scan.router, freemium.router,
                   report.router, billing.router):
        app.include_router(router, prefix="/api/v1")
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
