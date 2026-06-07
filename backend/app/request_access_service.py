from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from secrets import token_urlsafe

from .admin_service import get_effective_delivery_delay_minutes
from .config import Settings
from .repository import RequestCreationResult, count_recent_requests, create_request


class RateLimitExceededError(Exception):
    pass


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _isoformat(value: datetime) -> str:
    return value.isoformat()


def _render_request_confirmation_email(
    request_format: str,
    *,
    delay_minutes: int,
) -> tuple[str, str]:
    subject = "Подтверждение получения заявки на Антологию"
    delay_text = (
        f"через {delay_minutes} мин."
        if delay_minutes < 60
        else (
            f"примерно через {delay_minutes // 60} ч."
            if delay_minutes % 60 == 0
            else f"через {delay_minutes} мин."
        )
    )

    if request_format == "electronic":
        body = (
            "Ваша заявка на получение электронной версии Антологии получена.\n\n"
            "Заявка рассматривается, ссылка на скачивание будет направлена "
            f"{delay_text}.\n\n"
            "Это письмо подтверждает только получение заявки."
        )
    elif request_format == "paper":
        body = (
            "Ваша заявка на получение бумажной версии Антологии получена.\n\n"
            "Заявка передана на рассмотрение комиссии. Информация о принятом решении "
            "и способе получения будет направлена в течение 5 рабочих дней.\n\n"
            "Это письмо подтверждает только получение заявки."
        )
    else:
        body = (
            "Ваша заявка на получение электронной и бумажной версии Антологии получена.\n\n"
            "Электронная заявка рассматривается, ссылка на скачивание будет направлена "
            f"{delay_text}.\n\n"
            "Заявка на бумажную версию передана на рассмотрение комиссии. Информация о "
            "принятом решении и способе получения будет направлена в течение 5 рабочих дней."
        )

    return subject, body


def build_request_confirmation_message(
    request_format: str,
    *,
    delay_minutes: int,
) -> str:
    if request_format == "electronic":
        return (
            "Заявка получена. Письмо с подтверждением отправляется сразу, "
            f"ссылка на скачивание будет направлена через {delay_minutes} мин."
        )
    if request_format == "paper":
        return (
            "Заявка получена. Письмо с подтверждением отправляется сразу. "
            "Заявка на бумажную версию передана на рассмотрение комиссии, "
            "информация о решении и способе получения будет направлена в течение 5 рабочих дней."
        )
    return (
        "Заявка получена. Письмо с подтверждением отправляется сразу, "
        f"ссылка на скачивание будет направлена через {delay_minutes} мин., "
        "а решение по бумажной версии и способ получения будут направлены в течение 5 рабочих дней."
    )


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
    delivery_delay_minutes = get_effective_delivery_delay_minutes(database_path, settings)

    electronic_required = request_format in {"electronic", "both"}
    paper_required = request_format in {"paper", "both"}

    electronic_status = "pending" if electronic_required else "none"
    paper_status = "review" if paper_required else "none"
    delivery_token_candidate = token_urlsafe(24) if electronic_required else None

    confirmation_subject, confirmation_body = _render_request_confirmation_email(
        request_format,
        delay_minutes=delivery_delay_minutes,
    )
    email_jobs: list[dict[str, object]] = [
        {
            "kind": "request_confirmation",
            "recipient_email": payload["email"],
            "subject": confirmation_subject,
            "body": confirmation_body,
            "status": "pending",
            "send_after": created_at,
            "attempt_count": 0,
            "last_error": None,
            "sent_at": None,
            "created_at": created_at,
        }
    ]

    if electronic_required:
        send_after = now + timedelta(minutes=delivery_delay_minutes)
        email_jobs.append(
            {
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
        )

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
        email_jobs=email_jobs,
    )
