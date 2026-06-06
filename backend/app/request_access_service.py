from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from secrets import token_urlsafe

from .config import Settings
from .repository import RequestCreationResult, count_recent_requests, create_request


class RateLimitExceededError(Exception):
    pass


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _isoformat(value: datetime) -> str:
    return value.isoformat()


def create_request_access(
    database_path: Path,
    settings: Settings,
    payload: dict[str, object],
) -> RequestCreationResult:
    if str(payload.get("honeypot") or "").strip():
        return RequestCreationResult(
            request_id=0,
            electronic_status="none",
            paper_status="none",
            delivery_token_candidate=None,
            email_job_id=None,
            send_after=None,
        )

    now = _utc_now()
    created_at = _isoformat(now)
    updated_at = created_at
    consent_at = created_at
    request_ip = str(payload.get("request_ip") or "").strip() or None
    request_email = str(payload["email"])
    rate_limit_cutoff = _isoformat(
        now - timedelta(minutes=settings.rate_limit_window_minutes)
    )
    email_count, ip_count = count_recent_requests(
        database_path,
        email=request_email,
        request_ip=request_ip,
        created_after=rate_limit_cutoff,
    )
    if email_count >= settings.rate_limit_max_per_email:
        raise RateLimitExceededError("Too many requests for this email address")
    if request_ip and ip_count >= settings.rate_limit_max_per_ip:
        raise RateLimitExceededError("Too many requests from this IP address")

    request_format = str(payload["format"])

    electronic_required = request_format in {"electronic", "both"}
    paper_required = request_format in {"paper", "both"}

    electronic_status = "pending" if electronic_required else "none"
    paper_status = "review" if paper_required else "none"
    delivery_token_candidate = token_urlsafe(24) if electronic_required else None

    email_job = None

    if electronic_required:
        send_after = now + timedelta(minutes=settings.delivery_delay_minutes)
        email_job = {
            "kind": "electronic_link",
            "recipient_email": payload["email"],
            "subject": "Электронный доступ к Антологии",
            "body": (
                "Заявка принята. После истечения заданной задержки "
                "пользователь должен получить ссылку на скачивание книги."
            ),
            "status": "pending",
            "send_after": _isoformat(send_after),
            "attempt_count": 0,
            "last_error": None,
            "sent_at": None,
            "created_at": created_at,
        }

    return create_request(
        database_path=database_path,
        request_payload={
            **payload,
            "consent_at": consent_at,
            "request_ip": request_ip,
            "user_agent": str(payload.get("user_agent") or "").strip() or None,
        },
        electronic_status=electronic_status,
        paper_status=paper_status,
        delivery_token_candidate=delivery_token_candidate,
        created_at=created_at,
        updated_at=updated_at,
        email_job=email_job,
    )
