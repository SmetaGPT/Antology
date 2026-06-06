from __future__ import annotations

from contextlib import asynccontextmanager
from html import escape
from urllib.parse import parse_qs

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from .admin_service import (
    SESSION_COOKIE_NAME,
    authenticate_admin,
    build_dashboard_context,
    create_admin_session,
    require_admin_user,
    seed_admin_user,
)
from .config import Settings, get_settings
from .db import init_database
from .download_service import resolve_download
from .paper_review_service import apply_paper_decision
from .repository import get_request, list_admin_events
from .request_access_service import create_request_access
from .schemas import RequestAccessPayload, RequestAccessResponse


def _render_login_page(error_message: str | None = None) -> str:
    error_html = ""
    if error_message:
        error_html = f"<p style='color:#b42318;'>{escape(error_message)}</p>"

    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Antology Admin Login</title></head><body>"
        "<main style='max-width:420px;margin:48px auto;font-family:Arial,sans-serif;'>"
        "<h1>Antology Admin</h1>"
        "<p>Sign in to review requests and monitor delivery.</p>"
        f"{error_html}"
        "<form method='post' action='/admin/login' style='display:grid;gap:12px;'>"
        "<label>Email<br><input type='email' name='email' required style='width:100%;padding:8px;'></label>"
        "<label>Password<br><input type='password' name='password' required style='width:100%;padding:8px;'></label>"
        "<button type='submit' style='padding:10px 14px;'>Sign in</button>"
        "</form></main></body></html>"
    )


def _render_dashboard_page(
    admin_email: str,
    context: dict[str, object],
) -> str:
    counts = context["counts"]
    filters = context["filters"]
    request_rows = context["requests"]

    rows_html = "".join(
        (
            "<tr>"
            f"<td><a href='/admin/requests/{row['id']}'>{row['id']}</a></td>"
            f"<td>{escape(str(row['first_name']))} {escape(str(row['last_name']))}</td>"
            f"<td>{escape(str(row['email']))}</td>"
            f"<td>{escape(str(row['format']))}</td>"
            f"<td>{escape(str(row['electronic_status']))}</td>"
            f"<td>{escape(str(row['paper_status']))}</td>"
            f"<td>{escape(str(row['created_at']))}</td>"
            "</tr>"
        )
        for row in request_rows
    )

    if not rows_html:
        rows_html = "<tr><td colspan='7'>No requests found for the current filters.</td></tr>"

    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Antology Admin</title></head><body>"
        "<main style='max-width:1100px;margin:32px auto;font-family:Arial,sans-serif;'>"
        "<div style='display:flex;justify-content:space-between;align-items:center;gap:16px;'>"
        "<div><h1>Antology Admin Dashboard</h1>"
        f"<p>Signed in as {escape(admin_email)}</p></div>"
        "<form method='post' action='/admin/logout'><button type='submit'>Log out</button></form>"
        "</div>"
        "<section style='display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:24px 0;'>"
        f"<div><strong>Total requests</strong><br>{counts['total_requests']}</div>"
        f"<div><strong>Electronic sent</strong><br>{counts['electronic_sent']}</div>"
        f"<div><strong>Electronic failed</strong><br>{counts['electronic_failed']}</div>"
        f"<div><strong>Paper review</strong><br>{counts['paper_review']}</div>"
        f"<div><strong>Paper approved</strong><br>{counts['paper_approved']}</div>"
        f"<div><strong>Paper rejected</strong><br>{counts['paper_rejected']}</div>"
        "</section>"
        "<section>"
        "<h2>Requests</h2>"
        "<form method='get' action='/admin' style='display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px;'>"
        f"<label>Format<br><input name='format' value='{escape(str(filters['format']))}'></label>"
        f"<label>Electronic status<br><input name='electronic_status' value='{escape(str(filters['electronic_status']))}'></label>"
        f"<label>Paper status<br><input name='paper_status' value='{escape(str(filters['paper_status']))}'></label>"
        "<button type='submit'>Apply filters</button>"
        "</form>"
        "<table border='1' cellpadding='8' cellspacing='0' style='width:100%;border-collapse:collapse;'>"
        "<thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Format</th><th>Electronic</th><th>Paper</th><th>Created</th></tr></thead>"
        f"<tbody>{rows_html}</tbody></table>"
        "</section></main></body></html>"
    )


def _render_request_detail_page(
    request_row: object,
    *,
    events: list[object],
    error_message: str | None = None,
) -> str:
    assert request_row is not None
    fields = [
        ("ID", request_row["id"]),
        ("First name", request_row["first_name"]),
        ("Last name", request_row["last_name"]),
        ("Organization", request_row["organization"] or ""),
        ("Position", request_row["position"] or ""),
        ("Email", request_row["email"]),
        ("Phone", request_row["phone"] or ""),
        ("Purpose", request_row["purpose"]),
        ("Format", request_row["format"]),
        ("Electronic status", request_row["electronic_status"]),
        ("Paper status", request_row["paper_status"]),
        ("Paper pickup info", request_row["paper_pickup_info"] or ""),
        ("Paper admin note", request_row["paper_admin_note"] or ""),
        ("Created", request_row["created_at"]),
        ("Updated", request_row["updated_at"]),
    ]
    rows_html = "".join(
        f"<tr><th align='left'>{escape(str(label))}</th><td>{escape(str(value))}</td></tr>"
        for label, value in fields
    )
    error_html = ""
    if error_message:
        error_html = f"<p style='color:#b42318;'>{escape(error_message)}</p>"

    decision_form_html = ""
    if str(request_row["paper_status"]) == "review":
        decision_form_html = (
            "<section style='margin:24px 0;'>"
            "<h2>Paper review</h2>"
            "<form method='post' action='/admin/requests/"
            f"{request_row['id']}"
            "/paper-decision' style='display:grid;gap:12px;'>"
            "<label>Decision<br>"
            "<select name='decision'>"
            "<option value='approve'>Approve</option>"
            "<option value='reject'>Reject</option>"
            "</select></label>"
            "<label>Pickup information<br>"
            "<textarea name='pickup_info' rows='4' style='width:100%;'></textarea></label>"
            "<label>Admin note<br>"
            "<textarea name='admin_note' rows='4' style='width:100%;'></textarea></label>"
            "<button type='submit' style='width:max-content;'>Save decision</button>"
            "</form>"
            "<p>Approval requires pickup information. Rejection requires an admin note.</p>"
            "</section>"
        )

    events_html = "".join(
        (
            "<tr>"
            f"<td>{escape(str(event['created_at']))}</td>"
            f"<td>{escape(str(event['event_type']))}</td>"
            f"<td>{escape(str(event['metadata_json'] or ''))}</td>"
            "</tr>"
        )
        for event in events
    )
    if not events_html:
        events_html = "<tr><td colspan='3'>No admin events yet.</td></tr>"

    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>Request {request_row['id']}</title></head><body>"
        "<main style='max-width:800px;margin:32px auto;font-family:Arial,sans-serif;'>"
        f"<p><a href='/admin'>Back to dashboard</a></p><h1>Request #{request_row['id']}</h1>"
        f"{error_html}"
        "<table border='1' cellpadding='8' cellspacing='0' style='width:100%;border-collapse:collapse;'>"
        f"{rows_html}</table>"
        f"{decision_form_html}"
        "<section><h2>Admin events</h2>"
        "<table border='1' cellpadding='8' cellspacing='0' style='width:100%;border-collapse:collapse;'>"
        "<thead><tr><th>Created</th><th>Event</th><th>Metadata</th></tr></thead>"
        f"<tbody>{events_html}</tbody></table></section></main></body></html>"
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        init_database(app_settings.database_path)
        seed_admin_user(app_settings.database_path, app_settings)
        yield

    app = FastAPI(title=app_settings.app_name, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok", "env": app_settings.app_env}

    @app.get("/download/{token}")
    async def download_book(token: str) -> FileResponse:
        try:
            file_path, file_name = resolve_download(
                database_path=app_settings.database_path,
                settings=app_settings,
                raw_token=token,
            )
        except LookupError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except TimeoutError as error:
            raise HTTPException(status_code=410, detail=str(error)) from error
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

        return FileResponse(
            path=file_path,
            filename=file_name,
            media_type="application/pdf",
        )

    @app.post(
        f"{app_settings.api_prefix}/request-access",
        response_model=RequestAccessResponse,
        status_code=201,
    )
    async def request_access(payload: RequestAccessPayload) -> RequestAccessResponse:
        result = create_request_access(
            database_path=app_settings.database_path,
            settings=app_settings,
            payload=payload.model_dump(),
        )
        return RequestAccessResponse(
            status="accepted",
            request_id=result.request_id,
            electronic_status=result.electronic_status,
            paper_status=result.paper_status,
            email_job_id=result.email_job_id,
            delivery_scheduled_for=result.send_after,
        )

    @app.get("/admin/login", response_class=HTMLResponse)
    async def admin_login_page() -> HTMLResponse:
        return HTMLResponse(_render_login_page())

    @app.post("/admin/login")
    async def admin_login(request: Request):
        form_data = parse_qs((await request.body()).decode("utf-8"))
        email = str(form_data.get("email", [""])[0]).strip().lower()
        password = str(form_data.get("password", [""])[0])
        admin_user = authenticate_admin(
            app_settings.database_path,
            app_settings,
            email=email,
            password=password,
        )
        if admin_user is None:
            return HTMLResponse(_render_login_page("Invalid credentials."), status_code=401)

        response = RedirectResponse(url="/admin", status_code=303)
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=create_admin_session(app_settings, int(admin_user["id"])),
            httponly=True,
            samesite="lax",
            secure=app_settings.app_env == "production",
            max_age=8 * 60 * 60,
        )
        return response

    @app.post("/admin/logout")
    async def admin_logout() -> RedirectResponse:
        response = RedirectResponse(url="/admin/login", status_code=303)
        response.delete_cookie(SESSION_COOKIE_NAME)
        return response

    @app.get("/admin", response_class=HTMLResponse)
    async def admin_dashboard(
        request: Request,
        format: str | None = None,
        electronic_status: str | None = None,
        paper_status: str | None = None,
    ) -> HTMLResponse:
        admin_user = require_admin_user(request, app_settings.database_path, app_settings)
        context = build_dashboard_context(
            app_settings.database_path,
            request_format=format,
            electronic_status=electronic_status,
            paper_status=paper_status,
        )
        return HTMLResponse(_render_dashboard_page(str(admin_user["email"]), context))

    @app.get("/admin/requests/{request_id}", response_class=HTMLResponse)
    async def admin_request_detail(request: Request, request_id: int) -> HTMLResponse:
        require_admin_user(request, app_settings.database_path, app_settings)
        request_row = get_request(app_settings.database_path, request_id)
        if request_row is None:
            raise HTTPException(status_code=404, detail="Request was not found")

        events = list_admin_events(
            app_settings.database_path,
            entity_type="request",
            entity_id=request_id,
        )
        return HTMLResponse(_render_request_detail_page(request_row, events=events))

    @app.post("/admin/requests/{request_id}/paper-decision")
    async def admin_paper_decision(request: Request, request_id: int):
        admin_user = require_admin_user(request, app_settings.database_path, app_settings)
        form_data = parse_qs((await request.body()).decode("utf-8"))
        decision = str(form_data.get("decision", [""])[0]).strip().lower()
        pickup_info = str(form_data.get("pickup_info", [""])[0])
        admin_note = str(form_data.get("admin_note", [""])[0])

        try:
            apply_paper_decision(
                app_settings.database_path,
                admin_user_id=int(admin_user["id"]),
                request_id=request_id,
                decision=decision,
                pickup_info=pickup_info,
                admin_note=admin_note,
            )
        except LookupError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ValueError as error:
            request_row = get_request(app_settings.database_path, request_id)
            if request_row is None:
                raise HTTPException(status_code=404, detail="Request was not found") from error
            events = list_admin_events(
                app_settings.database_path,
                entity_type="request",
                entity_id=request_id,
            )
            return HTMLResponse(
                _render_request_detail_page(
                    request_row,
                    events=events,
                    error_message=str(error),
                ),
                status_code=400,
            )

        return RedirectResponse(url=f"/admin/requests/{request_id}", status_code=303)

    return app


app = create_app()
