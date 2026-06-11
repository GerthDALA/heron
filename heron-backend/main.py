"""Heron API — FastAPI application entry point."""

import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import _connect, check_corpus_updates, init_db, seed_corpus, seed_rules
from app.api.routes import (
    admin, ads, auth, billing, corpus, evidence, freemium, health, report, scan,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("heron")


async def _cert_expiry_loop(interval_hours: int) -> None:
    """Periodically notify users whose certificates expire within 60 days."""
    from app.services.evidence_service import notify_expiring_certs

    while True:
        try:
            db = await _connect()
            try:
                sent = await notify_expiring_certs(db)
                if sent:
                    logger.info("Sent %d certificate expiry notices", sent)
            finally:
                await db.close()
        except Exception:
            logger.exception("Certificate expiry check failed")
        await asyncio.sleep(interval_hours * 3600)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    await init_db()
    db = await _connect()
    try:
        corpora, articles = await seed_corpus(db)
        logger.info("Legal corpus: %d corpora, %d articles", corpora, articles)
        inserted = await seed_rules(db)
        if inserted:
            logger.info("Seeded %d EmpCo rules", inserted)
        if settings.CORPUS_AUTO_RELOAD:
            changed = await check_corpus_updates(db)
            if changed:
                logger.info("Corpus reloaded for: %s", ", ".join(changed))
    finally:
        await db.close()
    expiry_task = asyncio.create_task(_cert_expiry_loop(settings.CERT_EXPIRY_CHECK_HOURS))
    yield
    expiry_task.cancel()


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
                   report.router, billing.router, corpus.router,
                   evidence.router, ads.router, admin.router):
        app.include_router(router, prefix="/api/v1")
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
