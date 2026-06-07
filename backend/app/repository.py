from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
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
    email_jobs: list[dict[str, object]] | None = None,
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
                consent_at,
                request_ip,
                user_agent,
                electronic_status,
                paper_status,
                paper_pickup_info,
                paper_admin_note,
                delivery_token_candidate,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                request_payload.get("consent_at"),
                request_payload.get("request_ip"),
                request_payload.get("user_agent"),
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

        for email_job in email_jobs or []:
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
            if email_job.get("kind") == "electronic_link":
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


def count_recent_requests(
    database_path: Path,
    *,
    email: str,
    request_ip: str | None,
    created_after: str,
) -> tuple[int, int]:
    with connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT
                SUM(CASE WHEN email = ? THEN 1 ELSE 0 END) AS email_count,
                SUM(CASE WHEN request_ip = ? THEN 1 ELSE 0 END) AS ip_count
            FROM requests
            WHERE created_at >= ?
            """,
            (email, request_ip, created_after),
        ).fetchone()

    return int(row["email_count"] or 0), int(row["ip_count"] or 0)


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


def list_book_versions(database_path: Path) -> list[sqlite3.Row]:
    with connect(database_path) as connection:
        return connection.execute(
            "SELECT * FROM book_versions ORDER BY uploaded_at DESC, id DESC"
        ).fetchall()


def count_book_versions(database_path: Path) -> int:
    with connect(database_path) as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM book_versions").fetchone()
    return int(row["count"] or 0)


def list_book_versions_page(
    database_path: Path,
    *,
    limit: int,
    offset: int,
) -> list[sqlite3.Row]:
    with connect(database_path) as connection:
        return connection.execute(
            """
            SELECT *
            FROM book_versions
            ORDER BY uploaded_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()


def get_book_version(database_path: Path, book_version_id: int) -> sqlite3.Row | None:
    with connect(database_path) as connection:
        return connection.execute(
            "SELECT * FROM book_versions WHERE id = ?",
            (book_version_id,),
        ).fetchone()


def activate_book_version(
    database_path: Path,
    *,
    book_version_id: int,
) -> None:
    with connect(database_path) as connection:
        row = connection.execute(
            "SELECT id FROM book_versions WHERE id = ?",
            (book_version_id,),
        ).fetchone()
        if row is None:
            raise LookupError("Book version was not found")

        connection.execute("UPDATE book_versions SET is_active = 0")
        connection.execute(
            "UPDATE book_versions SET is_active = 1 WHERE id = ?",
            (book_version_id,),
        )
        connection.commit()


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
            "SELECT id FROM admin_users WHERE lower(email) = lower(?)",
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
            SET email = ?,
                password_hash = ?,
                is_active = ?
            WHERE id = ?
            """,
            (email, password_hash, 1 if is_active else 0, existing["id"]),
        )
        connection.commit()
        return int(existing["id"])


def get_admin_user_by_email(database_path: Path, email: str) -> sqlite3.Row | None:
    with connect(database_path) as connection:
        return connection.execute(
            "SELECT * FROM admin_users WHERE lower(email) = lower(?)",
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


def get_request_activity_summary(database_path: Path) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    day_prefix = now.strftime("%Y-%m-%d")
    month_prefix = now.strftime("%Y-%m")
    year_prefix = now.strftime("%Y")

    with connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT
                SUM(CASE WHEN substr(created_at, 1, 10) = ? THEN 1 ELSE 0 END) AS day_requests,
                SUM(CASE WHEN substr(created_at, 1, 7) = ? THEN 1 ELSE 0 END) AS month_requests,
                SUM(CASE WHEN substr(created_at, 1, 4) = ? THEN 1 ELSE 0 END) AS year_requests,
                MAX(created_at) AS latest_request_at
            FROM requests
            """,
            (day_prefix, month_prefix, year_prefix),
        ).fetchone()

    return {
        "day_requests": int(row["day_requests"] or 0),
        "month_requests": int(row["month_requests"] or 0),
        "year_requests": int(row["year_requests"] or 0),
        "latest_request_at": row["latest_request_at"],
    }


def create_site_visit(
    database_path: Path,
    *,
    session_id: str,
    path: str,
    referrer: str | None,
    request_ip: str | None,
    user_agent: str | None,
    created_at: str,
) -> bool:
    with connect(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO site_visits (
                session_id,
                path,
                referrer,
                request_ip,
                user_agent,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                path,
                referrer,
                request_ip,
                user_agent,
                created_at,
            ),
        )
        connection.commit()
        return int(cursor.rowcount or 0) > 0


def get_site_and_request_activity_summary(database_path: Path) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    day_prefix = now.strftime("%Y-%m-%d")
    month_prefix = now.strftime("%Y-%m")
    year_prefix = now.strftime("%Y")

    with connect(database_path) as connection:
        visit_row = connection.execute(
            """
            SELECT
                SUM(CASE WHEN substr(created_at, 1, 10) = ? THEN 1 ELSE 0 END) AS day_visits,
                SUM(CASE WHEN substr(created_at, 1, 7) = ? THEN 1 ELSE 0 END) AS month_visits,
                SUM(CASE WHEN substr(created_at, 1, 4) = ? THEN 1 ELSE 0 END) AS year_visits,
                MAX(created_at) AS latest_visit_at
            FROM site_visits
            """,
            (day_prefix, month_prefix, year_prefix),
        ).fetchone()
        request_row = connection.execute(
            """
            SELECT
                SUM(CASE WHEN substr(created_at, 1, 10) = ? THEN 1 ELSE 0 END) AS day_requests,
                SUM(CASE WHEN substr(created_at, 1, 7) = ? THEN 1 ELSE 0 END) AS month_requests,
                SUM(CASE WHEN substr(created_at, 1, 4) = ? THEN 1 ELSE 0 END) AS year_requests,
                MAX(created_at) AS latest_request_at
            FROM requests
            """,
            (day_prefix, month_prefix, year_prefix),
        ).fetchone()

    def conversion(visits: int, requests: int) -> float:
        if visits <= 0:
            return 0.0
        return round((requests / visits) * 100, 1)

    day_visits = int(visit_row["day_visits"] or 0)
    month_visits = int(visit_row["month_visits"] or 0)
    year_visits = int(visit_row["year_visits"] or 0)
    day_requests = int(request_row["day_requests"] or 0)
    month_requests = int(request_row["month_requests"] or 0)
    year_requests = int(request_row["year_requests"] or 0)

    return {
        "day_visits": day_visits,
        "month_visits": month_visits,
        "year_visits": year_visits,
        "day_requests": day_requests,
        "month_requests": month_requests,
        "year_requests": year_requests,
        "day_conversion": conversion(day_visits, day_requests),
        "month_conversion": conversion(month_visits, month_requests),
        "year_conversion": conversion(year_visits, year_requests),
        "latest_visit_at": visit_row["latest_visit_at"],
        "latest_request_at": request_row["latest_request_at"],
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


def count_requests_for_admin(
    database_path: Path,
    *,
    request_format: str | None = None,
    electronic_status: str | None = None,
    paper_status: str | None = None,
) -> int:
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

    query = "SELECT COUNT(*) AS count FROM requests"
    if filters:
        query += " WHERE " + " AND ".join(filters)

    with connect(database_path) as connection:
        row = connection.execute(query, values).fetchone()
    return int(row["count"] or 0)


def list_requests_for_admin_page(
    database_path: Path,
    *,
    request_format: str | None = None,
    electronic_status: str | None = None,
    paper_status: str | None = None,
    limit: int,
    offset: int,
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
    query += " ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?"
    values.extend([limit, offset])

    with connect(database_path) as connection:
        return connection.execute(query, values).fetchall()


def get_system_setting(database_path: Path, key: str) -> str | None:
    with connect(database_path) as connection:
        row = connection.execute(
            "SELECT setting_value FROM system_settings WHERE setting_key = ?",
            (key,),
        ).fetchone()
    if row is None:
        return None
    return str(row["setting_value"])


def set_system_setting(
    database_path: Path,
    *,
    key: str,
    value: str,
    updated_at: str,
) -> None:
    with connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO system_settings (setting_key, setting_value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET
                setting_value = excluded.setting_value,
                updated_at = excluded.updated_at
            """,
            (key, value, updated_at),
        )
        connection.commit()


def create_inbound_email(
    database_path: Path,
    *,
    provider_key: str,
    mailbox_name: str,
    message_uid: str,
    message_id: str | None,
    from_email: str | None,
    from_name: str | None,
    subject: str,
    body_text: str,
    received_at: str | None,
    imported_at: str,
) -> bool:
    with connect(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO inbound_emails (
                provider_key,
                mailbox_name,
                message_uid,
                message_id,
                from_email,
                from_name,
                subject,
                body_text,
                received_at,
                imported_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                provider_key,
                mailbox_name,
                message_uid,
                message_id,
                from_email,
                from_name,
                subject,
                body_text,
                received_at,
                imported_at,
            ),
        )
        connection.commit()
        return int(cursor.rowcount or 0) > 0


def count_inbound_emails(database_path: Path) -> int:
    with connect(database_path) as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM inbound_emails").fetchone()
    return int(row["count"] or 0)


def list_inbound_emails_page(
    database_path: Path,
    *,
    limit: int,
    offset: int,
) -> list[sqlite3.Row]:
    with connect(database_path) as connection:
        return connection.execute(
            """
            SELECT *
            FROM inbound_emails
            ORDER BY imported_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()


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
