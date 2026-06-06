from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .repository import (
    create_admin_event,
    create_email_job,
    get_request,
    update_request_paper_review,
)


@dataclass(frozen=True)
class PaperDecisionResult:
    request_id: int
    paper_status: str
    email_job_id: int
    admin_event_id: int


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _render_paper_approval_email(pickup_info: str, admin_note: str | None) -> tuple[str, str]:
    note_block = f"\n\nКомментарий администратора:\n{admin_note}" if admin_note else ""
    subject = "Решение по печатному экземпляру Антологии"
    body = (
        "Ваш запрос на печатное издание одобрен.\n\n"
        "Информация о получении:\n"
        f"{pickup_info}{note_block}\n\n"
        "Если у вас изменились планы, пожалуйста, ответьте на это письмо."
    )
    return subject, body


def _render_paper_rejection_email(admin_note: str) -> tuple[str, str]:
    subject = "Решение по печатному экземпляру Антологии"
    body = (
        "По вашему запросу на печатное издание принято отрицательное решение.\n\n"
        "Комментарий администратора:\n"
        f"{admin_note}\n\n"
        "При необходимости вы можете позже отправить новую заявку."
    )
    return subject, body


def apply_paper_decision(
    database_path: Path,
    *,
    admin_user_id: int,
    request_id: int,
    decision: str,
    pickup_info: str,
    admin_note: str,
) -> PaperDecisionResult:
    request_row = get_request(database_path, request_id)
    if request_row is None:
        raise LookupError("Request was not found")

    if str(request_row["paper_status"]) != "review":
        raise ValueError("Paper decision can be applied only to requests in review status")

    if str(request_row["format"]) not in {"paper", "both"}:
        raise ValueError("Paper decision is not available for this request")

    cleaned_pickup_info = pickup_info.strip()
    cleaned_admin_note = admin_note.strip()
    now = _utc_now().isoformat()

    if decision == "approve":
        if not cleaned_pickup_info:
            raise ValueError("Pickup information is required for approval")
        next_status = "approved"
        subject, body = _render_paper_approval_email(
            cleaned_pickup_info,
            cleaned_admin_note or None,
        )
        stored_note = cleaned_admin_note or None
        stored_pickup_info = cleaned_pickup_info
        event_type = "paper_request_approved"
        email_kind = "paper_pickup"
    elif decision == "reject":
        if not cleaned_admin_note:
            raise ValueError("Admin note is required for rejection")
        next_status = "rejected"
        subject, body = _render_paper_rejection_email(cleaned_admin_note)
        stored_note = cleaned_admin_note
        stored_pickup_info = None
        event_type = "paper_request_rejected"
        email_kind = "paper_rejected"
    else:
        raise ValueError("Unsupported paper decision")

    update_request_paper_review(
        database_path,
        request_id=request_id,
        next_paper_status=next_status,
        pickup_info=stored_pickup_info,
        admin_note=stored_note,
        updated_at=now,
    )
    email_job_id = create_email_job(
        database_path,
        request_id=request_id,
        kind=email_kind,
        recipient_email=str(request_row["email"]),
        subject=subject,
        body=body,
        status="pending",
        send_after=now,
        created_at=now,
    )
    admin_event_id = create_admin_event(
        database_path,
        admin_user_id=admin_user_id,
        event_type=event_type,
        entity_type="request",
        entity_id=request_id,
        metadata={
            "decision": decision,
            "paper_status": next_status,
            "pickup_info": stored_pickup_info,
            "admin_note": stored_note,
            "email_job_id": email_job_id,
        },
        created_at=now,
    )

    return PaperDecisionResult(
        request_id=request_id,
        paper_status=next_status,
        email_job_id=email_job_id,
        admin_event_id=admin_event_id,
    )
