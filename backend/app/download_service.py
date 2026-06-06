from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from secrets import token_urlsafe

from .config import Settings
from .repository import (
    DownloadTokenResult,
    create_download_token,
    get_active_book_version,
    mark_download_token_used,
    resolve_download_token,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _isoformat(value: datetime) -> str:
    return value.isoformat()


def issue_download_token(
    database_path: Path,
    settings: Settings,
    *,
    request_id: int,
) -> DownloadTokenResult:
    active_book = get_active_book_version(database_path)
    if active_book is None:
        raise LookupError("No active book version configured")

    now = _utc_now()
    expires_at = now + timedelta(hours=settings.download_token_ttl_hours)
    raw_token = token_urlsafe(32)

    return create_download_token(
        database_path,
        request_id=request_id,
        book_version_id=int(active_book["id"]),
        raw_token=raw_token,
        expires_at=_isoformat(expires_at),
        created_at=_isoformat(now),
    )


def resolve_download(
    database_path: Path,
    settings: Settings,
    *,
    raw_token: str,
) -> tuple[Path, str]:
    row = resolve_download_token(database_path, raw_token)
    if row is None:
        raise LookupError("Download token not found")

    expires_at = datetime.fromisoformat(str(row["expires_at"]))
    if expires_at <= _utc_now():
        raise TimeoutError("Download token expired")

    storage_root = settings.book_storage_dir.resolve()
    file_path = (storage_root / str(row["file_path"])).resolve()

    if not str(file_path).startswith(str(storage_root)):
        raise ValueError("Resolved book path escapes storage root")

    if not file_path.exists():
        raise FileNotFoundError("Book file is missing from storage")

    mark_download_token_used(database_path, int(row["id"]), _isoformat(_utc_now()))
    return file_path, str(row["file_name"])
