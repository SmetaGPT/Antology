from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import Settings
from .download_service import issue_download_token
from .email_service import EmailPayload, ImapMailReceiver, SmtpEmailSender, get_effective_mail_settings
from .repository import (
    create_inbound_email,
    list_due_email_jobs,
    mark_email_job_failed,
    mark_email_job_sent,
)


@dataclass(frozen=True)
class WorkerRunResult:
    processed_count: int
    sent_count: int
    failed_count: int


@dataclass(frozen=True)
class MailSyncResult:
    processed_count: int
    imported_count: int
    duplicate_count: int


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
    sender = email_sender or SmtpEmailSender(settings, database_path=database_path)

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
            elif job["kind"] in {"request_confirmation", "paper_pickup", "paper_rejected"}:
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


def sync_incoming_emails(
    database_path: Path,
    settings: Settings,
    *,
    receiver: ImapMailReceiver | None = None,
    limit: int = 20,
) -> MailSyncResult:
    runtime_settings = get_effective_mail_settings(database_path, settings)
    if not runtime_settings.inbound_mail_enabled:
        return MailSyncResult(processed_count=0, imported_count=0, duplicate_count=0)

    active_receiver = receiver or ImapMailReceiver(settings, database_path=database_path)
    processed_count = 0
    imported_count = 0
    duplicate_count = 0
    imported_at = _utc_now().isoformat()

    for message in active_receiver.fetch_unseen(limit=limit):
        processed_count += 1
        imported = create_inbound_email(
            database_path,
            provider_key=runtime_settings.provider_key,
            mailbox_name=message.mailbox_name,
            message_uid=message.message_uid,
            message_id=message.message_id,
            from_email=message.from_email,
            from_name=message.from_name,
            subject=message.subject,
            body_text=message.body_text,
            received_at=message.received_at,
            imported_at=imported_at,
        )
        if imported:
            imported_count += 1
        else:
            duplicate_count += 1

    return MailSyncResult(
        processed_count=processed_count,
        imported_count=imported_count,
        duplicate_count=duplicate_count,
    )
