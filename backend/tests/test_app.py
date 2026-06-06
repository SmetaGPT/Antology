from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.download_service import issue_download_token
from app.main import create_app
from app.repository import (
    create_book_version,
    get_email_job,
    get_download_token_state,
    get_request,
    list_admin_events,
    list_email_jobs,
)
from app.worker_service import process_due_email_jobs


def make_settings(database_path: Path) -> Settings:
    book_storage_dir = database_path.parent / "books"
    return Settings(
        app_name="Antology API Test",
        app_env="test",
        api_prefix="/api",
        cors_origins=["http://localhost:5173"],
        public_base_url="https://antology.test",
        database_path=database_path,
        book_storage_dir=book_storage_dir,
        download_token_ttl_hours=72,
        delivery_delay_minutes=30,
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

    request_row = get_request(database_path, payload["request_id"])
    assert request_row is not None
    assert request_row["electronic_status"] == "pending"
    assert request_row["paper_status"] == "none"
    assert request_row["delivery_token_candidate"] is not None
    assert request_row["updated_at"] == request_row["created_at"]

    email_jobs = list_email_jobs(database_path, payload["request_id"])
    assert len(email_jobs) == 1
    assert email_jobs[0]["kind"] == "electronic_link"
    assert email_jobs[0]["status"] == "pending"


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

    request_row = get_request(database_path, payload["request_id"])
    assert request_row is not None
    assert request_row["delivery_token_candidate"] is None
    assert list_email_jobs(database_path, payload["request_id"]) == []


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

    request_row = get_request(database_path, payload["request_id"])
    assert request_row is not None
    assert request_row["delivery_token_candidate"] is not None

    email_jobs = list_email_jobs(database_path, payload["request_id"])
    assert len(email_jobs) == 1
    assert email_jobs[0]["recipient_email"] == "elena@example.com"


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

    from app.db import connect

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

    from app.db import connect

    with connect(database_path) as connection:
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

    email_job_id = response.json()["email_job_id"]
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
    settings = Settings(
        app_name=settings.app_name,
        app_env=settings.app_env,
        api_prefix=settings.api_prefix,
        cors_origins=settings.cors_origins,
        public_base_url=settings.public_base_url,
        database_path=settings.database_path,
        book_storage_dir=settings.book_storage_dir,
        download_token_ttl_hours=settings.download_token_ttl_hours,
        delivery_delay_minutes=settings.delivery_delay_minutes,
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

    from app.db import connect

    with connect(database_path) as connection:
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
        "/admin/login",
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
    assert response.headers["location"] == "/admin/login"


def test_admin_can_log_in_and_log_out(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)

    with client:
        login_admin(client)

        dashboard_response = client.get("/admin")
        assert dashboard_response.status_code == 200
        assert "Antology Admin Dashboard" in dashboard_response.text

        logout_response = client.post("/admin/logout", follow_redirects=False)
        assert logout_response.status_code == 303
        assert logout_response.headers["location"] == "/admin/login"


def test_admin_dashboard_shows_counts_and_filterable_requests(tmp_path: Path) -> None:
    client, database_path = make_client(tmp_path)

    with client:
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
        third = client.post(
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

        from app.db import connect

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
        assert "Total requests</strong><br>5" in dashboard_response.text
        assert "Electronic sent</strong><br>1" in dashboard_response.text
        assert "Electronic failed</strong><br>1" in dashboard_response.text
        assert "Paper review</strong><br>1" in dashboard_response.text
        assert "Paper approved</strong><br>1" in dashboard_response.text
        assert "Paper rejected</strong><br>1" in dashboard_response.text

        filtered_response = client.get("/admin?paper_status=review")
        assert filtered_response.status_code == 200
        assert "Review User" in filtered_response.text
        assert "Approved User" not in filtered_response.text
        assert "Rejected User" not in filtered_response.text


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
    assert len(email_jobs) == 1
    assert email_jobs[0]["kind"] == "paper_pickup"
    assert email_jobs[0]["status"] == "pending"
    assert "Pickup point: Tverskaya 1" in email_jobs[0]["body"]

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
    assert len(email_jobs) == 2
    assert email_jobs[0]["kind"] == "electronic_link"
    assert email_jobs[1]["kind"] == "paper_rejected"
    assert "temporarily unavailable" in email_jobs[1]["body"]

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
    assert list_email_jobs(database_path, request_id)[0]["kind"] == "electronic_link"
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

    from app.db import connect

    paper_jobs = list_email_jobs(database_path, request_id)
    paper_job_id = paper_jobs[0]["id"]

    with connect(database_path) as connection:
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
