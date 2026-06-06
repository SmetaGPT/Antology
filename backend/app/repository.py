from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

from .db import connect


@dataclass(frozen=True)
class RequestCreationResult:
    request_id: int
    electronic_status: str
    paper_status: str
    delivery_token_candidate: str | None
    email_job_id: int | None
    send_after: str | None


@dataclass(frozen=True)
class DownloadTokenResult:
    token: str
    token_id: int
    request_id: int
    book_version_id: int
    expires_at: str


def create_request(
    database_path: Path,
    request_payload: dict[str, object],
    electronic_status: str,
    paper_status: str,
    delivery_token_candidate: str | None,
    created_at: str,
    updated_at: str,
    email_job: dict[str, object] | None = None,
) -> RequestCreationResult:
    with connect(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO requests (
                first_name,
                last_name,
                organization,
                position,
                email,
                phone,
                purpose,
                format,
                consent,
                electronic_status,
                paper_status,
                paper_pickup_info,
                paper_admin_note,
                delivery_token_candidate,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request_payload["first_name"],
                request_payload["last_name"],
                request_payload.get("organization"),
                request_payload.get("position"),
                request_payload["email"],
                request_payload.get("phone"),
                request_payload["purpose"],
                request_payload["format"],
                1 if request_payload["consent"] else 0,
                electronic_status,
                paper_status,
                None,
                None,
                delivery_token_candidate,
                created_at,
                updated_at,
            ),
        )
        request_id = int(cursor.lastrowid)

        email_job_id: int | None = None
        send_after: str | None = None

        if email_job is not None:
            job_cursor = connection.execute(
                """
                INSERT INTO email_jobs (
                    request_id,
                    kind,
                    recipient_email,
                    subject,
                    body,
                    status,
                    send_after,
                    attempt_count,
                    last_error,
                    sent_at,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request_id,
                    email_job["kind"],
                    email_job["recipient_email"],
                    email_job["subject"],
                    email_job["body"],
                    email_job["status"],
                    email_job["send_after"],
                    email_job["attempt_count"],
                    email_job["last_error"],
                    email_job["sent_at"],
                    email_job["created_at"],
                ),
            )
            email_job_id = int(job_cursor.lastrowid)
            send_after = str(email_job["send_after"])

        connection.commit()

    return RequestCreationResult(
        request_id=request_id,
        electronic_status=electronic_status,
        paper_status=paper_status,
        delivery_token_candidate=delivery_token_candidate,
        email_job_id=email_job_id,
        send_after=send_after,
    )


def get_request(database_path: Path, request_id: int) -> sqlite3.Row | None:
    with connect(database_path) as connection:
        return connection.execute(
            "SELECT * FROM requests WHERE id = ?",
            (request_id,),
        ).fetchone()


def get_email_job(database_path: Path, job_id: int) -> sqlite3.Row | None:
    with connect(database_path) as connection:
        return connection.execute(
            "SELECT * FROM email_jobs WHERE id = ?",
            (job_id,),
        ).fetchone()


def list_email_jobs(database_path: Path, request_id: int) -> list[sqlite3.Row]:
    with connect(database_path) as connection:
        return connection.execute(
            "SELECT * FROM email_jobs WHERE request_id = ? ORDER BY id ASC",
            (request_id,),
        ).fetchall()


def list_due_email_jobs(
    database_path: Path,
    *,
    send_before: str,
    max_attempts: int,
    limit: int = 25,
) -> list[sqlite3.Row]:
    with connect(database_path) as connection:
        return connection.execute(
            """
            SELECT *
            FROM email_jobs
            WHERE status = 'pending'
              AND send_after <= ?
              AND attempt_count < ?
            ORDER BY send_after ASC, id ASC
            LIMIT ?
            """,
            (send_before, max_attempts, limit),
        ).fetchall()


def mark_email_job_sent(database_path: Path, job_id: int, sent_at: str) -> None:
    with connect(database_path) as connection:
        job = connection.execute(
            "SELECT id, request_id, kind FROM email_jobs WHERE id = ?",
            (job_id,),
        ).fetchone()
        if job is None:
            raise LookupError(f"Email job {job_id} was not found")

        connection.execute(
            """
            UPDATE email_jobs
            SET status = 'sent',
                sent_at = ?,
                last_error = NULL
            WHERE id = ?
            """,
            (sent_at, job_id),
        )

        if job["kind"] == "electronic_link":
            connection.execute(
                """
                UPDATE requests
                SET electronic_status = 'sent',
                    updated_at = ?
                WHERE id = ?
                """,
                (sent_at, job["request_id"]),
            )

        connection.commit()


def mark_email_job_failed(
    database_path: Path,
    *,
    job_id: int,
    failed_at: str,
    error_message: str,
    max_attempts: int,
) -> None:
    with connect(database_path) as connection:
        job = connection.execute(
            """
            SELECT id, request_id, kind, attempt_count
            FROM email_jobs
            WHERE id = ?
            """,
            (job_id,),
        ).fetchone()
        if job is None:
            raise LookupError(f"Email job {job_id} was not found")

        next_attempt_count = int(job["attempt_count"]) + 1
        next_status = "failed" if next_attempt_count >= max_attempts else "pending"

        connection.execute(
            """
            UPDATE email_jobs
            SET status = ?,
                attempt_count = ?,
                last_error = ?,
                sent_at = NULL
            WHERE id = ?
            """,
            (next_status, next_attempt_count, error_message[:500], job_id),
        )

        if next_status == "failed" and job["kind"] == "electronic_link":
            connection.execute(
                """
                UPDATE requests
                SET electronic_status = 'failed',
                    updated_at = ?
                WHERE id = ?
                """,
                (failed_at, job["request_id"]),
            )

        connection.commit()


def create_book_version(
    database_path: Path,
    *,
    title: str,
    version_label: str,
    file_path: str,
    file_name: str,
    file_size: int,
    checksum: str,
    is_active: bool,
    uploaded_at: str,
) -> int:
    with connect(database_path) as connection:
        if is_active:
            connection.execute("UPDATE book_versions SET is_active = 0")

        cursor = connection.execute(
            """
            INSERT INTO book_versions (
                title,
                version_label,
                file_path,
                file_name,
                file_size,
                checksum,
                is_active,
                uploaded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                version_label,
                file_path,
                file_name,
                file_size,
                checksum,
                1 if is_active else 0,
                uploaded_at,
            ),
        )
        connection.commit()
        return int(cursor.lastrowid)


def get_active_book_version(database_path: Path) -> sqlite3.Row | None:
    with connect(database_path) as connection:
        return connection.execute(
            "SELECT * FROM book_versions WHERE is_active = 1 ORDER BY id DESC LIMIT 1"
        ).fetchone()


def create_download_token(
    database_path: Path,
    *,
    request_id: int,
    book_version_id: int,
    raw_token: str,
    expires_at: str,
    created_at: str,
) -> DownloadTokenResult:
    token_hash = sha256(raw_token.encode("utf-8")).hexdigest()

    with connect(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO download_tokens (
                request_id,
                book_version_id,
                token_hash,
                expires_at,
                used_count,
                last_used_at,
                created_at
            ) VALUES (?, ?, ?, ?, 0, NULL, ?)
            """,
            (
                request_id,
                book_version_id,
                token_hash,
                expires_at,
                created_at,
            ),
        )
        connection.commit()
        token_id = int(cursor.lastrowid)

    return DownloadTokenResult(
        token=raw_token,
        token_id=token_id,
        request_id=request_id,
        book_version_id=book_version_id,
        expires_at=expires_at,
    )


def resolve_download_token(database_path: Path, raw_token: str) -> sqlite3.Row | None:
    token_hash = sha256(raw_token.encode("utf-8")).hexdigest()

    with connect(database_path) as connection:
        return connection.execute(
            """
            SELECT
                dt.id,
                dt.request_id,
                dt.book_version_id,
                dt.expires_at,
                dt.used_count,
                dt.last_used_at,
                dt.created_at,
                bv.title,
                bv.version_label,
                bv.file_path,
                bv.file_name,
                bv.file_size,
                bv.checksum,
                bv.is_active,
                bv.uploaded_at
            FROM download_tokens dt
            JOIN book_versions bv ON bv.id = dt.book_version_id
            WHERE dt.token_hash = ?
            """,
            (token_hash,),
        ).fetchone()


def mark_download_token_used(database_path: Path, token_id: int, used_at: str) -> None:
    with connect(database_path) as connection:
        connection.execute(
            """
            UPDATE download_tokens
            SET used_count = used_count + 1,
                last_used_at = ?
            WHERE id = ?
            """,
            (used_at, token_id),
        )
        connection.commit()


def get_download_token_state(database_path: Path, token_id: int) -> sqlite3.Row | None:
    with connect(database_path) as connection:
        return connection.execute(
            "SELECT * FROM download_tokens WHERE id = ?",
            (token_id,),
        ).fetchone()


def upsert_admin_user(
    database_path: Path,
    *,
    email: str,
    password_hash: str,
    is_active: bool,
    created_at: str,
) -> int:
    with connect(database_path) as connection:
        existing = connection.execute(
            "SELECT id FROM admin_users WHERE email = ?",
            (email,),
        ).fetchone()

        if existing is None:
            cursor = connection.execute(
                """
                INSERT INTO admin_users (email, password_hash, is_active, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (email, password_hash, 1 if is_active else 0, created_at),
            )
            connection.commit()
            return int(cursor.lastrowid)

        connection.execute(
            """
            UPDATE admin_users
            SET password_hash = ?,
                is_active = ?
            WHERE id = ?
            """,
            (password_hash, 1 if is_active else 0, existing["id"]),
        )
        connection.commit()
        return int(existing["id"])


def get_admin_user_by_email(database_path: Path, email: str) -> sqlite3.Row | None:
    with connect(database_path) as connection:
        return connection.execute(
            "SELECT * FROM admin_users WHERE email = ?",
            (email,),
        ).fetchone()


def get_admin_user_by_id(database_path: Path, admin_user_id: int) -> sqlite3.Row | None:
    with connect(database_path) as connection:
        return connection.execute(
            "SELECT * FROM admin_users WHERE id = ?",
            (admin_user_id,),
        ).fetchone()


def get_admin_dashboard_counts(database_path: Path) -> dict[str, int]:
    with connect(database_path) as connection:
        request_counts = connection.execute(
            """
            SELECT
                COUNT(*) AS total_requests,
                SUM(CASE WHEN electronic_status = 'sent' THEN 1 ELSE 0 END) AS electronic_sent,
                SUM(CASE WHEN electronic_status = 'failed' THEN 1 ELSE 0 END) AS electronic_failed,
                SUM(CASE WHEN paper_status = 'review' THEN 1 ELSE 0 END) AS paper_review,
                SUM(CASE WHEN paper_status = 'approved' THEN 1 ELSE 0 END) AS paper_approved,
                SUM(CASE WHEN paper_status = 'rejected' THEN 1 ELSE 0 END) AS paper_rejected
            FROM requests
            """
        ).fetchone()

    return {
        "total_requests": int(request_counts["total_requests"] or 0),
        "electronic_sent": int(request_counts["electronic_sent"] or 0),
        "electronic_failed": int(request_counts["electronic_failed"] or 0),
        "paper_review": int(request_counts["paper_review"] or 0),
        "paper_approved": int(request_counts["paper_approved"] or 0),
        "paper_rejected": int(request_counts["paper_rejected"] or 0),
    }


def list_requests_for_admin(
    database_path: Path,
    *,
    request_format: str | None = None,
    electronic_status: str | None = None,
    paper_status: str | None = None,
) -> list[sqlite3.Row]:
    filters: list[str] = []
    values: list[object] = []

    if request_format:
        filters.append("format = ?")
        values.append(request_format)

    if electronic_status:
        filters.append("electronic_status = ?")
        values.append(electronic_status)

    if paper_status:
        filters.append("paper_status = ?")
        values.append(paper_status)

    query = "SELECT * FROM requests"
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY created_at DESC, id DESC"

    with connect(database_path) as connection:
        return connection.execute(query, values).fetchall()


def create_email_job(
    database_path: Path,
    *,
    request_id: int,
    kind: str,
    recipient_email: str,
    subject: str,
    body: str,
    status: str,
    send_after: str,
    created_at: str,
) -> int:
    with connect(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO email_jobs (
                request_id,
                kind,
                recipient_email,
                subject,
                body,
                status,
                send_after,
                attempt_count,
                last_error,
                sent_at,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, NULL, NULL, ?)
            """,
            (
                request_id,
                kind,
                recipient_email,
                subject,
                body,
                status,
                send_after,
                created_at,
            ),
        )
        connection.commit()
        return int(cursor.lastrowid)


def update_request_paper_review(
    database_path: Path,
    *,
    request_id: int,
    next_paper_status: str,
    pickup_info: str | None,
    admin_note: str | None,
    updated_at: str,
) -> None:
    with connect(database_path) as connection:
        connection.execute(
            """
            UPDATE requests
            SET paper_status = ?,
                paper_pickup_info = ?,
                paper_admin_note = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                next_paper_status,
                pickup_info,
                admin_note,
                updated_at,
                request_id,
            ),
        )
        connection.commit()


def create_admin_event(
    database_path: Path,
    *,
    admin_user_id: int,
    event_type: str,
    entity_type: str,
    entity_id: int,
    metadata: dict[str, object],
    created_at: str,
) -> int:
    with connect(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO admin_events (
                admin_user_id,
                event_type,
                entity_type,
                entity_id,
                metadata_json,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                admin_user_id,
                event_type,
                entity_type,
                entity_id,
                json.dumps(metadata, ensure_ascii=True),
                created_at,
            ),
        )
        connection.commit()
        return int(cursor.lastrowid)


def list_admin_events(
    database_path: Path,
    *,
    entity_type: str,
    entity_id: int,
) -> list[sqlite3.Row]:
    with connect(database_path) as connection:
        return connection.execute(
            """
            SELECT *
            FROM admin_events
            WHERE entity_type = ? AND entity_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (entity_type, entity_id),
        ).fetchall()
