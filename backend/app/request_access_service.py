from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from secrets import token_urlsafe

from .config import Settings
from .repository import RequestCreationResult, create_request


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _isoformat(value: datetime) -> str:
    return value.isoformat()


def create_request_access(
    database_path: Path,
    settings: Settings,
    payload: dict[str, object],
) -> RequestCreationResult:
    now = _utc_now()
    created_at = _isoformat(now)
    updated_at = created_at
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
        request_payload=payload,
        electronic_status=electronic_status,
        paper_status=paper_status,
        delivery_token_candidate=delivery_token_candidate,
        created_at=created_at,
        updated_at=updated_at,
        email_job=email_job,
    )
