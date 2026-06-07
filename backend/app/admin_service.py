from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import pbkdf2_hmac, sha256
import hmac
from pathlib import Path
from typing import TypedDict

from fastapi import HTTPException, Request, status

from .book_admin_service import build_book_versions_context
from .config import Settings
from .email_service import get_mail_settings_debug_snapshot
from .repository import (
    count_book_versions,
    count_inbound_emails,
    count_requests_for_admin,
    get_admin_dashboard_counts,
    get_admin_user_by_email,
    get_admin_user_by_id,
    get_site_and_request_activity_summary,
    get_system_setting,
    list_inbound_emails_page,
    list_book_versions_page,
    list_requests_for_admin_page,
    upsert_admin_user,
)

SESSION_COOKIE_NAME = "antology_admin_session"
SESSION_TTL_HOURS = 8
ADMIN_LOGIN_PATH = "/ad/log"
BOOKS_PAGE_SIZE = 10
REQUESTS_PAGE_SIZE = 20
DELIVERY_DELAY_SETTING_KEY = "electronic_delivery_delay_minutes"


class AdminUserIdentity(TypedDict):
    id: int
    email: str


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_admin_email(email: str) -> str:
    return email.strip().lower()


def _hash_password(settings: Settings, email: str, password: str) -> str:
    normalized_email = _normalize_admin_email(email)
    salt = f"antology-admin:{settings.secret_key}:{normalized_email}".encode("utf-8")
    digest = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return digest.hex()


def seed_admin_user(database_path: Path, settings: Settings) -> int:
    normalized_email = _normalize_admin_email(settings.admin_email)
    return upsert_admin_user(
        database_path,
        email=normalized_email,
        password_hash=_hash_password(settings, normalized_email, settings.admin_password),
        is_active=True,
        created_at=_utc_now().isoformat(),
    )


def authenticate_admin(
    database_path: Path,
    settings: Settings,
    *,
    email: str,
    password: str,
) -> AdminUserIdentity | None:
    normalized_email = _normalize_admin_email(email)
    admin_user = get_admin_user_by_email(database_path, normalized_email)
    if admin_user is None or int(admin_user["is_active"]) != 1:
        return None

    expected_hash = _hash_password(settings, normalized_email, password)
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


def require_admin_user(request: Request, database_path: Path, settings: Settings) -> AdminUserIdentity:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    admin_user_id = read_admin_session(settings, token) if token else None
    if admin_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": ADMIN_LOGIN_PATH},
        )

    admin_user = get_admin_user_by_id(database_path, admin_user_id)
    if admin_user is None or int(admin_user["is_active"]) != 1:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": ADMIN_LOGIN_PATH},
        )

    return {"id": int(admin_user["id"]), "email": str(admin_user["email"])}


def get_effective_delivery_delay_minutes(database_path: Path, settings: Settings) -> int:
    stored_value = get_system_setting(database_path, DELIVERY_DELAY_SETTING_KEY)
    if stored_value is None:
        return settings.delivery_delay_minutes
    try:
        normalized = int(stored_value)
    except ValueError:
        return settings.delivery_delay_minutes
    return max(1, normalized)


def _build_pagination(total_count: int, page: int, page_size: int) -> dict[str, int]:
    normalized_total_pages = max(1, (total_count + page_size - 1) // page_size)
    normalized_page = min(max(1, page), normalized_total_pages)
    offset = (normalized_page - 1) * page_size
    return {
        "page": normalized_page,
        "page_size": page_size,
        "total_count": total_count,
        "total_pages": normalized_total_pages,
        "offset": offset,
    }


def build_dashboard_context(
    database_path: Path,
    settings: Settings,
) -> dict[str, object]:
    recent_requests = list_requests_for_admin_page(
        database_path,
        limit=5,
        offset=0,
    )
    book_context = build_book_versions_context(database_path)
    context: dict[str, object] = {
        "counts": get_admin_dashboard_counts(database_path),
        "activity_summary": get_site_and_request_activity_summary(database_path),
        "recent_requests": recent_requests,
        "active_version": book_context["active_version"],
        "delivery_delay_minutes": get_effective_delivery_delay_minutes(database_path, settings),
    }
    return context


def build_books_page_context(
    database_path: Path,
    *,
    page: int,
) -> dict[str, object]:
    total_count = count_book_versions(database_path)
    pagination = _build_pagination(total_count, page, BOOKS_PAGE_SIZE)
    book_context = build_book_versions_context(database_path)
    context: dict[str, object] = {
        "versions": list_book_versions_page(
            database_path,
            limit=pagination["page_size"],
            offset=pagination["offset"],
        ),
        "pagination": pagination,
        "active_version": book_context["active_version"],
    }
    return context


def build_requests_page_context(
    database_path: Path,
    *,
    request_format: str | None,
    electronic_status: str | None,
    paper_status: str | None,
    page: int,
) -> dict[str, object]:
    total_count = count_requests_for_admin(
        database_path,
        request_format=request_format,
        electronic_status=electronic_status,
        paper_status=paper_status,
    )
    pagination = _build_pagination(total_count, page, REQUESTS_PAGE_SIZE)
    context: dict[str, object] = {
        "requests": list_requests_for_admin_page(
            database_path,
            request_format=request_format,
            electronic_status=electronic_status,
            paper_status=paper_status,
            limit=pagination["page_size"],
            offset=pagination["offset"],
        ),
        "filters": {
            "format": request_format or "",
            "electronic_status": electronic_status or "",
            "paper_status": paper_status or "",
        },
        "pagination": pagination,
    }
    return context


def build_settings_page_context(
    database_path: Path,
    settings: Settings,
) -> dict[str, object]:
    context: dict[str, object] = {
        "delivery_delay_minutes": get_effective_delivery_delay_minutes(database_path, settings),
        "default_delivery_delay_minutes": settings.delivery_delay_minutes,
        "paper_review_days_text": "5 рабочих дней",
        "public_base_url": settings.public_base_url,
        "smtp_from_email": settings.smtp_from_email,
        "admin_email": settings.admin_email,
        "mail_settings": get_mail_settings_debug_snapshot(database_path, settings),
        "inbound_email_count": count_inbound_emails(database_path),
        "inbound_emails": list_inbound_emails_page(
            database_path,
            limit=10,
            offset=0,
        ),
    }
    return context
