from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from secrets import token_hex

from fastapi import UploadFile

from .config import Settings
from .repository import (
    activate_book_version,
    create_admin_event,
    create_book_version,
    get_book_version,
    list_book_versions,
)


@dataclass(frozen=True)
class BookUploadResult:
    book_version_id: int
    file_name: str
    file_size: int
    checksum: str


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _sanitize_label(value: str, default: str) -> str:
    collapsed = "-".join(part for part in value.strip().lower().replace("_", "-").split() if part)
    return collapsed or default


async def store_uploaded_book(
    settings: Settings,
    *,
    database_path: Path,
    admin_user_id: int,
    upload_file: UploadFile,
    title: str,
    version_label: str,
    make_active: bool,
) -> BookUploadResult:
    if upload_file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise ValueError("Only PDF uploads are allowed")

    raw_bytes = await upload_file.read()
    if not raw_bytes:
        raise ValueError("Uploaded file is empty")

    max_size_bytes = settings.max_book_upload_mb * 1024 * 1024
    if len(raw_bytes) > max_size_bytes:
        raise ValueError(f"Uploaded file exceeds the {settings.max_book_upload_mb} MB limit")

    original_name = upload_file.filename or "book.pdf"
    if not original_name.lower().endswith(".pdf"):
        raise ValueError("Uploaded file must have a .pdf extension")

    safe_version = _sanitize_label(version_label, "book")
    file_token = token_hex(8)
    stored_file_name = f"{safe_version}-{file_token}.pdf"
    storage_root = settings.book_storage_dir.resolve()
    storage_root.mkdir(parents=True, exist_ok=True)
    target_path = storage_root / stored_file_name
    target_path.write_bytes(raw_bytes)

    checksum = sha256(raw_bytes).hexdigest()
    uploaded_at = _utc_now().isoformat()
    book_version_id = create_book_version(
        database_path,
        title=title.strip() or "Anthology",
        version_label=version_label.strip() or "unlabeled",
        file_path=stored_file_name,
        file_name=original_name,
        file_size=len(raw_bytes),
        checksum=checksum,
        is_active=make_active,
        uploaded_at=uploaded_at,
    )
    create_admin_event(
        database_path,
        admin_user_id=admin_user_id,
        event_type="book_uploaded",
        entity_type="book_version",
        entity_id=book_version_id,
        metadata={
            "title": title.strip() or "Anthology",
            "version_label": version_label.strip() or "unlabeled",
            "file_name": original_name,
            "stored_file_name": stored_file_name,
            "file_size": len(raw_bytes),
            "checksum": checksum,
            "is_active": make_active,
        },
        created_at=uploaded_at,
    )

    return BookUploadResult(
        book_version_id=book_version_id,
        file_name=original_name,
        file_size=len(raw_bytes),
        checksum=checksum,
    )


def switch_active_book_version(
    database_path: Path,
    *,
    admin_user_id: int,
    book_version_id: int,
) -> None:
    activate_book_version(database_path, book_version_id=book_version_id)
    book_version = get_book_version(database_path, book_version_id)
    if book_version is None:
        raise LookupError("Book version was not found")

    create_admin_event(
        database_path,
        admin_user_id=admin_user_id,
        event_type="book_activated",
        entity_type="book_version",
        entity_id=book_version_id,
        metadata={
            "title": str(book_version["title"]),
            "version_label": str(book_version["version_label"]),
        },
        created_at=_utc_now().isoformat(),
    )


def build_book_versions_context(database_path: Path) -> dict[str, object]:
    versions = list_book_versions(database_path)
    active_version = next((row for row in versions if int(row["is_active"]) == 1), None)
    return {
        "versions": versions,
        "active_version": active_version,
    }
