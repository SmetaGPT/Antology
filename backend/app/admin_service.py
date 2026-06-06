from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import pbkdf2_hmac, sha256
import hmac
from pathlib import Path

from fastapi import HTTPException, Request, status

from .config import Settings
from .repository import (
    get_admin_dashboard_counts,
    get_admin_user_by_email,
    get_admin_user_by_id,
    list_requests_for_admin,
    upsert_admin_user,
)

SESSION_COOKIE_NAME = "antology_admin_session"
SESSION_TTL_HOURS = 8


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_password(settings: Settings, email: str, password: str) -> str:
    salt = f"antology-admin:{settings.secret_key}:{email}".encode("utf-8")
    digest = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return digest.hex()


def seed_admin_user(database_path: Path, settings: Settings) -> int:
    return upsert_admin_user(
        database_path,
        email=settings.admin_email,
        password_hash=_hash_password(settings, settings.admin_email, settings.admin_password),
        is_active=True,
        created_at=_utc_now().isoformat(),
    )


def authenticate_admin(
    database_path: Path,
    settings: Settings,
    *,
    email: str,
    password: str,
) -> dict[str, object] | None:
    admin_user = get_admin_user_by_email(database_path, email)
    if admin_user is None or int(admin_user["is_active"]) != 1:
        return None

    expected_hash = _hash_password(settings, email, password)
    if not hmac.compare_digest(str(admin_user["password_hash"]), expected_hash):
        return None

    return {"id": int(admin_user["id"]), "email": str(admin_user["email"])}


def create_admin_session(settings: Settings, admin_user_id: int) -> str:
    expires_at = int((_utc_now() + timedelta(hours=SESSION_TTL_HOURS)).timestamp())
    payload = f"{admin_user_id}:{expires_at}"
    signature = hmac.new(
        settings.secret_key.encode("utf-8"),
        payload.encode("utf-8"),
        sha256,
    ).hexdigest()
    return f"{payload}:{signature}"


def read_admin_session(settings: Settings, token: str) -> int | None:
    try:
        admin_user_id_raw, expires_at_raw, signature = token.split(":", maxsplit=2)
        admin_user_id = int(admin_user_id_raw)
        expires_at = int(expires_at_raw)
    except (TypeError, ValueError):
        return None

    payload = f"{admin_user_id}:{expires_at}"
    expected_signature = hmac.new(
        settings.secret_key.encode("utf-8"),
        payload.encode("utf-8"),
        sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        return None

    if expires_at < int(_utc_now().timestamp()):
        return None

    return admin_user_id


def require_admin_user(request: Request, database_path: Path, settings: Settings) -> dict[str, object]:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    admin_user_id = read_admin_session(settings, token) if token else None
    if admin_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/admin/login"},
        )

    admin_user = get_admin_user_by_id(database_path, admin_user_id)
    if admin_user is None or int(admin_user["is_active"]) != 1:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/admin/login"},
        )

    return {"id": int(admin_user["id"]), "email": str(admin_user["email"])}


def build_dashboard_context(
    database_path: Path,
    *,
    request_format: str | None,
    electronic_status: str | None,
    paper_status: str | None,
) -> dict[str, object]:
    return {
        "counts": get_admin_dashboard_counts(database_path),
        "requests": list_requests_for_admin(
            database_path,
            request_format=request_format,
            electronic_status=electronic_status,
            paper_status=paper_status,
        ),
        "filters": {
            "format": request_format or "",
            "electronic_status": electronic_status or "",
            "paper_status": paper_status or "",
        },
    }
