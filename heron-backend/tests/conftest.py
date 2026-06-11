import asyncio
import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key_for_pytest_only_32ch")

BACKEND_DIR = Path(__file__).resolve().parent.parent
RULES_SEED_PATH = BACKEND_DIR / "app" / "db" / "rules_seed.json"


@pytest.fixture(scope="session")
def rules() -> list[dict]:
    return json.loads(RULES_SEED_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def regex_engine(rules):
    from app.engine.regex_engine import RegexEngine
    return RegexEngine(rules)


@pytest.fixture
def risk_calculator():
    from app.engine.risk_calculator import RiskCalculator
    return RiskCalculator()


@pytest.fixture
def test_db_path(tmp_path, monkeypatch):
    """Point the app at a throwaway SQLite database."""
    db_path = tmp_path / "test_heron.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path / "reports"))
    from app.config import get_settings
    get_settings.cache_clear()
    yield str(db_path)
    get_settings.cache_clear()


@pytest.fixture
def initialized_db(test_db_path, monkeypatch, tmp_path):
    """Initialise schema + seed corpus, certifications and rules."""
    monkeypatch.setenv("EVIDENCE_STORAGE_PATH", str(tmp_path / "evidence"))
    from app.config import get_settings
    get_settings.cache_clear()
    from app.database import _connect, init_db, seed_corpus, seed_rules

    async def setup():
        await init_db(test_db_path)
        db = await _connect(test_db_path)
        try:
            await seed_corpus(db)  # corpus first: rule_article_links FK
            await seed_rules(db)
        finally:
            await db.close()

    asyncio.run(setup())
    return test_db_path


@pytest.fixture
def fake_homepage(monkeypatch):
    async def fake_crawl_homepage(domain):
        return {
            "url": "https://marque.fr",
            "title": "Marque",
            "body_text": "Formule eco-responsable et naturelle. Carbon neutral by 2030.",
        }

    from app.engine import crawler
    monkeypatch.setattr(crawler, "crawl_homepage", fake_crawl_homepage)


@pytest.fixture
def client(initialized_db):
    """Synchronous test client against the full app (test DB already seeded)."""
    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as test_client:
        yield test_client
