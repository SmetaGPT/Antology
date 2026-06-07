from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any, cast

from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

SettingsModel = cast(Any, importlib.import_module("app.config").Settings)
issue_download_token = cast(Any, importlib.import_module("app.download_service").issue_download_token)
create_app = cast(Any, importlib.import_module("app.main").create_app)
repository = importlib.import_module("app.repository")
create_book_version = cast(Any, repository.create_book_version)
get_email_job = cast(Any, repository.get_email_job)
get_active_book_version = cast(Any, repository.get_active_book_version)
get_download_token_state = cast(Any, repository.get_download_token_state)
get_request = cast(Any, repository.get_request)
list_admin_events = cast(Any, repository.list_admin_events)
list_book_versions = cast(Any, repository.list_book_versions)
list_email_jobs = cast(Any, repository.list_email_jobs)
set_system_setting = cast(Any, repository.set_system_setting)
process_due_email_jobs = cast(Any, importlib.import_module("app.worker_service").process_due_email_jobs)
sync_incoming_emails = cast(Any, importlib.import_module("app.worker_service").sync_incoming_emails)
ReceivedEmail = cast(Any, importlib.import_module("app.email_service").ReceivedEmail)
connect = cast(Any, importlib.import_module("app.db").connect)


def make_settings(database_path: Path) -> Any:
    book_storage_dir = database_path.parent / "books"
    return SettingsModel(
        app_name="Antology API Test",
        app_env="test",
        api_prefix="/api",
        cors_origins=["http://localhost:5173"],
        public_base_url="https://antology.test",
        database_path=database_path,
        book_storage_dir=book_storage_dir,
        expose_api_docs=True,
        download_token_ttl_hours=72,
        max_book_upload_mb=250,
        delivery_delay_minutes=30,
        rate_limit_window_minutes=60,
        rate_limit_max_per_ip=10,
        rate_limit_max_per_email=3,
        smtp_host="localhost",
        smtp_port=1025,
        smtp_username="",
        smtp_password="",
        smtp_from_email="noreply@antology.test",
        smtp_use_tls=False,
        email_max_retries=3,
        worker_poll_interval_seconds=1,
        admin_email="admin@antology.test",
        admin_password="test-password",
        secret_key="test-secret-key",
    )


def make_client(tmp_path: Path) -> tuple[TestClient, Path]:
    database_path = tmp_path / "test.db"
    app = create_app(make_settings(database_path))
    return TestClient(app), database_path


def seed_active_book(database_path: Path) -> int:
    settings = make_settings(database_path)
    settings.book_storage_dir.mkdir(parents=True, exist_ok=True)
    book_path = settings.book_storage_dir / "anthology-v1.pdf"
    book_path.write_bytes(b"%PDF-1.4\nfake-pdf-content\n")

    return create_book_version(
        database_path,
        title="Anthology",
        version_label="v1",
        file_path="anthology-v1.pdf",
        file_name="anthology-v1.pdf",
        file_size=book_path.stat().st_size,
        checksum="test-checksum",
        is_active=True,
        uploaded_at="2026-06-06T00:00:00+00:00",
    )


def test_healthcheck(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_production_app_disables_public_api_docs_by_default(tmp_path: Path) -> None:
    database_path = tmp_path / "prod.db"
    base_settings = make_settings(database_path)
    production_settings = SettingsModel(
        app_name=base_settings.app_name,
        app_env="production",
        api_prefix=base_settings.api_prefix,
        cors_origins=base_settings.cors_origins,
        public_base_url=base_settings.public_base_url,
        database_path=base_settings.database_path,
        book_storage_dir=base_settings.book_storage_dir,
        expose_api_docs=False,
        download_token_ttl_hours=base_settings.download_token_ttl_hours,
        max_book_upload_mb=base_settings.max_book_upload_mb,
        delivery_delay_minutes=base_settings.delivery_delay_minutes,
        rate_limit_window_minutes=base_settings.rate_limit_window_minutes,
        rate_limit_max_per_ip=base_settings.rate_limit_max_per_ip,
        rate_limit_max_per_email=base_settings.rate_limit_max_per_email,
        smtp_host=base_settings.smtp_host,
        smtp_port=base_settings.smtp_port,
        smtp_username=base_settings.smtp_username,
        smtp_password=base_settings.smtp_password,
        smtp_from_email=base_settings.smtp_from_email,
        smtp_use_tls=base_settings.smtp_use_tls,
        email_max_retries=base_settings.email_max_retries,
        worker_poll_interval_seconds=base_settings.worker_poll_interval_seconds,
        admin_email=base_settings.admin_email,
        admin_password=base_settings.admin_password,
        secret_key=base_settings.secret_key,
    )
    client = TestClient(create_app(production_settings))

    with client:
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404


def test_request_access_rejects_missing_consent(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    response = client.post(
        "/api/request-access",
        json={
            "first_name": "Ivan",
            "last_name": "Ivanov",
            "email": "ivan@example.com",
            "purpose": "Need anthology access for a research project and public lecture.",
            "format": "electronic",
            "consent": False,
        },
    )

    assert response.status_code == 422


def test_request_access_creates_electronic_request_and_email_job(tmp_path: Path) -> None:
    client, database_path = make_client(tmp_path)

    with client:
        response = client.post(
            "/api/request-access",
            json={
                "first_name": "Ivan",
                "last_name": "Ivanov",
                "organization": "Museum",
                "position": "Researcher",
                "email": "ivan@example.com",
                "phone": "+79990000000",
                "purpose": "Need anthology access for a research project and public lecture.",
                "format": "electronic",
                "consent": True,
            },
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "accepted"
    assert payload["electronic_status"] == "pending"
    assert payload["paper_status"] == "none"
    assert payload["email_job_id"] is not None
    assert payload["delivery_scheduled_for"] is not None
    assert "Письмо с подтверждением" in payload["confirmation_message"]
    assert payload["electronic_delivery_delay_minutes"] == 30

    request_row = get_request(database_path, payload["request_id"])
    assert request_row is not None
    assert request_row["electronic_status"] == "pending"
    assert request_row["paper_status"] == "none"
    assert request_row["delivery_token_candidate"] is not None
    assert request_row["updated_at"] == request_row["created_at"]
    assert request_row["consent_at"] == request_row["created_at"]
    assert request_row["request_ip"]
    assert request_row["user_agent"]

    email_jobs = list_email_jobs(database_path, payload["request_id"])
    assert len(email_jobs) == 2
    assert email_jobs[0]["kind"] == "request_confirmation"
    assert email_jobs[0]["status"] == "pending"
    assert email_jobs[1]["kind"] == "electronic_link"
    assert email_jobs[1]["status"] == "pending"


def test_request_access_creates_paper_review_without_email_job(tmp_path: Path) -> None:
    client, database_path = make_client(tmp_path)

    with client:
        response = client.post(
            "/api/request-access",
            json={
                "first_name": "Anna",
                "last_name": "Petrova",
                "organization": "Library",
                "position": "Curator",
                "email": "anna@example.com",
                "phone": "+79990000001",
                "purpose": "Need the printed anthology for a local reading room exhibition.",
                "format": "paper",
                "consent": True,
            },
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["electronic_status"] == "none"
    assert payload["paper_status"] == "review"
    assert payload["email_job_id"] is None
    assert payload["delivery_scheduled_for"] is None
    assert "5 рабочих дней" in payload["confirmation_message"]
    assert payload["electronic_delivery_delay_minutes"] is None

    request_row = get_request(database_path, payload["request_id"])
    assert request_row is not None
    assert request_row["delivery_token_candidate"] is None
    email_jobs = list_email_jobs(database_path, payload["request_id"])
    assert len(email_jobs) == 1
    assert email_jobs[0]["kind"] == "request_confirmation"


def test_request_access_creates_both_paths(tmp_path: Path) -> None:
    client, database_path = make_client(tmp_path)

    with client:
        response = client.post(
            "/api/request-access",
            json={
                "first_name": "Elena",
                "last_name": "Sidorova",
                "organization": "University",
                "position": "Lecturer",
                "email": "elena@example.com",
                "phone": "+79990000002",
                "purpose": "Need digital access now and a printed set for a university archive.",
                "format": "both",
                "consent": True,
            },
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["electronic_status"] == "pending"
    assert payload["paper_status"] == "review"
    assert payload["email_job_id"] is not None
    assert "5 рабочих дней" in payload["confirmation_message"]
    assert payload["electronic_delivery_delay_minutes"] == 30

    request_row = get_request(database_path, payload["request_id"])
    assert request_row is not None
    assert request_row["delivery_token_candidate"] is not None

    email_jobs = list_email_jobs(database_path, payload["request_id"])
    assert len(email_jobs) == 2
    assert email_jobs[0]["kind"] == "request_confirmation"
    assert email_jobs[0]["recipient_email"] == "elena@example.com"
    assert email_jobs[1]["kind"] == "electronic_link"


def test_request_access_silently_drops_honeypot_submission(tmp_path: Path) -> None:
    client, database_path = make_client(tmp_path)

    with client:
        response = client.post(
            "/api/request-access",
            json={
                "first_name": "Spam",
                "last_name": "Bot",
                "email": "spam@example.com",
                "purpose": "Need anthology access for an apparently normal request.",
                "honeypot": "https://spam.invalid",
                "format": "electronic",
                "consent": True,
            },
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["request_id"] == 0
    assert payload["electronic_status"] == "none"
    assert payload["paper_status"] == "none"
    assert get_request(database_path, 1) is None


def test_request_access_rate_limits_repeated_email_requests(tmp_path: Path) -> None:
    client, database_path = make_client(tmp_path)
    settings = make_settings(database_path)
    limited_settings = SettingsModel(
        app_name=settings.app_name,
        app_env=settings.app_env,
        api_prefix=settings.api_prefix,
        cors_origins=settings.cors_origins,
        public_base_url=settings.public_base_url,
        database_path=settings.database_path,
        book_storage_dir=settings.book_storage_dir,
        expose_api_docs=settings.expose_api_docs,
        download_token_ttl_hours=settings.download_token_ttl_hours,
        max_book_upload_mb=settings.max_book_upload_mb,
        delivery_delay_minutes=settings.delivery_delay_minutes,
        rate_limit_window_minutes=settings.rate_limit_window_minutes,
        rate_limit_max_per_ip=settings.rate_limit_max_per_ip,
        rate_limit_max_per_email=1,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_username,
        smtp_password=settings.smtp_password,
        smtp_from_email=settings.smtp_from_email,
        smtp_use_tls=settings.smtp_use_tls,
        email_max_retries=settings.email_max_retries,
        worker_poll_interval_seconds=settings.worker_poll_interval_seconds,
        admin_email=settings.admin_email,
        admin_password=settings.admin_password,
        secret_key=settings.secret_key,
    )
    limited_client = TestClient(create_app(limited_settings))

    with limited_client:
        first = limited_client.post(
            "/api/request-access",
            json={
                "first_name": "Alexey",
                "last_name": "Morin",
                "email": "alexey@example.com",
                "purpose": "Need the anthology for a lecture and reference work.",
                "format": "electronic",
                "consent": True,
            },
        )
        second = limited_client.post(
            "/api/request-access",
            json={
                "first_name": "Alexey",
                "last_name": "Morin",
                "email": "alexey@example.com",
                "purpose": "Need the anthology for a lecture and reference work.",
                "format": "electronic",
                "consent": True,
            },
        )

    assert first.status_code == 201
    assert second.status_code == 429
    assert second.json()["detail"] == "Too many requests. Please try again later."


def test_site_visit_endpoint_tracks_single_session_once(tmp_path: Path) -> None:
    client, database_path = make_client(tmp_path)

    with client:
        first = client.post(
            "/api/site-visit",
            json={
                "session_id": "session-001",
                "path": "/",
                "referrer": "https://example.test",
            },
        )
        second = client.post(
            "/api/site-visit",
            json={
                "session_id": "session-001",
                "path": "/",
                "referrer": "https://example.test",
            },
        )

    assert first.status_code == 202
    assert second.status_code == 202

    with connect(database_path) as connection:
        visits = connection.execute(
            "SELECT session_id, path, referrer, request_ip, user_agent FROM site_visits"
        ).fetchall()

    assert len(visits) == 1
    assert visits[0]["session_id"] == "session-001"
    assert visits[0]["path"] == "/"
    assert visits[0]["referrer"] == "https://example.test"
    assert visits[0]["request_ip"]
    assert visits[0]["user_agent"]


def test_download_book_returns_active_book_for_valid_token(tmp_path: Path) -> None:
    client, database_path = make_client(tmp_path)
    settings = make_settings(database_path)

    with client:
        seed_active_book(database_path)
        response = client.post(
            "/api/request-access",
            json={
                "first_name": "Pavel",
                "last_name": "Smirnov",
                "email": "pavel@example.com",
                "purpose": "Need the book for an architecture seminar and archive notes.",
                "format": "electronic",
                "consent": True,
            },
        )

    request_id = response.json()["request_id"]
    token_result = issue_download_token(
        database_path,
        settings,
        request_id=request_id,
    )

    download_response = client.get(f"/download/{token_result.token}")
    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "application/pdf"

    token_state = get_download_token_state(database_path, token_result.token_id)
    assert token_state is not None
    assert token_state["used_count"] == 1
    assert token_state["last_used_at"] is not None


def test_download_book_rejects_invalid_token(tmp_path: Path) -> None:
    client, database_path = make_client(tmp_path)

    with client:
        seed_active_book(database_path)

    response = client.get("/download/not-a-real-token")
    assert response.status_code == 404


def test_download_book_rejects_expired_token(tmp_path: Path) -> None:
    client, database_path = make_client(tmp_path)
    settings = make_settings(database_path)

    with client:
        seed_active_book(database_path)
        response = client.post(
            "/api/request-access",
            json={
                "first_name": "Maria",
                "last_name": "Kuznetsova",
                "email": "maria@example.com",
                "purpose": "Need digital access for a regional museum education program.",
                "format": "electronic",
                "consent": True,
            },
        )

    request_id = response.json()["request_id"]
    token_result = issue_download_token(
        database_path,
        settings,
        request_id=request_id,
    )


    with connect(database_path) as connection:
        connection.execute(
            "UPDATE download_tokens SET expires_at = ? WHERE id = ?",
            ("2000-01-01T00:00:00+00:00", token_result.token_id),
        )
        connection.commit()

    expired_response = client.get(f"/download/{token_result.token}")
    assert expired_response.status_code == 410


class FakeEmailSender:
    def __init__(self) -> None:
        self.sent_payloads: list[object] = []

    def send(self, payload: object) -> None:
        self.sent_payloads.append(payload)


class FailingEmailSender:
    def send(self, payload: object) -> None:
        raise RuntimeError("SMTP outage")


def test_worker_sends_due_electronic_jobs(tmp_path: Path) -> None:
    client, database_path = make_client(tmp_path)
    settings = make_settings(database_path)
    sender = FakeEmailSender()

    with client:
        seed_active_book(database_path)
        response = client.post(
            "/api/request-access",
            json={
                "first_name": "Nikolai",
                "last_name": "Fedorov",
                "email": "nikolai@example.com",
                "purpose": "Need the anthology for a municipal archive lecture series.",
                "format": "electronic",
                "consent": True,
            },
        )

    request_id = response.json()["request_id"]
    email_job_id = response.json()["email_job_id"]


    with connect(database_path) as connection:
        connection.execute(
            "UPDATE email_jobs SET send_after = ? WHERE request_id = ? AND kind = 'request_confirmation'",
            ("2999-01-01T00:00:00+00:00", request_id),
        )
        connection.execute(
            "UPDATE email_jobs SET send_after = ? WHERE id = ?",
            ("2000-01-01T00:00:00+00:00", email_job_id),
        )
        connection.commit()

    result = process_due_email_jobs(
        database_path,
        settings,
        email_sender=sender,
    )

    assert result.processed_count == 1
    assert result.sent_count == 1
    assert result.failed_count == 0
    assert len(sender.sent_payloads) == 1

    payload = sender.sent_payloads[0]
    assert hasattr(payload, "body")
    assert "/download/" in payload.body
    assert "https://antology.test/download/" in payload.body

    request_row = get_request(database_path, request_id)
    assert request_row is not None
    assert request_row["electronic_status"] == "sent"

    email_job = get_email_job(database_path, email_job_id)
    assert email_job is not None
    assert email_job["status"] == "sent"
    assert email_job["sent_at"] is not None
    assert email_job["last_error"] is None


def test_worker_ignores_future_jobs_until_due(tmp_path: Path) -> None:
    client, database_path = make_client(tmp_path)
    settings = make_settings(database_path)
    sender = FakeEmailSender()

    with client:
        seed_active_book(database_path)
        response = client.post(
            "/api/request-access",
            json={
                "first_name": "Olga",
                "last_name": "Morozova",
                "email": "olga@example.com",
                "purpose": "Need the anthology for a university urban studies elective.",
                "format": "electronic",
                "consent": True,
            },
        )

    request_id = response.json()["request_id"]
    email_job_id = response.json()["email_job_id"]
    with connect(database_path) as connection:
        connection.execute(
            "UPDATE email_jobs SET send_after = ? WHERE request_id = ? AND kind = 'request_confirmation'",
            ("2999-01-01T00:00:00+00:00", request_id),
        )
        connection.commit()
    result = process_due_email_jobs(
        database_path,
        settings,
        email_sender=sender,
    )

    assert result.processed_count == 0
    assert result.sent_count == 0
    assert result.failed_count == 0
    assert sender.sent_payloads == []

    email_job = get_email_job(database_path, email_job_id)
    assert email_job is not None
    assert email_job["status"] == "pending"
    assert email_job["attempt_count"] == 0


def test_worker_keeps_failure_metadata_for_failed_jobs(tmp_path: Path) -> None:
    client, database_path = make_client(tmp_path)
    settings = make_settings(database_path)
    settings = SettingsModel(
        app_name=settings.app_name,
        app_env=settings.app_env,
        api_prefix=settings.api_prefix,
        cors_origins=settings.cors_origins,
        public_base_url=settings.public_base_url,
        database_path=settings.database_path,
        book_storage_dir=settings.book_storage_dir,
        expose_api_docs=settings.expose_api_docs,
        download_token_ttl_hours=settings.download_token_ttl_hours,
        max_book_upload_mb=settings.max_book_upload_mb,
        delivery_delay_minutes=settings.delivery_delay_minutes,
        rate_limit_window_minutes=settings.rate_limit_window_minutes,
        rate_limit_max_per_ip=settings.rate_limit_max_per_ip,
        rate_limit_max_per_email=settings.rate_limit_max_per_email,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_username,
        smtp_password=settings.smtp_password,
        smtp_from_email=settings.smtp_from_email,
        smtp_use_tls=settings.smtp_use_tls,
        email_max_retries=1,
        worker_poll_interval_seconds=settings.worker_poll_interval_seconds,
        admin_email=settings.admin_email,
        admin_password=settings.admin_password,
        secret_key=settings.secret_key,
    )

    with client:
        seed_active_book(database_path)
        response = client.post(
            "/api/request-access",
            json={
                "first_name": "Irina",
                "last_name": "Lebedeva",
                "email": "irina@example.com",
                "purpose": "Need the book for an independent preservation workshop.",
                "format": "electronic",
                "consent": True,
            },
        )

    request_id = response.json()["request_id"]
    email_job_id = response.json()["email_job_id"]

    with connect(database_path) as connection:
        connection.execute(
            "UPDATE email_jobs SET send_after = ? WHERE request_id = ? AND kind = 'request_confirmation'",
            ("2999-01-01T00:00:00+00:00", request_id),
        )
        connection.execute(
            "UPDATE email_jobs SET send_after = ? WHERE id = ?",
            ("2000-01-01T00:00:00+00:00", email_job_id),
        )
        connection.commit()

    result = process_due_email_jobs(
        database_path,
        settings,
        email_sender=FailingEmailSender(),
    )

    assert result.processed_count == 1
    assert result.sent_count == 0
    assert result.failed_count == 1

    email_job = get_email_job(database_path, email_job_id)
    assert email_job is not None
    assert email_job["status"] == "failed"
    assert email_job["attempt_count"] == 1
    assert email_job["last_error"] == "SMTP outage"

    request_row = get_request(database_path, request_id)
    assert request_row is not None
    assert request_row["electronic_status"] == "failed"


def login_admin(client: TestClient) -> None:
    response = client.post(
        "/ad/log",
        data={
            "email": "admin@antology.test",
            "password": "test-password",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/admin"


def test_admin_routes_require_authentication(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)

    with client:
        response = client.get("/admin", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/ad/log"


def test_admin_can_log_in_and_log_out(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)

    with client:
        login_admin(client)

        dashboard_response = client.get("/admin")
        assert dashboard_response.status_code == 200
        assert "Панель администратора" in dashboard_response.text
        assert "Anthology" in dashboard_response.text
        assert "Admin" in dashboard_response.text

        logout_response = client.post("/admin/logout", follow_redirects=False)
        assert logout_response.status_code == 303
        assert logout_response.headers["location"] == "/ad/log"


def test_admin_login_is_case_insensitive_for_seeded_email(tmp_path: Path) -> None:
    database_path = tmp_path / "test.db"
    settings = make_settings(database_path)
    mixed_case_settings = SettingsModel(
        app_name=settings.app_name,
        app_env=settings.app_env,
        api_prefix=settings.api_prefix,
        cors_origins=settings.cors_origins,
        public_base_url=settings.public_base_url,
        database_path=settings.database_path,
        book_storage_dir=settings.book_storage_dir,
        expose_api_docs=settings.expose_api_docs,
        download_token_ttl_hours=settings.download_token_ttl_hours,
        max_book_upload_mb=settings.max_book_upload_mb,
        delivery_delay_minutes=settings.delivery_delay_minutes,
        rate_limit_window_minutes=settings.rate_limit_window_minutes,
        rate_limit_max_per_ip=settings.rate_limit_max_per_ip,
        rate_limit_max_per_email=settings.rate_limit_max_per_email,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_username,
        smtp_password=settings.smtp_password,
        smtp_from_email=settings.smtp_from_email,
        smtp_use_tls=settings.smtp_use_tls,
        email_max_retries=settings.email_max_retries,
        worker_poll_interval_seconds=settings.worker_poll_interval_seconds,
        admin_email="Nikita_G@yandex.ru",
        admin_password="amin123$",
        secret_key=settings.secret_key,
    )
    client = TestClient(create_app(mixed_case_settings))

    with client:
        response = client.post(
            "/ad/log",
            data={
                "email": "nikita_g@yandex.ru",
                "password": "amin123$",
            },
            follow_redirects=False,
        )

    assert response.status_code == 303
    assert response.headers["location"] == "/admin"


def test_legacy_admin_login_route_redirects_to_new_path(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)

    with client:
        response = client.get("/admin/login", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/ad/log"


def test_admin_dashboard_shows_counts_and_filterable_requests(tmp_path: Path) -> None:
    client, database_path = make_client(tmp_path)

    with client:
        client.post(
            "/api/site-visit",
            json={
                "session_id": "visit-0001",
                "path": "/",
                "referrer": None,
            },
        )
        client.post(
            "/api/site-visit",
            json={
                "session_id": "visit-0002",
                "path": "/",
                "referrer": None,
            },
        )
        first = client.post(
            "/api/request-access",
            json={
                "first_name": "Sent",
                "last_name": "User",
                "email": "sent@example.com",
                "purpose": "Need a sent electronic record.",
                "format": "electronic",
                "consent": True,
            },
        ).json()
        second = client.post(
            "/api/request-access",
            json={
                "first_name": "Failed",
                "last_name": "User",
                "email": "failed@example.com",
                "purpose": "Need a failed electronic record.",
                "format": "electronic",
                "consent": True,
            },
        ).json()
        client.post(
            "/api/request-access",
            json={
                "first_name": "Review",
                "last_name": "User",
                "email": "review@example.com",
                "purpose": "Need paper review record.",
                "format": "paper",
                "consent": True,
            },
        ).json()
        fourth = client.post(
            "/api/request-access",
            json={
                "first_name": "Approved",
                "last_name": "User",
                "email": "approved@example.com",
                "purpose": "Need approved paper record.",
                "format": "paper",
                "consent": True,
            },
        ).json()
        fifth = client.post(
            "/api/request-access",
            json={
                "first_name": "Rejected",
                "last_name": "User",
                "email": "rejected@example.com",
                "purpose": "Need rejected paper record.",
                "format": "paper",
                "consent": True,
            },
        ).json()

        with connect(database_path) as connection:
            connection.execute(
                "UPDATE requests SET electronic_status = 'sent' WHERE id = ?",
                (first["request_id"],),
            )
            connection.execute(
                "UPDATE requests SET electronic_status = 'failed' WHERE id = ?",
                (second["request_id"],),
            )
            connection.execute(
                "UPDATE requests SET paper_status = 'approved' WHERE id = ?",
                (fourth["request_id"],),
            )
            connection.execute(
                "UPDATE requests SET paper_status = 'rejected' WHERE id = ?",
                (fifth["request_id"],),
            )
            connection.commit()

        login_admin(client)

        dashboard_response = client.get("/admin")
        assert dashboard_response.status_code == 200
        assert "Всего заявок" in dashboard_response.text
        assert ">5<" in dashboard_response.text
        assert "Отправлено (эл.)" in dashboard_response.text
        assert "Ошибки (эл.)" in dashboard_response.text
        assert "На проверке" in dashboard_response.text
        assert "Одобрено" in dashboard_response.text
        assert "Отклонено" in dashboard_response.text
        assert "Посещения" in dashboard_response.text
        assert "Конверсия" in dashboard_response.text
        assert "За день" in dashboard_response.text
        assert "Последние заявки" in dashboard_response.text
        assert "Открыть все заявки" in dashboard_response.text

        filtered_response = client.get("/admin/requests?paper_status=review")
        assert filtered_response.status_code == 200
        assert "Review User" in filtered_response.text
        assert "Approved User" not in filtered_response.text
        assert "Rejected User" not in filtered_response.text
        assert "Фильтрация и обработка поступивших заявок" in filtered_response.text


def test_admin_can_open_books_requests_and_settings_pages(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)

    with client:
        login_admin(client)

        books_response = client.get("/admin/books")
        requests_response = client.get("/admin/requests")
        settings_response = client.get("/admin/settings")

    assert books_response.status_code == 200
    assert "Версии книги" in books_response.text
    assert requests_response.status_code == 200
    assert "Фильтрация и обработка поступивших заявок" in requests_response.text
    assert settings_response.status_code == 200
    assert "Настройки отправки" in settings_response.text


def test_admin_can_update_delivery_delay_setting(tmp_path: Path) -> None:
    client, database_path = make_client(tmp_path)

    with client:
        login_admin(client)
        response = client.post(
            "/admin/settings/delivery-delay",
            data={"delivery_delay_minutes": "90"},
        )
        request_response = client.post(
            "/api/request-access",
            json={
                "first_name": "Delay",
                "last_name": "User",
                "email": "delay@example.com",
                "purpose": "Need digital access for delayed link verification.",
                "format": "electronic",
                "consent": True,
            },
        )

    assert response.status_code == 200
    assert "Новая задержка отправки ссылки сохранена." in response.text

    with connect(database_path) as connection:
        setting_row = connection.execute(
            "SELECT setting_value FROM system_settings WHERE setting_key = ?",
            ("electronic_delivery_delay_minutes",),
        ).fetchone()

    assert setting_row is not None
    assert setting_row["setting_value"] == "90"
    assert request_response.status_code == 201
    assert request_response.json()["electronic_delivery_delay_minutes"] == 90
    assert "через 90 мин." in request_response.json()["confirmation_message"]


def test_admin_can_update_mail_provider_settings(tmp_path: Path) -> None:
    client, database_path = make_client(tmp_path)

    with client:
        login_admin(client)
        response = client.post(
            "/admin/settings/mail",
            data={
                "provider_key": "yandex",
                "smtp_from_email": "robot@example.com",
                "smtp_username": "robot@example.com",
                "smtp_password": "smtp-secret",
                "imap_username": "robot@example.com",
                "imap_password": "imap-secret",
                "outbound_mail_enabled": "on",
                "inbound_mail_enabled": "on",
            },
        )

    assert response.status_code == 200
    assert "Почтовые настройки сохранены." in response.text
    assert "Yandex" in response.text

    with connect(database_path) as connection:
        rows = {
            row["setting_key"]: row["setting_value"]
            for row in connection.execute(
                "SELECT setting_key, setting_value FROM system_settings"
            ).fetchall()
        }

    assert rows["mail_provider_key"] == "yandex"
    assert rows["smtp_host"] == "smtp.yandex.com"
    assert rows["smtp_port"] == "465"
    assert rows["smtp_security"] == "ssl"
    assert rows["imap_host"] == "imap.yandex.com"
    assert rows["imap_port"] == "993"
    assert rows["outbound_mail_enabled"] == "1"
    assert rows["inbound_mail_enabled"] == "1"


class FakeMailReceiver:
    def __init__(self, messages: list[object]) -> None:
        self._messages = messages

    def fetch_unseen(self, *, limit: int = 20) -> list[object]:
        return self._messages[:limit]


def test_sync_incoming_emails_imports_messages(tmp_path: Path) -> None:
    client, database_path = make_client(tmp_path)
    settings = make_settings(database_path)
    with client:
        pass
    now = "2026-06-07T12:00:00+00:00"
    set_system_setting(
        database_path,
        key="inbound_mail_enabled",
        value="1",
        updated_at=now,
    )
    set_system_setting(
        database_path,
        key="mail_provider_key",
        value="custom",
        updated_at=now,
    )

    receiver = FakeMailReceiver(
        [
            ReceivedEmail(
                mailbox_name="INBOX",
                message_uid="101",
                message_id="<msg-101@example.test>",
                from_email="reader@example.test",
                from_name="Reader",
                subject="Вопрос по Антологии",
                body_text="Подскажите, как получить бумажную версию?",
                received_at="Fri, 07 Jun 2026 12:00:00 +0000",
            )
        ]
    )

    result = sync_incoming_emails(
        database_path,
        settings,
        receiver=receiver,
    )

    assert result.processed_count == 1
    assert result.imported_count == 1
    assert result.duplicate_count == 0

    with connect(database_path) as connection:
        rows = connection.execute(
            "SELECT from_email, subject, mailbox_name FROM inbound_emails"
        ).fetchall()

    assert len(rows) == 1
    assert rows[0]["from_email"] == "reader@example.test"
    assert rows[0]["subject"] == "Вопрос по Антологии"
    assert rows[0]["mailbox_name"] == "INBOX"


def test_admin_request_detail_shows_contact_data(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)

    with client:
        response = client.post(
            "/api/request-access",
            json={
                "first_name": "Daria",
                "last_name": "Voronina",
                "organization": "City Archive",
                "position": "Curator",
                "email": "daria@example.com",
                "phone": "+79991112233",
                "purpose": "Need the anthology for a municipal history reading room.",
                "format": "both",
                "consent": True,
            },
        )

        login_admin(client)

        detail_response = client.get(f"/admin/requests/{response.json()['request_id']}")

    assert detail_response.status_code == 200
    assert "Daria" in detail_response.text
    assert "Voronina" in detail_response.text
    assert "City Archive" in detail_response.text
    assert "daria@example.com" in detail_response.text


def test_admin_can_approve_paper_request_and_create_pickup_email_job(tmp_path: Path) -> None:
    client, database_path = make_client(tmp_path)

    with client:
        response = client.post(
            "/api/request-access",
            json={
                "first_name": "Petr",
                "last_name": "Belov",
                "email": "petr@example.com",
                "purpose": "Need a printed copy for a district archive desk.",
                "format": "paper",
                "consent": True,
            },
        )
        request_id = response.json()["request_id"]

        login_admin(client)

        decision_response = client.post(
            f"/admin/requests/{request_id}/paper-decision",
            data={
                "decision": "approve",
                "pickup_info": "Pickup point: Tverskaya 1, weekdays 11:00-18:00.",
                "admin_note": "Bring an ID to confirm the reservation.",
            },
            follow_redirects=False,
        )

    assert decision_response.status_code == 303
    assert decision_response.headers["location"] == f"/admin/requests/{request_id}"

    request_row = get_request(database_path, request_id)
    assert request_row is not None
    assert request_row["paper_status"] == "approved"
    assert request_row["paper_pickup_info"] == "Pickup point: Tverskaya 1, weekdays 11:00-18:00."
    assert request_row["paper_admin_note"] == "Bring an ID to confirm the reservation."

    email_jobs = list_email_jobs(database_path, request_id)
    assert len(email_jobs) == 2
    assert email_jobs[0]["kind"] == "request_confirmation"
    assert email_jobs[1]["kind"] == "paper_pickup"
    assert email_jobs[1]["status"] == "pending"
    assert "Pickup point: Tverskaya 1" in email_jobs[1]["body"]

    admin_events = list_admin_events(
        database_path,
        entity_type="request",
        entity_id=request_id,
    )
    assert len(admin_events) == 1
    assert admin_events[0]["event_type"] == "paper_request_approved"
    assert '"email_job_id"' in admin_events[0]["metadata_json"]


def test_admin_can_reject_paper_request_and_create_rejection_email_job(tmp_path: Path) -> None:
    client, database_path = make_client(tmp_path)

    with client:
        response = client.post(
            "/api/request-access",
            json={
                "first_name": "Svetlana",
                "last_name": "Egorova",
                "email": "svetlana@example.com",
                "purpose": "Need a printed copy for a private collection request.",
                "format": "both",
                "consent": True,
            },
        )
        request_id = response.json()["request_id"]

        login_admin(client)

        decision_response = client.post(
            f"/admin/requests/{request_id}/paper-decision",
            data={
                "decision": "reject",
                "pickup_info": "",
                "admin_note": "Printed stock is temporarily unavailable.",
            },
            follow_redirects=False,
        )

    assert decision_response.status_code == 303

    request_row = get_request(database_path, request_id)
    assert request_row is not None
    assert request_row["paper_status"] == "rejected"
    assert request_row["paper_pickup_info"] is None
    assert request_row["paper_admin_note"] == "Printed stock is temporarily unavailable."

    email_jobs = list_email_jobs(database_path, request_id)
    assert len(email_jobs) == 3
    assert email_jobs[0]["kind"] == "request_confirmation"
    assert email_jobs[1]["kind"] == "electronic_link"
    assert email_jobs[2]["kind"] == "paper_rejected"
    assert "temporarily unavailable" in email_jobs[2]["body"]

    admin_events = list_admin_events(
        database_path,
        entity_type="request",
        entity_id=request_id,
    )
    assert len(admin_events) == 1
    assert admin_events[0]["event_type"] == "paper_request_rejected"


def test_admin_rejects_invalid_paper_transition(tmp_path: Path) -> None:
    client, database_path = make_client(tmp_path)

    with client:
        response = client.post(
            "/api/request-access",
            json={
                "first_name": "Roman",
                "last_name": "Kiselev",
                "email": "roman@example.com",
                "purpose": "Need only electronic access for a reading club.",
                "format": "electronic",
                "consent": True,
            },
        )
        request_id = response.json()["request_id"]

        login_admin(client)

        decision_response = client.post(
            f"/admin/requests/{request_id}/paper-decision",
            data={
                "decision": "approve",
                "pickup_info": "Front desk",
                "admin_note": "",
            },
        )

    assert decision_response.status_code == 400
    assert "Paper decision can be applied only to requests in review status" in decision_response.text

    request_row = get_request(database_path, request_id)
    assert request_row is not None
    assert request_row["paper_status"] == "none"
    email_jobs = list_email_jobs(database_path, request_id)
    assert email_jobs[0]["kind"] == "request_confirmation"
    assert email_jobs[1]["kind"] == "electronic_link"
    assert list_admin_events(
        database_path,
        entity_type="request",
        entity_id=request_id,
    ) == []


def test_worker_sends_due_paper_pickup_jobs(tmp_path: Path) -> None:
    client, database_path = make_client(tmp_path)
    settings = make_settings(database_path)
    sender = FakeEmailSender()

    with client:
        response = client.post(
            "/api/request-access",
            json={
                "first_name": "Maksim",
                "last_name": "Novikov",
                "email": "maksim@example.com",
                "purpose": "Need a printed copy for a cultural center.",
                "format": "paper",
                "consent": True,
            },
        )
        request_id = response.json()["request_id"]
        login_admin(client)
        client.post(
            f"/admin/requests/{request_id}/paper-decision",
            data={
                "decision": "approve",
                "pickup_info": "Pickup at reception after Tuesday.",
                "admin_note": "",
            },
        )

    paper_jobs = list_email_jobs(database_path, request_id)
    paper_job_id = next(int(job["id"]) for job in paper_jobs if job["kind"] == "paper_pickup")

    with connect(database_path) as connection:
        connection.execute(
            "UPDATE email_jobs SET send_after = ? WHERE request_id = ? AND kind = 'request_confirmation'",
            ("2999-01-01T00:00:00+00:00", request_id),
        )
        connection.execute(
            "UPDATE email_jobs SET send_after = ? WHERE id = ?",
            ("2000-01-01T00:00:00+00:00", paper_job_id),
        )
        connection.commit()

    result = process_due_email_jobs(
        database_path,
        settings,
        email_sender=sender,
    )

    assert result.processed_count == 1
    assert result.sent_count == 1
    assert result.failed_count == 0
    assert len(sender.sent_payloads) == 1
    payload = sender.sent_payloads[0]
    assert hasattr(payload, "body")
    assert "Pickup at reception after Tuesday." in payload.body

    email_job = get_email_job(database_path, paper_job_id)
    assert email_job is not None
    assert email_job["status"] == "sent"


def test_admin_can_upload_new_pdf_and_make_it_active(tmp_path: Path) -> None:
    client, database_path = make_client(tmp_path)
    settings = make_settings(database_path)

    with client:
        login_admin(client)
        response = client.post(
            "/admin/books/upload",
            data={
                "title": "Anthology",
                "version_label": "v2-2026",
                "make_active": "on",
            },
            files={
                "book_file": ("anthology-v2.pdf", b"%PDF-1.4\nversion-two\n", "application/pdf"),
            },
            follow_redirects=False,
        )

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/books"

    versions = list_book_versions(database_path)
    assert len(versions) == 1
    version = versions[0]
    assert version["title"] == "Anthology"
    assert version["version_label"] == "v2-2026"
    assert version["file_name"] == "anthology-v2.pdf"
    assert version["file_size"] > 0
    assert int(version["is_active"]) == 1

    stored_path = settings.book_storage_dir / str(version["file_path"])
    assert stored_path.exists()
    assert stored_path.read_bytes() == b"%PDF-1.4\nversion-two\n"

    events = list_admin_events(
        database_path,
        entity_type="book_version",
        entity_id=int(version["id"]),
    )
    assert len(events) == 1
    assert events[0]["event_type"] == "book_uploaded"


def test_admin_can_activate_existing_book_version(tmp_path: Path) -> None:
    client, database_path = make_client(tmp_path)
    settings = make_settings(database_path)

    with client:
        first_id = seed_active_book(database_path)
        settings.book_storage_dir.mkdir(parents=True, exist_ok=True)
        second_path = settings.book_storage_dir / "anthology-v2.pdf"
        second_path.write_bytes(b"%PDF-1.4\nnew-version\n")
        second_id = create_book_version(
            database_path,
            title="Anthology",
            version_label="v2",
            file_path="anthology-v2.pdf",
            file_name="anthology-v2.pdf",
            file_size=second_path.stat().st_size,
            checksum="checksum-v2",
            is_active=False,
            uploaded_at="2026-06-06T01:00:00+00:00",
        )
        login_admin(client)
        response = client.post(
            f"/admin/books/{second_id}/activate",
            follow_redirects=False,
        )

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/books"

    active_version = get_active_book_version(database_path)
    assert active_version is not None
    assert int(active_version["id"]) == second_id

    versions = {int(row["id"]): row for row in list_book_versions(database_path)}
    assert int(versions[first_id]["is_active"]) == 0
    assert int(versions[second_id]["is_active"]) == 1

    events = list_admin_events(
        database_path,
        entity_type="book_version",
        entity_id=second_id,
    )
    assert any(event["event_type"] == "book_activated" for event in events)


def test_new_electronic_request_uses_newly_uploaded_active_book(tmp_path: Path) -> None:
    client, database_path = make_client(tmp_path)
    settings = make_settings(database_path)

    with client:
        login_admin(client)
        upload_response = client.post(
            "/admin/books/upload",
            data={
                "title": "Anthology",
                "version_label": "v3-2026",
                "make_active": "on",
            },
            files={
                "book_file": ("anthology-v3.pdf", b"%PDF-1.4\nversion-three\n", "application/pdf"),
            },
            follow_redirects=False,
        )
        assert upload_response.status_code == 303

        request_response = client.post(
            "/api/request-access",
            json={
                "first_name": "Andrei",
                "last_name": "Mikhailov",
                "email": "andrei@example.com",
                "purpose": "Need the current electronic book for a local archive seminar.",
                "format": "electronic",
                "consent": True,
            },
        )

    request_id = request_response.json()["request_id"]
    token_result = issue_download_token(
        database_path,
        settings,
        request_id=request_id,
    )
    download_response = client.get(f"/download/{token_result.token}")

    assert download_response.status_code == 200
    assert download_response.content == b"%PDF-1.4\nversion-three\n"

    active_version = get_active_book_version(database_path)
    assert active_version is not None
    assert active_version["version_label"] == "v3-2026"
