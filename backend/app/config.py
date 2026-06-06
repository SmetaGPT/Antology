from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    api_prefix: str
    cors_origins: list[str]
    public_base_url: str
    database_path: Path
    book_storage_dir: Path
    download_token_ttl_hours: int
    delivery_delay_minutes: int
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    smtp_use_tls: bool
    email_max_retries: int
    worker_poll_interval_seconds: int
    admin_email: str
    admin_password: str
    secret_key: str


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _env_flag(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def get_settings() -> Settings:
    database_path = Path(os.getenv("DATABASE_PATH", "backend/data/leads.db"))
    book_storage_dir = Path(os.getenv("BOOK_STORAGE_DIR", "backend/data/books"))

    return Settings(
        app_name=os.getenv("APP_NAME", "Antology API"),
        app_env=os.getenv("APP_ENV", "development"),
        api_prefix=os.getenv("API_PREFIX", "/api"),
        cors_origins=_split_csv(os.getenv("CORS_ORIGINS", "http://localhost:5173")),
        public_base_url=os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:8000").rstrip("/"),
        database_path=database_path,
        book_storage_dir=book_storage_dir,
        download_token_ttl_hours=int(os.getenv("DOWNLOAD_TOKEN_TTL_HOURS", "72")),
        delivery_delay_minutes=int(os.getenv("DELIVERY_DELAY_MINUTES", "30")),
        smtp_host=os.getenv("SMTP_HOST", "localhost"),
        smtp_port=int(os.getenv("SMTP_PORT", "1025")),
        smtp_username=os.getenv("SMTP_USERNAME", ""),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        smtp_from_email=os.getenv("SMTP_FROM_EMAIL", "noreply@example.com"),
        smtp_use_tls=_env_flag("SMTP_USE_TLS", False),
        email_max_retries=int(os.getenv("EMAIL_MAX_RETRIES", "3")),
        worker_poll_interval_seconds=int(os.getenv("WORKER_POLL_INTERVAL_SECONDS", "15")),
        admin_email=os.getenv("ADMIN_EMAIL", "admin@example.com"),
        admin_password=os.getenv("ADMIN_PASSWORD", "change-me"),
        secret_key=os.getenv("SECRET_KEY", "dev-secret-key"),
    )
