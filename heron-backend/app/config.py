"""Application settings, loaded from environment / .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "sqlite+aiosqlite:///./heron.db"
    ANTHROPIC_API_KEY: str = ""
    # Claude Sonnet model used for replacement generation (spec: claude-sonnet-4-5).
    CLAUDE_MODEL: str = "claude-sonnet-4-5"
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    RESEND_API_KEY: str = ""
    JWT_SECRET_KEY: str = "change_this_to_a_random_32_char_string"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 60 * 24 * 7  # 7 days
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]
    MAX_PAGES_STARTER: int = 500
    MAX_PAGES_BRAND: int = 3000
    SCAN_TIMEOUT_SECONDS: int = 600  # 10 minutes
    FREEMIUM_MAX_CLAIMS_VISIBLE: int = 1  # Show 1 full, redact rest
    HERON_FROM_EMAIL: str = "heron@yourdomain.com"
    FRONTEND_URL: str = "http://localhost:3000"
    REPORTS_DIR: str = "./reports"
    EVIDENCE_UPLOAD_MAX_MB: int = 10
    EVIDENCE_STORAGE_PATH: str = "./evidence"
    ADS_SCAN_MAX_CHARS: int = 50000
    ADS_SCAN_MIN_CHARS: int = 10
    CORPUS_AUTO_RELOAD: bool = True  # reload corpus on startup if files changed
    # SSRF guard: refuse to crawl private/loopback hosts. Set to true only
    # for local development against a mock storefront.
    CRAWLER_ALLOW_PRIVATE_HOSTS: bool = False
    CERT_EXPIRY_CHECK_HOURS: int = 24

    @property
    def sqlite_path(self) -> str:
        """Extract the plain file path from the sqlalchemy-style DATABASE_URL."""
        url = self.DATABASE_URL
        for prefix in ("sqlite+aiosqlite:///", "sqlite:///"):
            if url.startswith(prefix):
                return url[len(prefix):]
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
