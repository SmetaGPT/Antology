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
    expose_api_docs: bool
    download_token_ttl_hours: int
    max_book_upload_mb: int
    delivery_delay_minutes: int
    rate_limit_window_minutes: int
    rate_limit_max_per_ip: int
    rate_limit_max_per_email: int
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


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _env_flag(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", maxsplit=1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _load_default_env_files() -> None:
    for candidate in (
        REPO_ROOT / ".env",
        BACKEND_ROOT / ".env",
        REPO_ROOT / ".env.production",
        BACKEND_ROOT / ".env.production",
    ):
        _load_env_file(candidate)


def get_settings() -> Settings:
    _load_default_env_files()
    app_env = os.getenv("APP_ENV", "development")
    database_path = Path(os.getenv("DATABASE_PATH", "backend/data/leads.db"))
    book_storage_dir = Path(os.getenv("BOOK_STORAGE_DIR", "backend/data/books"))

    return Settings(
        app_name=os.getenv("APP_NAME", "Antology API"),
        app_env=app_env,
        api_prefix=os.getenv("API_PREFIX", "/api"),
        cors_origins=_split_csv(os.getenv("CORS_ORIGINS", "http://localhost:5173")),
        public_base_url=os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:8000").rstrip("/"),
        database_path=database_path,
        book_storage_dir=book_storage_dir,
        expose_api_docs=_env_flag("EXPOSE_API_DOCS", app_env != "production"),
        download_token_ttl_hours=int(os.getenv("DOWNLOAD_TOKEN_TTL_HOURS", "72")),
        max_book_upload_mb=int(os.getenv("MAX_BOOK_UPLOAD_MB", "250")),
        delivery_delay_minutes=int(os.getenv("DELIVERY_DELAY_MINUTES", "30")),
        rate_limit_window_minutes=int(os.getenv("RATE_LIMIT_WINDOW_MINUTES", "60")),
        rate_limit_max_per_ip=int(os.getenv("RATE_LIMIT_MAX_PER_IP", "10")),
        rate_limit_max_per_email=int(os.getenv("RATE_LIMIT_MAX_PER_EMAIL", "3")),
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
