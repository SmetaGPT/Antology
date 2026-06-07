from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from html import escape
from sqlite3 import Row
from textwrap import dedent
from time import perf_counter
from typing import Literal, cast
from urllib.parse import parse_qs

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from .admin_service import (
    ADMIN_LOGIN_PATH,
    SESSION_COOKIE_NAME,
    authenticate_admin,
    build_books_page_context,
    build_dashboard_context,
    build_requests_page_context,
    build_settings_page_context,
    create_admin_session,
    get_effective_delivery_delay_minutes,
    require_admin_user,
    seed_admin_user,
)
from .book_admin_service import store_uploaded_book, switch_active_book_version
from .config import Settings, get_settings
from .db import init_database
from .download_service import resolve_download
from .email_service import persist_mail_settings
from .logging_utils import configure_logging
from .paper_review_service import apply_paper_decision
from .repository import create_admin_event, create_site_visit, get_request, list_admin_events, set_system_setting
from .request_access_service import (
    RateLimitExceededError,
    build_request_confirmation_message,
    create_request_access,
)
from .schemas import RequestAccessPayload, RequestAccessResponse, SiteVisitPayload
from .worker_service import process_due_email_jobs, sync_incoming_emails


def _format_file_size(size_bytes: object) -> str:
    value = int(size_bytes or 0)
    units = ["B", "KB", "MB", "GB"]
    unit_index = 0
    size = float(value)
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    precision = 0 if unit_index == 0 else 1
    return f"{size:.{precision}f} {units[unit_index]}"


def _badge_class_for_status(status_value: str) -> str:
    mapping = {
        "sent": "badge-success",
        "approved": "badge-success",
        "review": "badge-warn",
        "pending": "badge-info",
        "electronic": "badge-info",
        "both": "badge-info",
        "failed": "badge-danger",
        "rejected": "badge-danger",
        "paper": "badge-neutral",
        "none": "badge-neutral",
    }
    return mapping.get(status_value, "badge-neutral")


def _render_status_badge(status_value: object, label: str | None = None) -> str:
    normalized = str(status_value or "none")
    text = escape(label or normalized)
    badge_class = _badge_class_for_status(normalized)
    return f"<span class='badge {badge_class}'>{text}</span>"


def _render_admin_styles() -> str:
    return dedent(
        """
        <style>
          :root {
            color-scheme: light;
            --bg: #f5f1e8;
            --panel: #ffffff;
            --panel-soft: #faf7f1;
            --line: #d7cfc1;
            --line-strong: #c8bea9;
            --text: #1f1a16;
            --muted: #847668;
            --brand: #2b2fda;
            --sidebar: #1c1b18;
            --sidebar-soft: #24231f;
            --sidebar-text: #f4efe6;
            --success: #2f7d32;
            --danger: #b5362f;
            --warn: #ad6f0c;
            --info: #1b66c9;
            --shadow: 0 18px 40px rgba(29, 24, 19, 0.07);
            font-family: Inter, Segoe UI, Arial, sans-serif;
          }

          * { box-sizing: border-box; }
          body {
            margin: 0;
            background: var(--bg);
            color: var(--text);
            font-family: Inter, Segoe UI, Arial, sans-serif;
          }

          a { color: inherit; text-decoration: none; }
          button, input, textarea, select {
            font: inherit;
          }

          .admin-shell {
            min-height: 100vh;
            display: grid;
            grid-template-columns: 220px minmax(0, 1fr);
          }

          .sidebar {
            background: var(--sidebar);
            color: var(--sidebar-text);
            display: flex;
            flex-direction: column;
            border-right: 1px solid rgba(255,255,255,0.08);
          }

          .sidebar-brand {
            padding: 26px 24px;
            font-size: 15px;
            font-weight: 700;
            border-bottom: 1px solid rgba(255,255,255,0.08);
          }

          .sidebar-brand span { color: #6875ff; }
          .sidebar-section-title {
            padding: 20px 24px 8px;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: rgba(244, 239, 230, 0.42);
          }

          .sidebar-nav {
            display: grid;
            gap: 4px;
            padding: 0 12px;
          }

          .sidebar-link {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 12px;
            border-radius: 10px;
            color: rgba(244, 239, 230, 0.82);
            transition: background 0.2s ease, color 0.2s ease;
          }

          .sidebar-link:hover,
          .sidebar-link.active {
            background: var(--sidebar-soft);
            color: #ffffff;
          }

          .sidebar-link svg {
            width: 16px;
            height: 16px;
            stroke: currentColor;
            fill: none;
            stroke-width: 1.8;
          }

          .sidebar-user {
            margin-top: auto;
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 18px 20px;
            border-top: 1px solid rgba(255,255,255,0.08);
          }

          .sidebar-user-avatar {
            width: 30px;
            height: 30px;
            border-radius: 999px;
            background: #6875ff;
            color: #fff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 700;
            flex: 0 0 auto;
          }

          .sidebar-user-meta {
            min-width: 0;
          }

          .sidebar-user-name {
            font-size: 14px;
            font-weight: 600;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }

          .sidebar-user-email {
            font-size: 12px;
            color: rgba(244, 239, 230, 0.55);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }

          .admin-main {
            padding: 24px 28px 34px;
          }

          .topbar {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 20px;
            margin-bottom: 18px;
          }

          .page-title {
            margin: 0;
            font-size: 20px;
            font-weight: 800;
          }

          .page-subtitle {
            margin: 2px 0 0;
            color: var(--muted);
            font-size: 14px;
          }

          .ghost-button,
          .primary-button,
          .secondary-button {
            border-radius: 10px;
            border: 1px solid var(--line-strong);
            padding: 8px 14px;
            background: #fff;
            color: var(--text);
            cursor: pointer;
          }

          .ghost-button:hover,
          .secondary-button:hover {
            background: #f9f5ee;
          }

          .primary-button {
            background: #1f1d1a;
            color: #fff;
            border-color: #1f1d1a;
            font-weight: 600;
          }

          .primary-button:hover {
            background: #2b2825;
          }

          .logout-form { margin: 0; }

          .stats-grid {
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: 12px;
            margin-bottom: 18px;
          }

          .stat-card,
          .panel {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 16px;
            box-shadow: var(--shadow);
          }

          .stat-card {
            padding: 13px 15px;
          }

          .stat-label {
            color: var(--muted);
            font-size: 12px;
            margin-bottom: 5px;
          }

          .stat-value {
            font-size: 15px;
            font-weight: 800;
          }

          .stat-value.info { color: var(--info); }
          .stat-value.warn { color: var(--warn); }
          .stat-value.success { color: var(--success); }
          .stat-value.danger { color: var(--danger); }

          .split-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.15fr) minmax(0, 0.85fr);
            gap: 20px;
            margin-bottom: 18px;
            align-items: start;
          }

          .panel {
            padding: 16px;
          }

          .panel-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 12px;
          }

          .panel-title {
            margin: 0;
            font-size: 15px;
            font-weight: 800;
          }

          .panel-icon {
            width: 16px;
            height: 16px;
            stroke: var(--muted);
            fill: none;
            stroke-width: 1.8;
            flex: 0 0 auto;
          }

          .notice {
            display: flex;
            align-items: center;
            gap: 10px;
            border-radius: 12px;
            padding: 10px 12px;
            margin-bottom: 12px;
            border: 1px solid #b7d2f5;
            background: #eaf4ff;
            color: var(--info);
            font-size: 13px;
          }

          .notice.error {
            border-color: #ecc0bc;
            background: #fff3f1;
            color: var(--danger);
          }

          .form-grid-2,
          .filter-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 12px;
          }

          .upload-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1.2fr auto;
            gap: 10px;
            align-items: end;
          }

          .upload-actions {
            display: grid;
            gap: 8px;
            align-self: stretch;
          }

          .filter-grid {
            grid-template-columns: 1.15fr 1.15fr 1.15fr auto;
            align-items: end;
          }

          .field-label {
            display: block;
            margin-bottom: 5px;
            color: var(--muted);
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
          }

          .text-input,
          .select-input,
          .file-input {
            width: 100%;
            border: 1px solid var(--line);
            border-radius: 10px;
            padding: 9px 11px;
            background: #fff;
            color: var(--text);
          }

          .file-drop {
            border: 1px dashed var(--line-strong);
            border-radius: 12px;
            padding: 12px 14px;
            text-align: center;
            background: var(--panel-soft);
            color: var(--muted);
            margin-top: 8px;
          }

          .checkbox-row {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 10px 0 12px;
            color: var(--muted);
            font-size: 13px;
          }

          .checkbox-row.compact {
            margin: 0;
            font-size: 12px;
            white-space: nowrap;
          }

          .table-wrap {
            overflow-x: auto;
            border: 1px solid var(--line);
            border-radius: 14px;
            background: #fff;
          }

          table {
            width: 100%;
            border-collapse: collapse;
          }

          thead th {
            text-align: left;
            font-size: 12px;
            color: var(--muted);
            letter-spacing: 0.06em;
            text-transform: uppercase;
            padding: 12px 10px;
            border-bottom: 1px solid var(--line);
            white-space: nowrap;
          }

          tbody td {
            padding: 12px 10px;
            border-bottom: 1px solid #eee7db;
            vertical-align: top;
            font-size: 13px;
          }

          tbody tr:last-child td {
            border-bottom: 0;
          }

          .table-link {
            color: #1f1d1a;
            font-weight: 700;
          }

          .empty-state {
            padding: 24px 16px;
            text-align: center;
            color: #b3a797;
          }

          .empty-state svg {
            width: 24px;
            height: 24px;
            stroke: currentColor;
            fill: none;
            stroke-width: 1.8;
            margin-bottom: 8px;
          }

          .badge {
            display: inline-flex;
            align-items: center;
            padding: 5px 9px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
            background: #f0ece5;
            color: var(--muted);
            border: 1px solid #e0d7ca;
          }

          .badge-info { color: var(--info); background: #eef5ff; border-color: #c8dcff; }
          .badge-success { color: var(--success); background: #edf8ee; border-color: #cde7d0; }
          .badge-danger { color: var(--danger); background: #fff1f0; border-color: #efcac7; }
          .badge-warn { color: var(--warn); background: #fff7ea; border-color: #ead7aa; }
          .badge-neutral { color: #726759; background: #f4efe7; border-color: #e1d8cb; }

          .activity-list {
            display: grid;
            gap: 10px;
          }

          .activity-compare {
            display: grid;
            gap: 8px;
          }

          .activity-compare-head,
          .activity-compare-row {
            display: grid;
            grid-template-columns: 1.2fr 1fr 1fr 1fr;
            gap: 10px;
            align-items: center;
          }

          .activity-compare-head {
            color: var(--muted);
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
          }

          .activity-compare-row {
            padding: 9px 10px;
            border: 1px solid var(--line);
            border-radius: 12px;
            background: var(--panel-soft);
            font-size: 13px;
          }

          .activity-compare-row .period {
            font-weight: 700;
          }

          .activity-footnote {
            margin-top: 2px;
            color: var(--muted);
            font-size: 12px;
            line-height: 1.45;
          }

          .activity-item {
            padding: 10px 12px;
            border: 1px solid var(--line);
            border-radius: 12px;
            background: var(--panel-soft);
          }

          .activity-title {
            font-size: 13px;
            font-weight: 700;
            margin-bottom: 3px;
          }

          .activity-meta {
            color: var(--muted);
            font-size: 12px;
          }

          .section-stack {
            display: grid;
            gap: 14px;
          }

          .detail-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 12px;
          }

          .detail-card {
            padding: 12px 14px;
            border: 1px solid var(--line);
            border-radius: 12px;
            background: var(--panel-soft);
          }

          .detail-label {
            color: var(--muted);
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin-bottom: 5px;
          }

          .detail-value {
            font-size: 13px;
            line-height: 1.45;
            word-break: break-word;
          }

          .back-link {
            color: var(--muted);
            font-size: 13px;
            margin-bottom: 8px;
            display: inline-flex;
          }

          .summary-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 14px;
            margin-bottom: 18px;
          }

          .summary-card {
            padding: 14px 16px;
            border: 1px solid var(--line);
            border-radius: 14px;
            background: var(--panel-soft);
          }

          .summary-card strong {
            display: block;
            margin-bottom: 6px;
            font-size: 13px;
          }

          .summary-card p {
            margin: 0;
            color: var(--muted);
            font-size: 12px;
            line-height: 1.5;
          }

          .inline-actions {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
          }

                    .mail-settings-form {
                        display: grid;
                        gap: 12px;
                    }

                    .mail-provider-grid {
                        display: grid;
                        grid-template-columns: 1.05fr 1fr;
                        gap: 10px;
                    }

                    .mail-protocol-title {
                        color: var(--muted);
                        font-size: 12px;
                        font-weight: 800;
                        letter-spacing: 0.06em;
                        text-transform: uppercase;
                    }

                    .mail-grid-3,
                    .mail-grid-2 {
                        display: grid;
                        gap: 10px;
                    }

                    .mail-grid-3 {
                        grid-template-columns: repeat(3, minmax(0, 1fr));
                    }

                    .mail-grid-2 {
                        grid-template-columns: repeat(2, minmax(0, 1fr));
                    }

                    .mail-divider {
                        height: 1px;
                        background: var(--line);
                    }

                    .mail-footer-grid {
                        display: grid;
                        grid-template-columns: 1.05fr 1fr;
                        gap: 10px;
                        align-items: start;
                    }

                    .mail-check-actions {
                        display: grid;
                        gap: 10px;
                    }

                    .mail-checkboxes {
                        display: grid;
                        gap: 8px;
                    }

                    .mail-actions {
                        display: flex;
                        align-items: center;
                        gap: 10px;
                        flex-wrap: wrap;
                    }

                    .mail-note {
                        margin: 0;
                    }

          .meta-note {
            color: var(--muted);
            font-size: 12px;
            line-height: 1.5;
          }

          .pagination {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-top: 12px;
            color: var(--muted);
            font-size: 12px;
          }

          .pagination-links {
            display: flex;
            align-items: center;
            gap: 8px;
          }

          .quick-list {
            display: grid;
            gap: 10px;
          }

          .quick-item {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 12px;
            padding: 10px 12px;
            border: 1px solid var(--line);
            border-radius: 12px;
            background: var(--panel-soft);
          }

          .quick-item-main {
            min-width: 0;
          }

          .quick-item-title {
            font-size: 13px;
            font-weight: 700;
            margin-bottom: 4px;
          }

          .quick-item-meta {
            color: var(--muted);
            font-size: 12px;
            line-height: 1.45;
            word-break: break-word;
          }

          @media (max-width: 1180px) {
            .stats-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
            .split-grid { grid-template-columns: 1fr; }
            .filter-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .upload-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
                        .mail-grid-3 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
          }

          @media (max-width: 920px) {
            .admin-shell { grid-template-columns: 1fr; }
            .sidebar {
              position: sticky;
              top: 0;
              z-index: 20;
            }
            .admin-main { padding: 18px 14px 24px; }
          }

          @media (max-width: 720px) {
            .stats-grid,
            .summary-grid,
            .detail-grid,
            .form-grid-2,
            .filter-grid {
              grid-template-columns: 1fr;
            }
                        .mail-provider-grid,
                        .mail-grid-2,
                        .mail-grid-3,
                        .mail-footer-grid {
                            grid-template-columns: 1fr;
                        }
            .upload-grid,
            .activity-compare-head,
            .activity-compare-row {
              grid-template-columns: 1fr;
            }
            .topbar {
              flex-direction: column;
              align-items: stretch;
            }
          }
        </style>
        """
    ).strip()


def _render_sidebar_icon(kind: str, class_name: str = "panel-icon") -> str:
    icons = {
        "overview": "<svg viewBox='0 0 24 24'><rect x='3' y='3' width='7' height='7' rx='1.5'></rect><rect x='14' y='3' width='7' height='7' rx='1.5'></rect><rect x='3' y='14' width='7' height='7' rx='1.5'></rect><rect x='14' y='14' width='7' height='7' rx='1.5'></rect></svg>",
        "book": "<svg viewBox='0 0 24 24'><path d='M6 4.5h9a3 3 0 0 1 3 3V20H9a3 3 0 0 0-3 3z'></path><path d='M6 4.5V20'></path></svg>",
        "requests": "<svg viewBox='0 0 24 24'><path d='M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z'></path></svg>",
        "settings": "<svg viewBox='0 0 24 24'><circle cx='12' cy='12' r='3'></circle><path d='M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06A1.7 1.7 0 0 0 15 19.4a1.7 1.7 0 0 0-1 .6 1.7 1.7 0 0 0-.4 1.07V21a2 2 0 1 1-4 0v-.1A1.7 1.7 0 0 0 9 19.4a1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-.6-1 1.7 1.7 0 0 0-1.07-.4H2.9a2 2 0 1 1 0-4H3a1.7 1.7 0 0 0 1.6-1A1.7 1.7 0 0 0 4.26 6.7l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.7 1.7 0 0 0 9 4.6h.1a1.7 1.7 0 0 0 1-.6 1.7 1.7 0 0 0 .4-1.07V2.9a2 2 0 1 1 4 0V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.87-.34l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.7 1.7 0 0 0 19.4 9c0 .39.14.77.4 1.07.25.3.61.51 1 .6h.1a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1 .4c-.3.25-.51.61-.6 1z'></path></svg>",
        "activity": "<svg viewBox='0 0 24 24'><path d='M3 12h4l2.5-6 4 12 2.5-6H21'></path></svg>",
        "panel": "<svg viewBox='0 0 24 24'><rect x='5' y='4' width='14' height='16' rx='2'></rect><path d='M8 8h8M8 12h8M8 16h5'></path></svg>",
        "search": "<svg viewBox='0 0 24 24'><circle cx='11' cy='11' r='7'></circle><path d='m20 20-3.5-3.5'></path></svg>",
        "upload": "<svg viewBox='0 0 24 24'><path d='M12 16V4'></path><path d='m7 9 5-5 5 5'></path><path d='M5 20h14'></path></svg>",
    }
    svg = icons.get(kind, icons["panel"])
    svg_attrs = (
        f"class='{escape(class_name)}' "
        "width='16' height='16' fill='none' stroke='currentColor' "
        "stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' "
        "aria-hidden='true' "
    )
    return svg.replace("<svg ", f"<svg {svg_attrs}", 1)


def _render_sidebar(admin_email: str, active_nav: str) -> str:
    nav_sections = [
        (
            "Основное",
            [
                ("overview", "Обзор", "/admin"),
                ("book", "Версии книги", "/admin/books"),
                ("requests", "Заявки", "/admin/requests"),
            ],
        ),
        (
            "Система",
            [
                ("settings", "Настройки", "/admin/settings"),
            ],
        ),
    ]
    nav_html_parts: list[str] = []
    for section_title, items in nav_sections:
        nav_html_parts.append(f"<div class='sidebar-section-title'>{escape(section_title)}</div>")
        nav_html_parts.append("<nav class='sidebar-nav'>")
        for key, label, href in items:
            active_class = " active" if active_nav == key else ""
            nav_html_parts.append(
                f"<a class='sidebar-link{active_class}' href='{href}'>"
                f"{_render_sidebar_icon(key, 'sidebar-icon')}"
                f"<span>{escape(label)}</span>"
                "</a>"
            )
        nav_html_parts.append("</nav>")

    display_name = str(admin_email).split("@", maxsplit=1)[0]
    initials = (display_name[:1] or "A").upper()
    return (
        "<aside class='sidebar'>"
        "<div class='sidebar-brand'>Anthology <span>Admin</span></div>"
        f"{''.join(nav_html_parts)}"
        "<div class='sidebar-user'>"
        f"<div class='sidebar-user-avatar'>{escape(initials)}</div>"
        "<div class='sidebar-user-meta'>"
        f"<div class='sidebar-user-name'>{escape(display_name)}</div>"
        f"<div class='sidebar-user-email'>{escape(admin_email)}</div>"
        "</div></div></aside>"
    )


def _render_admin_page(
    *,
    title: str,
    subtitle: str,
    admin_email: str,
    active_nav: str,
    content_html: str,
) -> str:
    return (
        "<!doctype html><html lang='ru'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1.0'>"
        f"<title>{escape(title)}</title>"
        f"{_render_admin_styles()}</head><body>"
        "<div class='admin-shell'>"
        f"{_render_sidebar(admin_email, active_nav)}"
        "<main class='admin-main'>"
        "<div class='topbar'>"
        "<div>"
        f"<h1 class='page-title'>{escape(title)}</h1>"
        f"<p class='page-subtitle'>{escape(subtitle)}</p>"
        "</div>"
        "<form class='logout-form' method='post' action='/admin/logout'>"
        "<button type='submit' class='ghost-button'>↩ Выйти</button>"
        "</form>"
        "</div>"
        f"{content_html}"
        "</main></div></body></html>"
    )


def _render_empty_state(icon: str, message: str) -> str:
    return (
        "<div class='empty-state'>"
        f"{_render_sidebar_icon(icon, 'empty-icon')}"
        f"<div>{escape(message)}</div>"
        "</div>"
    )


def _request_format_label(value: object) -> str:
    return {
        "electronic": "электронный",
        "paper": "бумажный",
        "both": "оба",
    }.get(str(value), str(value))


def _electronic_status_label(value: object) -> str:
    return {
        "none": "нет",
        "pending": "ожидает",
        "sent": "отправлено",
        "failed": "ошибка",
    }.get(str(value), str(value))


def _paper_status_label(value: object) -> str:
    return {
        "none": "нет",
        "review": "на проверке",
        "approved": "одобрено",
        "rejected": "отклонено",
    }.get(str(value), str(value))


def _build_query(params: dict[str, object]) -> str:
    query_parts = [
        f"{escape(str(key))}={escape(str(value))}"
        for key, value in params.items()
        if value not in {None, "", 0}
    ]
    return f"?{'&'.join(query_parts)}" if query_parts else ""


def _render_pagination(base_path: str, pagination: dict[str, int], extra_params: dict[str, object] | None = None) -> str:
    page = int(pagination["page"])
    total_pages = int(pagination["total_pages"])
    total_count = int(pagination["total_count"])
    if total_count <= 0:
        return ""

    params = dict(extra_params or {})
    prev_link = ""
    next_link = ""

    if page > 1:
        prev_link = (
            f"<a class='secondary-button' href='{base_path}{_build_query({**params, 'page': page - 1})}'>← Назад</a>"
        )
    if page < total_pages:
        next_link = (
            f"<a class='secondary-button' href='{base_path}{_build_query({**params, 'page': page + 1})}'>Далее →</a>"
        )

    return (
        "<div class='pagination'>"
        f"<span>Страница {page} из {total_pages} · всего записей: {total_count}</span>"
        "<div class='pagination-links'>"
        f"{prev_link}{next_link}"
        "</div></div>"
    )


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
        "<form method='post' action='/ad/log' style='display:grid;gap:12px;'>"
        "<label>Email<br><input type='email' name='email' required style='width:100%;padding:8px;'></label>"
        "<label>Password<br><input type='password' name='password' required style='width:100%;padding:8px;'></label>"
        "<button type='submit' style='padding:10px 14px;'>Sign in</button>"
        "</form></main></body></html>"
    )


def _render_dashboard_page(
    admin_email: str,
    context: dict[str, object],
) -> str:
    counts = cast(dict[str, object], context["counts"])
    activity_summary = cast(dict[str, object], context["activity_summary"])
    request_rows = cast(list[Row], context["recent_requests"])
    active_version = cast(Row | None, context["active_version"])
    delivery_delay_minutes = int(context["delivery_delay_minutes"])
    active_version_html = (
        "Активная версия не выбрана"
        if active_version is None
        else (
            f"{escape(str(active_version['title']))} / "
              f"{escape(str(active_version['version_label']))} / "
              f"{escape(str(active_version['file_name']))}"
          )
    )
    recent_rows_html = "".join(
        (
            "<div class='quick-item'>"
            "<div class='quick-item-main'>"
            f"<div class='quick-item-title'><a class='table-link' href='/admin/requests/{row['id']}'>"
            f"#{row['id']} · {escape(str(row['first_name']))} {escape(str(row['last_name']))}</a></div>"
            f"<div class='quick-item-meta'>{escape(str(row['email']))}<br>{escape(str(row['created_at']))}</div>"
            "</div>"
            "<div class='inline-actions'>"
            f"{_render_status_badge(row['format'], _request_format_label(row['format']))}"
            f"{_render_status_badge(row['electronic_status'], _electronic_status_label(row['electronic_status']))}"
            f"{_render_status_badge(row['paper_status'], _paper_status_label(row['paper_status']))}"
            "</div></div>"
        )
        for row in request_rows
    )
    if not recent_rows_html:
        recent_rows_html = _render_empty_state("search", "Последние заявки пока отсутствуют")

    activity_rows = [
        ("За день", int(activity_summary["day_visits"]), int(activity_summary["day_requests"]), float(activity_summary["day_conversion"])),
        ("За месяц", int(activity_summary["month_visits"]), int(activity_summary["month_requests"]), float(activity_summary["month_conversion"])),
        ("За год", int(activity_summary["year_visits"]), int(activity_summary["year_requests"]), float(activity_summary["year_conversion"])),
    ]
    activity_html = (
        "<div class='activity-compare'>"
        "<div class='activity-compare-head'>"
        "<span>Период</span><span>Посещения</span><span>Заявки</span><span>Конверсия</span>"
        "</div>"
        + "".join(
            "<div class='activity-compare-row'>"
            f"<span class='period'>{escape(label)}</span>"
            f"<span>{visits}</span>"
            f"<span>{requests}</span>"
            f"<span>{conversion:.1f}%</span>"
            "</div>"
            for label, visits, requests, conversion in activity_rows
        )
          + "<div class='activity-footnote'>"
          f"Последний визит: {escape(str(activity_summary['latest_visit_at'] or '—'))}<br>"
          f"Последняя заявка: {escape(str(activity_summary['latest_request_at'] or '—'))}"
          "</div></div>"
      )

    content_html = (
        "<section class='stats-grid'>"
        f"<div class='stat-card'><div class='stat-label'>Всего заявок</div><div class='stat-value'>{counts['total_requests']}</div></div>"
        f"<div class='stat-card'><div class='stat-label'>Отправлено (эл.)</div><div class='stat-value info'>{counts['electronic_sent']}</div></div>"
        f"<div class='stat-card'><div class='stat-label'>Ошибки (эл.)</div><div class='stat-value danger'>{counts['electronic_failed']}</div></div>"
        f"<div class='stat-card'><div class='stat-label'>На проверке</div><div class='stat-value warn'>{counts['paper_review']}</div></div>"
        f"<div class='stat-card'><div class='stat-label'>Одобрено</div><div class='stat-value success'>{counts['paper_approved']}</div></div>"
        f"<div class='stat-card'><div class='stat-label'>Отклонено</div><div class='stat-value danger'>{counts['paper_rejected']}</div></div>"
        "</section>"
        "<section class='split-grid'>"
        "<div class='panel'>"
        "<div class='panel-header'>"
        f"{_render_sidebar_icon('overview')}"
        "<h2 class='panel-title'>Краткий обзор</h2>"
        "</div>"
        "<div class='summary-grid'>"
        "<div class='summary-card'>"
        "<strong>Активная версия книги</strong>"
        f"<p>{active_version_html}</p>"
        "<div style='margin-top:10px;'><a class='secondary-button' href='/admin/books'>Перейти к версиям</a></div>"
        "</div>"
        "<div class='summary-card'>"
        "<strong>Отправка электронной ссылки</strong>"
        f"<p>Подтверждение заявки уходит сразу. Ссылка на скачивание отправляется через {delivery_delay_minutes} мин.</p>"
        "<div style='margin-top:10px;'><a class='secondary-button' href='/admin/settings'>Изменить настройку</a></div>"
        "</div>"
        "</div>"
        "<div class='panel-header' style='margin-top:4px;'>"
        f"{_render_sidebar_icon('requests')}"
        "<h2 class='panel-title'>Последние заявки</h2>"
        "</div>"
        f"<div class='quick-list'>{recent_rows_html}</div>"
        "<div style='margin-top:12px;'><a class='secondary-button' href='/admin/requests'>Открыть все заявки</a></div>"
        "</div>"
        "<div class='panel'>"
        "<div class='panel-header'>"
        f"{_render_sidebar_icon('activity')}"
        "<h2 class='panel-title'>Активность</h2>"
        "</div>"
        f"{activity_html}"
        "</div>"
        "</section>"
    )
    return _render_admin_page(
        title="Панель администратора",
        subtitle="Обзор заявок, посещений и текущих правил доставки",
        admin_email=admin_email,
        active_nav="overview",
        content_html=content_html,
    )


def _render_books_page(
    admin_email: str,
    context: dict[str, object],
    *,
    error_message: str | None = None,
) -> str:
    versions = cast(list[Row], context["versions"])
    active_version = cast(Row | None, context["active_version"])
    pagination = cast(dict[str, int], context["pagination"])
    error_html = (
        f"<div class='notice error'>{escape(error_message)}</div>"
        if error_message
        else ""
    )
    active_version_html = (
        "Активная версия не выбрана"
        if active_version is None
        else (
            f"{escape(str(active_version['title']))} / "
            f"{escape(str(active_version['version_label']))} / "
            f"{escape(str(active_version['file_name']))}"
        )
    )
    versions_rows_html = "".join(
        (
            "<tr>"
            f"<td>{row['id']}</td>"
            f"<td>{escape(str(row['title']))}</td>"
            f"<td>{escape(str(row['version_label']))}</td>"
            f"<td>{escape(str(row['file_name']))}</td>"
            f"<td>{_format_file_size(row['file_size'])}</td>"
            f"<td>{_render_status_badge('approved' if int(row['is_active']) == 1 else 'none', 'да' if int(row['is_active']) == 1 else 'нет')}</td>"
            "<td>"
            f"<form method='post' action='/admin/books/{row['id']}/activate'>"
            "<button type='submit' class='secondary-button'>Сделать активной</button>"
            "</form>"
            "</td></tr>"
        )
        for row in versions
    )
    if not versions_rows_html:
        versions_rows_html = f"<tr><td colspan='7'>{_render_empty_state('book', 'Версии книги ещё не загружены')}</td></tr>"

    content_html = (
        f"{error_html}"
        "<section class='panel' style='margin-bottom:18px;'>"
        "<div class='panel-header'>"
        f"{_render_sidebar_icon('upload')}"
        "<h2 class='panel-title'>Загрузить версию книги</h2>"
        "</div>"
        f"<div class='notice'>{active_version_html}</div>"
        "<form method='post' action='/admin/books/upload' enctype='multipart/form-data'>"
        "<div class='upload-grid'>"
        "<div><label class='field-label'>Название</label><input class='text-input' name='title' value='Anthology' required></div>"
        "<div><label class='field-label'>Метка версии</label><input class='text-input' name='version_label' placeholder='v1-2026-06' required></div>"
        "<div><label class='field-label'>PDF-файл</label><input class='file-input' type='file' name='book_file' accept='application/pdf' required></div>"
        "<div class='upload-actions'>"
        "<label class='checkbox-row compact'><input type='checkbox' name='make_active' checked> Сделать активной</label>"
        "<button type='submit' class='primary-button'>Загрузить книгу</button>"
        "</div></div></form>"
        "</section>"
        "<section class='panel'>"
        "<div class='panel-header'>"
        f"{_render_sidebar_icon('book')}"
        "<h2 class='panel-title'>Версии книги</h2>"
        "</div>"
        "<div class='table-wrap'><table><thead><tr>"
        "<th>ID</th><th>Название</th><th>Версия</th><th>Файл</th><th>Размер</th><th>Активна</th><th>Действия</th>"
        "</tr></thead><tbody>"
        f"{versions_rows_html}"
        "</tbody></table></div>"
        f"{_render_pagination('/admin/books', pagination)}"
        "</section>"
    )
    return _render_admin_page(
        title="Версии книги",
        subtitle="Загрузка, активация и история PDF-версий",
        admin_email=admin_email,
        active_nav="book",
        content_html=content_html,
    )


def _render_requests_page(
    admin_email: str,
    context: dict[str, object],
) -> str:
    filters = cast(dict[str, str], context["filters"])
    request_rows = cast(list[Row], context["requests"])
    pagination = cast(dict[str, int], context["pagination"])

    def _option(value: str, label: str, current: str) -> str:
        selected = " selected" if value == current else ""
        return f"<option value='{escape(value)}'{selected}>{escape(label)}</option>"

    rows_html = "".join(
        (
            "<tr>"
            f"<td><a class='table-link' href='/admin/requests/{row['id']}'>{row['id']}</a></td>"
            f"<td><a class='table-link' href='/admin/requests/{row['id']}'>{escape(str(row['first_name']))} {escape(str(row['last_name']))}</a></td>"
            f"<td>{escape(str(row['email']))}</td>"
            f"<td>{_render_status_badge(row['format'], _request_format_label(row['format']))}</td>"
            f"<td>{_render_status_badge(row['electronic_status'], _electronic_status_label(row['electronic_status']))}</td>"
            f"<td>{_render_status_badge(row['paper_status'], _paper_status_label(row['paper_status']))}</td>"
            f"<td>{escape(str(row['created_at']))}</td>"
            "</tr>"
        )
        for row in request_rows
    )
    if not rows_html:
        rows_html = f"<tr><td colspan='7'>{_render_empty_state('search', 'Заявок по текущим фильтрам не найдено')}</td></tr>"

    format_value = str(filters["format"])
    electronic_value = str(filters["electronic_status"])
    paper_value = str(filters["paper_status"])
    content_html = (
        "<section class='panel'>"
        "<div class='panel-header'>"
        f"{_render_sidebar_icon('requests')}"
        "<h2 class='panel-title'>Заявки</h2>"
        "</div>"
        "<form method='get' action='/admin/requests' class='filter-grid' style='margin-bottom:16px;'>"
        "<div><label class='field-label'>Формат</label><select class='select-input' name='format'>"
        f"{_option('', 'Все форматы', format_value)}"
        f"{_option('electronic', 'Электронный', format_value)}"
        f"{_option('paper', 'Бумажный', format_value)}"
        f"{_option('both', 'Оба варианта', format_value)}"
        "</select></div>"
        "<div><label class='field-label'>Эл. статус</label><select class='select-input' name='electronic_status'>"
        f"{_option('', 'Любой', electronic_value)}"
        f"{_option('pending', 'Ожидает', electronic_value)}"
        f"{_option('sent', 'Отправлено', electronic_value)}"
        f"{_option('failed', 'Ошибка', electronic_value)}"
        f"{_option('none', 'Нет', electronic_value)}"
        "</select></div>"
        "<div><label class='field-label'>Статус (бумага)</label><select class='select-input' name='paper_status'>"
        f"{_option('', 'Любой', paper_value)}"
        f"{_option('review', 'На проверке', paper_value)}"
        f"{_option('approved', 'Одобрено', paper_value)}"
        f"{_option('rejected', 'Отклонено', paper_value)}"
        f"{_option('none', 'Нет', paper_value)}"
        "</select></div>"
        "<div><button type='submit' class='secondary-button'>Применить</button></div>"
        "</form>"
        "<div class='table-wrap'><table><thead><tr>"
        "<th>ID</th><th>Имя</th><th>Email</th><th>Формат</th><th>Эл.</th><th>Бумага</th><th>Создана</th>"
        "</tr></thead><tbody>"
        f"{rows_html}"
        "</tbody></table></div>"
        f"{_render_pagination('/admin/requests', pagination, filters)}"
        "</section>"
    )
    return _render_admin_page(
        title="Заявки",
        subtitle="Фильтрация и обработка поступивших заявок",
        admin_email=admin_email,
        active_nav="requests",
        content_html=content_html,
    )


def _render_settings_page(
    admin_email: str,
    context: dict[str, object],
    *,
    success_message: str | None = None,
    error_message: str | None = None,
) -> str:
    delivery_delay_minutes = int(context["delivery_delay_minutes"])
    default_delivery_delay_minutes = int(context["default_delivery_delay_minutes"])
    mail_settings = cast(dict[str, object], context["mail_settings"])
    inbound_emails = cast(list[Row], context["inbound_emails"])
    inbound_email_count = int(context["inbound_email_count"])
    notices = []
    if success_message:
        notices.append(f"<div class='notice'>{escape(success_message)}</div>")
    if error_message:
        notices.append(f"<div class='notice error'>{escape(error_message)}</div>")

    provider_options_html = "".join(
        (
            f"<option value='{escape(key)}'"
            f"{' selected' if str(mail_settings['provider_key']) == key else ''}>"
            f"{escape(label)}</option>"
        )
        for key, label in (
            ("custom", "Custom"),
            ("local", "Local / Mailpit"),
            ("gmail", "Gmail"),
            ("yandex", "Yandex"),
            ("mailru", "Mail.ru"),
        )
    )
    inbound_rows_html = "".join(
        (
            "<tr>"
            f"<td>{escape(str(row['imported_at'] or '—'))}</td>"
            f"<td>{escape(str(row['from_email'] or '—'))}</td>"
            f"<td>{escape(str(row['subject'] or 'Без темы'))}</td>"
            f"<td>{escape(str(row['mailbox_name'] or 'INBOX'))}</td>"
            "</tr>"
        )
        for row in inbound_emails
    )
    if not inbound_rows_html:
        inbound_rows_html = f"<tr><td colspan='4'>{_render_empty_state('activity', 'Входящие письма ещё не импортированы')}</td></tr>"

    content_html = (
        "".join(notices)
        + "<section class='panel' style='margin-bottom:18px;'>"
        "<div class='panel-header'>"
        f"{_render_sidebar_icon('settings')}"
        "<h2 class='panel-title'>Настройки отправки</h2>"
        "</div>"
        "<form method='post' action='/admin/settings/delivery-delay' class='section-stack'>"
        "<div class='form-grid-2'>"
        "<div>"
        "<label class='field-label'>Задержка отправки ссылки, мин.</label>"
        f"<input class='text-input' type='number' min='1' max='10080' name='delivery_delay_minutes' value='{delivery_delay_minutes}' required>"
        f"<div class='meta-note' style='margin-top:6px;'>Значение по умолчанию из env: {default_delivery_delay_minutes} мин.</div>"
        "</div>"
        "<div class='summary-card'>"
        "<strong>Бумажные заявки</strong>"
        "<p>Подтверждение получения отправляется сразу. Решение комиссии и способ получения направляются в течение 5 рабочих дней.</p>"
        "</div>"
        "</div>"
        "<div class='inline-actions'>"
        "<button type='submit' class='primary-button'>Сохранить настройки</button>"
        "<span class='meta-note'>Новое значение применяется ко всем новым электронным и смешанным заявкам.</span>"
        "</div>"
        "</form></section>"
        "<section class='panel' style='margin-bottom:18px;'>"
        "<div class='panel-header'>"
        f"{_render_sidebar_icon('activity')}"
        "<h2 class='panel-title'>Почтовый провайдер и автоматизация</h2>"
        "</div>"
        "<form method='post' action='/admin/settings/mail' class='mail-settings-form'>"
        "<div class='mail-provider-grid'>"
        "<div><label class='field-label'>Провайдер</label>"
        f"<select class='select-input' name='provider_key'>{provider_options_html}</select>"
        "<div class='meta-note' style='margin-top:6px;'>"
        "Для Gmail, Yandex и Mail.ru SMTP/IMAP host/port/security будут взяты из preset. Для нестандартной конфигурации выбери Custom."
        "</div></div>"
        "<div><label class='field-label'>От кого отправлять</label>"
        f"<input class='text-input' name='smtp_from_email' value='{escape(str(mail_settings['smtp_from_email']))}' placeholder='noreply@example.com'>"
        "</div></div>"
        "<div class='mail-protocol-title'>SMTP</div>"
        "<div class='mail-grid-3'>"
        "<div><label class='field-label'>Логин</label>"
        f"<input class='text-input' name='smtp_username' value='{escape(str(mail_settings['smtp_username']))}'></div>"
        "<div><label class='field-label'>Пароль</label>"
        "<input class='text-input' type='password' name='smtp_password' placeholder='Оставь пустым, чтобы не менять'></div>"
        "<div><label class='field-label'>Хост</label>"
        f"<input class='text-input' name='smtp_host' value='{escape(str(mail_settings['smtp_host']))}'></div>"
        "</div>"
        "<div class='mail-grid-2'>"
        "<div><label class='field-label'>Порт</label>"
        f"<input class='text-input' type='number' name='smtp_port' value='{escape(str(mail_settings['smtp_port']))}'></div>"
        "<div><label class='field-label'>Безопасность</label>"
        "<select class='select-input' name='smtp_security'>"
        f"<option value='none'{' selected' if str(mail_settings['smtp_security']) == 'none' else ''}>none</option>"
        f"<option value='starttls'{' selected' if str(mail_settings['smtp_security']) == 'starttls' else ''}>starttls</option>"
        f"<option value='ssl'{' selected' if str(mail_settings['smtp_security']) == 'ssl' else ''}>ssl</option>"
        "</select></div>"
        "</div>"
        "<div class='mail-divider'></div>"
        "<div class='mail-protocol-title'>IMAP</div>"
        "<div class='mail-grid-3'>"
        "<div><label class='field-label'>Логин</label>"
        f"<input class='text-input' name='imap_username' value='{escape(str(mail_settings['imap_username']))}' placeholder='Не задан'></div>"
        "<div><label class='field-label'>Пароль</label>"
        "<input class='text-input' type='password' name='imap_password' placeholder='Оставь пустым, чтобы не менять'></div>"
        "<div><label class='field-label'>Хост</label>"
        f"<input class='text-input' name='imap_host' value='{escape(str(mail_settings['imap_host']))}'></div>"
        "</div>"
        "<div class='mail-grid-2'>"
        "<div><label class='field-label'>Порт</label>"
        f"<input class='text-input' type='number' name='imap_port' value='{escape(str(mail_settings['imap_port']))}'></div>"
        "<div><label class='field-label'>Безопасность</label>"
        "<select class='select-input' name='imap_security'>"
        f"<option value='none'{' selected' if str(mail_settings['imap_security']) == 'none' else ''}>none</option>"
        f"<option value='ssl'{' selected' if str(mail_settings['imap_security']) == 'ssl' else ''}>ssl</option>"
        f"<option value='starttls'{' selected' if str(mail_settings['imap_security']) == 'starttls' else ''}>starttls</option>"
        "</select></div>"
        "</div>"
        "<div class='mail-grid-2'>"
        "<div><label class='field-label'>Входящая папка</label>"
        f"<input class='text-input' name='imap_mailbox' value='{escape(str(mail_settings['imap_mailbox']))}'></div>"
        "<div></div>"
        "</div>"
        "<div class='mail-footer-grid'>"
        "<div class='mail-check-actions'>"
        "<div class='mail-checkboxes'>"
        f"<label class='checkbox-row compact'><input type='checkbox' name='outbound_mail_enabled' {'checked' if bool(mail_settings['outbound_mail_enabled']) else ''}> Автоотправка исходящих</label>"
        f"<label class='checkbox-row compact'><input type='checkbox' name='inbound_mail_enabled' {'checked' if bool(mail_settings['inbound_mail_enabled']) else ''}> Автоприём входящих</label>"
        "</div>"
        "<div class='mail-actions'>"
        "<button type='submit' class='primary-button'>Сохранить настройки</button>"
        "<button type='submit' class='secondary-button' formaction='/admin/settings/mail/sync' formmethod='post'>Проверить почту</button>"
        "</div>"
        "</div>"
        "<div class='summary-card'>"
        "<strong>Автоматическая обработка</strong>"
        "<p class='mail-note'>Очередь исходящих и импорт входящих обрабатываются фоновым циклом каждые несколько секунд.</p>"
        "</div>"
        "</div>"
        "</form>"
        "</section>"
        "<section class='panel' style='margin-bottom:18px;'>"
        "<div class='panel-header'>"
        f"{_render_sidebar_icon('requests')}"
        f"<h2 class='panel-title'>Последние входящие письма ({inbound_email_count})</h2>"
        "</div>"
        "<div class='table-wrap'><table><thead><tr>"
        "<th>Импорт</th><th>Отправитель</th><th>Тема</th><th>Папка</th>"
        "</tr></thead><tbody>"
        f"{inbound_rows_html}"
        "</tbody></table></div>"
        "</section>"
        "<section class='panel'>"
        "<div class='panel-header'>"
        f"{_render_sidebar_icon('panel')}"
        "<h2 class='panel-title'>Текущая логика уведомлений</h2>"
        "</div>"
        "<div class='summary-grid'>"
        "<div class='summary-card'><strong>Электронная заявка</strong><p>Сразу отправляется письмо-подтверждение получения заявки, затем по истечении установленной задержки отправляется письмо со ссылкой на скачивание книги.</p></div>"
        "<div class='summary-card'><strong>Бумажная заявка</strong><p>Сразу отправляется письмо-подтверждение получения заявки, затем комиссия принимает решение и направляет информацию о способе получения в течение 5 рабочих дней.</p></div>"
        "</div></section>"
    )
    return _render_admin_page(
        title="Настройки",
        subtitle="Параметры автоматической отправки и правила обработки заявок",
        admin_email=admin_email,
        active_nav="settings",
        content_html=content_html,
    )


def _render_request_detail_page(
    admin_email: str,
    request_row: Row,
    *,
    events: list[Row],
    error_message: str | None = None,
) -> str:
    detail_fields = [
        ("ID", request_row["id"]),
        ("Имя", request_row["first_name"]),
        ("Фамилия", request_row["last_name"]),
        ("Организация", request_row["organization"] or "—"),
        ("Должность", request_row["position"] or "—"),
        ("Email", request_row["email"]),
        ("Телефон", request_row["phone"] or "—"),
        ("Формат", request_row["format"]),
        ("Эл. статус", request_row["electronic_status"]),
        ("Статус бумаги", request_row["paper_status"]),
        ("Создана", request_row["created_at"]),
        ("Обновлена", request_row["updated_at"]),
    ]
    detail_cards_html = "".join(
        "<div class='detail-card'>"
        f"<div class='detail-label'>{escape(str(label))}</div>"
        f"<div class='detail-value'>{escape(str(value))}</div>"
        "</div>"
        for label, value in detail_fields
    )
    purpose_card_html = (
        "<div class='detail-card' style='grid-column:1 / -1;'>"
        "<div class='detail-label'>Цель использования</div>"
        f"<div class='detail-value'>{escape(str(request_row['purpose']))}</div>"
        "</div>"
    )
    paper_meta_card_html = (
        "<div class='detail-card' style='grid-column:1 / -1;'>"
        "<div class='detail-label'>Комментарий по бумажной версии</div>"
        f"<div class='detail-value'>Пункт выдачи: {escape(str(request_row['paper_pickup_info'] or '—'))}<br>"
        f"Примечание администратора: {escape(str(request_row['paper_admin_note'] or '—'))}</div>"
        "</div>"
    )
    error_html = (
        f"<div class='notice error'>{escape(error_message)}</div>"
        if error_message
        else ""
    )
    decision_form_html = ""
    if str(request_row["paper_status"]) == "review":
        decision_form_html = (
            "<section class='panel'>"
            "<div class='panel-header'>"
            f"{_render_sidebar_icon('panel')}"
            "<h2 class='panel-title'>Решение по бумажной заявке</h2>"
            "</div>"
            "<form method='post' action='/admin/requests/"
            f"{request_row['id']}"
            "/paper-decision' class='section-stack'>"
            "<div><label class='field-label'>Решение</label>"
            "<select class='select-input' name='decision'>"
            "<option value='approve'>Одобрить</option>"
            "<option value='reject'>Отклонить</option>"
            "</select></div>"
            "<div><label class='field-label'>Информация о выдаче</label>"
            "<textarea class='text-input' name='pickup_info' rows='4'></textarea></div>"
            "<div><label class='field-label'>Примечание администратора</label>"
            "<textarea class='text-input' name='admin_note' rows='4'></textarea></div>"
            "<div style='color:var(--muted);font-size:13px;'>"
            "Для одобрения укажи информацию о выдаче. Для отказа заполни примечание администратора."
            "</div>"
            "<div><button type='submit' class='primary-button'>Сохранить решение</button></div>"
            "</form></section>"
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
        events_html = f"<tr><td colspan='3'>{_render_empty_state('activity', 'События администратора ещё не зафиксированы')}</td></tr>"

    content_html = (
        "<a class='back-link' href='/admin/requests'>← Назад к заявкам</a>"
        f"{error_html}"
        "<div class='section-stack'>"
        "<section class='panel'>"
        "<div class='panel-header'>"
        f"{_render_sidebar_icon('requests')}"
        f"<h2 class='panel-title'>Заявка #{request_row['id']}</h2>"
        "</div>"
        "<div class='detail-grid'>"
        f"{detail_cards_html}{purpose_card_html}{paper_meta_card_html}"
        "</div></section>"
        f"{decision_form_html}"
        "<section class='panel'>"
        "<div class='panel-header'>"
        f"{_render_sidebar_icon('activity')}"
        "<h2 class='panel-title'>События администратора</h2>"
        "</div>"
        "<div class='table-wrap'><table><thead><tr><th>Создано</th><th>Событие</th><th>Metadata</th></tr></thead><tbody>"
        f"{events_html}"
        "</tbody></table></div>"
        "</section>"
        "</div>"
    )
    return _render_admin_page(
        title=f"Заявка #{request_row['id']}",
        subtitle="Детали заявки и действия администратора",
        admin_email=admin_email,
        active_nav="requests",
        content_html=content_html,
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    configure_logging(app_settings.app_env)
    logger = logging.getLogger("antology.api")

    async def run_mail_cycle() -> None:
        try:
            send_result = process_due_email_jobs(
                app_settings.database_path,
                app_settings,
            )
            sync_result = sync_incoming_emails(
                app_settings.database_path,
                app_settings,
            )
            logger.info(
                "mail_cycle_complete",
                extra={
                    "event": "mail_cycle_complete",
                    "outbox_processed": send_result.processed_count,
                    "outbox_sent": send_result.sent_count,
                    "outbox_failed": send_result.failed_count,
                    "inbox_processed": sync_result.processed_count,
                    "inbox_imported": sync_result.imported_count,
                    "inbox_duplicates": sync_result.duplicate_count,
                },
            )
        except Exception:
            logger.exception("mail_cycle_failed", extra={"event": "mail_cycle_failed"})

    async def mail_worker_loop(stop_event: asyncio.Event) -> None:
        while not stop_event.is_set():
            await run_mail_cycle()
            try:
                await asyncio.wait_for(
                    stop_event.wait(),
                    timeout=app_settings.worker_poll_interval_seconds,
                )
            except asyncio.TimeoutError:
                continue

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app_settings.book_storage_dir.mkdir(parents=True, exist_ok=True)
        init_database(app_settings.database_path)
        seed_admin_user(app_settings.database_path, app_settings)
        stop_event = asyncio.Event()
        worker_task: asyncio.Task[None] | None = None
        if app_settings.app_env != "test":
            worker_task = asyncio.create_task(mail_worker_loop(stop_event))
        logger.info(
            "app_started",
            extra={
                "event": "app_started",
                "app_env": app_settings.app_env,
                "database_path": str(app_settings.database_path),
                "book_storage_dir": str(app_settings.book_storage_dir),
                "api_docs_enabled": app_settings.expose_api_docs,
            },
        )
        try:
            yield
        finally:
            if worker_task is not None:
                stop_event.set()
                await worker_task

    app = FastAPI(
        title=app_settings.app_name,
        lifespan=lifespan,
        docs_url="/docs" if app_settings.expose_api_docs else None,
        redoc_url="/redoc" if app_settings.expose_api_docs else None,
        openapi_url="/openapi.json" if app_settings.expose_api_docs else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        started_at = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((perf_counter() - started_at) * 1000, 2)
            logger.exception(
                "request_failed",
                extra={
                    "event": "request_failed",
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
            )
            raise

        duration_ms = round((perf_counter() - started_at) * 1000, 2)
        logger.info(
            "request_complete",
            extra={
                "event": "request_complete",
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response

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
    async def request_access(request: Request, payload: RequestAccessPayload) -> RequestAccessResponse:
        effective_delay_minutes = get_effective_delivery_delay_minutes(
            app_settings.database_path,
            app_settings,
        )
        try:
            result = create_request_access(
                database_path=app_settings.database_path,
                settings=app_settings,
                payload={
                    **payload.model_dump(),
                    "request_ip": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                },
            )
        except RateLimitExceededError as error:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
            ) from error

        return RequestAccessResponse(
            status="accepted",
            request_id=result.request_id,
            electronic_status=cast(Literal["none", "pending", "sent", "failed"], result.electronic_status),
            paper_status=cast(Literal["none", "review", "approved", "rejected"], result.paper_status),
            email_job_id=result.email_job_id,
            delivery_scheduled_for=result.send_after,
            confirmation_message=build_request_confirmation_message(
                str(payload.format),
                delay_minutes=effective_delay_minutes,
            ),
            electronic_delivery_delay_minutes=(
                effective_delay_minutes if str(payload.format) in {"electronic", "both"} else None
            ),
        )

    @app.post(f"{app_settings.api_prefix}/site-visit", status_code=202)
    async def record_site_visit(request: Request, payload: SiteVisitPayload) -> dict[str, str]:
        create_site_visit(
            app_settings.database_path,
            session_id=payload.session_id,
            path=payload.path,
            referrer=payload.referrer,
            request_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        return {"status": "accepted"}

    @app.get(ADMIN_LOGIN_PATH, response_class=HTMLResponse)
    async def admin_login_page() -> HTMLResponse:
        return HTMLResponse(_render_login_page())

    @app.get("/admin/login")
    async def admin_login_legacy_redirect() -> RedirectResponse:
        return RedirectResponse(url=ADMIN_LOGIN_PATH, status_code=307)

    @app.post(ADMIN_LOGIN_PATH)
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

    @app.post("/admin/login")
    async def admin_login_legacy_post(request: Request):
        return await admin_login(request)

    @app.post("/admin/logout")
    async def admin_logout() -> RedirectResponse:
        response = RedirectResponse(url=ADMIN_LOGIN_PATH, status_code=303)
        response.delete_cookie(SESSION_COOKIE_NAME)
        return response

    @app.get("/admin", response_class=HTMLResponse)
    async def admin_dashboard(request: Request) -> HTMLResponse:
        admin_user = require_admin_user(request, app_settings.database_path, app_settings)
        context = build_dashboard_context(app_settings.database_path, app_settings)
        return HTMLResponse(_render_dashboard_page(str(admin_user["email"]), context))

    @app.get("/admin/books", response_class=HTMLResponse)
    async def admin_books_page(request: Request, page: int = 1) -> HTMLResponse:
        admin_user = require_admin_user(request, app_settings.database_path, app_settings)
        context = build_books_page_context(
            app_settings.database_path,
            page=page,
        )
        return HTMLResponse(_render_books_page(str(admin_user["email"]), context))

    @app.get("/admin/requests", response_class=HTMLResponse)
    async def admin_requests_page(
        request: Request,
        format: str | None = None,
        electronic_status: str | None = None,
        paper_status: str | None = None,
        page: int = 1,
    ) -> HTMLResponse:
        admin_user = require_admin_user(request, app_settings.database_path, app_settings)
        context = build_requests_page_context(
            app_settings.database_path,
            request_format=format,
            electronic_status=electronic_status,
            paper_status=paper_status,
            page=page,
        )
        return HTMLResponse(_render_requests_page(str(admin_user["email"]), context))

    @app.get("/admin/settings", response_class=HTMLResponse)
    async def admin_settings_page(request: Request) -> HTMLResponse:
        admin_user = require_admin_user(request, app_settings.database_path, app_settings)
        context = build_settings_page_context(app_settings.database_path, app_settings)
        return HTMLResponse(_render_settings_page(str(admin_user["email"]), context))

    @app.post("/admin/books/upload")
    async def admin_upload_book(
        request: Request,
        title: str = Form(...),
        version_label: str = Form(...),
        make_active: str | None = Form(default=None),
        book_file: UploadFile = File(...),
    ):
        admin_user = require_admin_user(request, app_settings.database_path, app_settings)
        try:
            await store_uploaded_book(
                app_settings,
                database_path=app_settings.database_path,
                admin_user_id=int(admin_user["id"]),
                upload_file=book_file,
                title=title,
                version_label=version_label,
                make_active=make_active is not None,
            )
        except ValueError as error:
            context = build_books_page_context(
                app_settings.database_path,
                page=1,
            )
            return HTMLResponse(
                _render_books_page(str(admin_user["email"]), context, error_message=str(error)),
                status_code=400,
            )
        finally:
            await book_file.close()

        return RedirectResponse(url="/admin/books", status_code=303)

    @app.post("/admin/books/{book_version_id}/activate")
    async def admin_activate_book(request: Request, book_version_id: int):
        admin_user = require_admin_user(request, app_settings.database_path, app_settings)
        try:
            switch_active_book_version(
                app_settings.database_path,
                admin_user_id=int(admin_user["id"]),
                book_version_id=book_version_id,
            )
        except LookupError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

        return RedirectResponse(url="/admin/books", status_code=303)

    @app.post("/admin/settings/delivery-delay")
    async def admin_update_delivery_delay(request: Request):
        admin_user = require_admin_user(request, app_settings.database_path, app_settings)
        form_data = parse_qs((await request.body()).decode("utf-8"))
        raw_value = str(form_data.get("delivery_delay_minutes", [""])[0]).strip()

        try:
            delivery_delay_minutes = int(raw_value)
        except ValueError:
            context = build_settings_page_context(app_settings.database_path, app_settings)
            return HTMLResponse(
                _render_settings_page(
                    str(admin_user["email"]),
                    context,
                    error_message="Укажи целое число минут.",
                ),
                status_code=400,
            )

        if not 1 <= delivery_delay_minutes <= 10080:
            context = build_settings_page_context(app_settings.database_path, app_settings)
            return HTMLResponse(
                _render_settings_page(
                    str(admin_user["email"]),
                    context,
                    error_message="Допустимый диапазон: от 1 до 10080 минут.",
                ),
                status_code=400,
            )

        updated_at = datetime.now(timezone.utc).isoformat()
        set_system_setting(
            app_settings.database_path,
            key="electronic_delivery_delay_minutes",
            value=str(delivery_delay_minutes),
            updated_at=updated_at,
        )
        create_admin_event(
            app_settings.database_path,
            admin_user_id=int(admin_user["id"]),
            event_type="delivery_delay_updated",
            entity_type="system",
            entity_id=0,
            metadata={"delivery_delay_minutes": delivery_delay_minutes},
            created_at=updated_at,
        )

        context = build_settings_page_context(app_settings.database_path, app_settings)
        return HTMLResponse(
            _render_settings_page(
                str(admin_user["email"]),
                context,
                success_message="Новая задержка отправки ссылки сохранена.",
            )
        )

    @app.post("/admin/settings/mail")
    async def admin_update_mail_settings(request: Request):
        admin_user = require_admin_user(request, app_settings.database_path, app_settings)
        form_data = parse_qs((await request.body()).decode("utf-8"))
        payload = {
            key: str(values[0])
            for key, values in form_data.items()
            if values
        }
        updated_at = datetime.now(timezone.utc).isoformat()
        try:
            next_settings = persist_mail_settings(
                app_settings.database_path,
                app_settings,
                payload,
                updated_at=updated_at,
            )
        except ValueError as error:
            context = build_settings_page_context(app_settings.database_path, app_settings)
            return HTMLResponse(
                _render_settings_page(
                    str(admin_user["email"]),
                    context,
                    error_message=str(error),
                ),
                status_code=400,
            )

        create_admin_event(
            app_settings.database_path,
            admin_user_id=int(admin_user["id"]),
            event_type="mail_settings_updated",
            entity_type="system",
            entity_id=1,
            metadata={
                "provider_key": next_settings.provider_key,
                "smtp_host": next_settings.smtp_host,
                "smtp_port": next_settings.smtp_port,
                "imap_host": next_settings.imap_host,
                "imap_port": next_settings.imap_port,
                "outbound_mail_enabled": next_settings.outbound_mail_enabled,
                "inbound_mail_enabled": next_settings.inbound_mail_enabled,
            },
            created_at=updated_at,
        )
        context = build_settings_page_context(app_settings.database_path, app_settings)
        return HTMLResponse(
            _render_settings_page(
                str(admin_user["email"]),
                context,
                success_message="Почтовые настройки сохранены.",
            )
        )

    @app.post("/admin/settings/mail/sync")
    async def admin_sync_mail_now(request: Request):
        admin_user = require_admin_user(request, app_settings.database_path, app_settings)
        try:
            send_result = process_due_email_jobs(
                app_settings.database_path,
                app_settings,
            )
            sync_result = sync_incoming_emails(
                app_settings.database_path,
                app_settings,
            )
            success_message = (
                "Почтовый цикл выполнен: "
                f"исходящих отправлено {send_result.sent_count}, "
                f"входящих импортировано {sync_result.imported_count}."
            )
            context = build_settings_page_context(app_settings.database_path, app_settings)
            return HTMLResponse(
                _render_settings_page(
                    str(admin_user["email"]),
                    context,
                    success_message=success_message,
                )
            )
        except Exception as error:
            context = build_settings_page_context(app_settings.database_path, app_settings)
            return HTMLResponse(
                _render_settings_page(
                    str(admin_user["email"]),
                    context,
                    error_message=f"Не удалось выполнить почтовый цикл: {error}",
                ),
                status_code=500,
            )

    @app.get("/admin/requests/{request_id}", response_class=HTMLResponse)
    async def admin_request_detail(request: Request, request_id: int) -> HTMLResponse:
        admin_user = require_admin_user(request, app_settings.database_path, app_settings)
        request_row = get_request(app_settings.database_path, request_id)
        if request_row is None:
            raise HTTPException(status_code=404, detail="Request was not found")

        events = list_admin_events(
            app_settings.database_path,
            entity_type="request",
            entity_id=request_id,
        )
        return HTMLResponse(
            _render_request_detail_page(
                str(admin_user["email"]),
                request_row,
                events=events,
            )
        )

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
            admin_identity = require_admin_user(request, app_settings.database_path, app_settings)
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
                    str(admin_identity["email"]),
                    request_row,
                    events=events,
                    error_message=str(error),
                ),
                status_code=400,
            )

        return RedirectResponse(url=f"/admin/requests/{request_id}", status_code=303)

    return app


app = create_app()
