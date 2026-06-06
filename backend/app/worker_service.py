from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import Settings
from .download_service import issue_download_token
from .email_service import EmailPayload, SmtpEmailSender
from .repository import (
    list_due_email_jobs,
    mark_email_job_failed,
    mark_email_job_sent,
)


@dataclass(frozen=True)
class WorkerRunResult:
    processed_count: int
    sent_count: int
    failed_count: int


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _build_download_link(settings: Settings, token: str) -> str:
    return f"{settings.public_base_url}/download/{token}"


def _render_electronic_link_email(download_link: str) -> tuple[str, str]:
    subject = "Ссылка на электронную книгу Антологии"
    body = (
        "Спасибо за ваш интерес к проекту.\n\n"
        "Книга доступна по ссылке:\n"
        f"{download_link}\n\n"
        "Если ссылка перестанет работать, отправьте заявку повторно или свяжитесь с администратором проекта."
    )
    return subject, body


def process_due_email_jobs(
    database_path: Path,
    settings: Settings,
    *,
    email_sender: SmtpEmailSender | None = None,
) -> WorkerRunResult:
    now = _utc_now()
    due_jobs = list_due_email_jobs(
        database_path,
        send_before=now.isoformat(),
        max_attempts=settings.email_max_retries,
    )
    sender = email_sender or SmtpEmailSender(settings)

    processed_count = 0
    sent_count = 0
    failed_count = 0

    for job in due_jobs:
        processed_count += 1

        try:
            if job["kind"] == "electronic_link":
                token_result = issue_download_token(
                    database_path,
                    settings,
                    request_id=int(job["request_id"]),
                )
                download_link = _build_download_link(settings, token_result.token)
                subject, body = _render_electronic_link_email(download_link)
            elif job["kind"] in {"paper_pickup", "paper_rejected"}:
                subject = str(job["subject"])
                body = str(job["body"])
            else:
                raise ValueError(f"Unsupported email job kind: {job['kind']}")

            sender.send(
                EmailPayload(
                    recipient_email=str(job["recipient_email"]),
                    subject=subject,
                    body=body,
                )
            )
            mark_email_job_sent(database_path, int(job["id"]), now.isoformat())
            sent_count += 1
        except Exception as error:
            mark_email_job_failed(
                database_path,
                job_id=int(job["id"]),
                failed_at=now.isoformat(),
                error_message=str(error),
                max_attempts=settings.email_max_retries,
            )
            failed_count += 1

    return WorkerRunResult(
        processed_count=processed_count,
        sent_count=sent_count,
        failed_count=failed_count,
    )
