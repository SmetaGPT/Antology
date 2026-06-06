from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import zipfile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a restorable Antology runtime backup archive.")
    parser.add_argument("--database", required=True, help="Path to the SQLite database file.")
    parser.add_argument("--books", required=True, help="Path to the runtime books directory.")
    parser.add_argument("--output", required=True, help="Directory where backup archives will be stored.")
    return parser.parse_args()


def build_backup(database_path: Path, books_path: Path, output_dir: Path) -> Path:
    if not database_path.exists():
        raise FileNotFoundError(f"Database file was not found: {database_path}")
    if not books_path.exists():
        raise FileNotFoundError(f"Books directory was not found: {books_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_path = output_dir / f"antology-runtime-backup-{timestamp}.zip"

    manifest = {
        "created_at": timestamp,
        "database": database_path.name,
        "books": sorted(path.name for path in books_path.iterdir() if path.is_file()),
    }

    with zipfile.ZipFile(archive_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(database_path, arcname=f"database/{database_path.name}")
        for file_path in sorted(books_path.rglob("*")):
            if file_path.is_file():
                relative_path = file_path.relative_to(books_path)
                archive.write(file_path, arcname=f"books/{relative_path.as_posix()}")
        archive.writestr("manifest.json", json.dumps(manifest, indent=2))

    return archive_path


def main() -> None:
    args = parse_args()
    archive_path = build_backup(
        database_path=Path(args.database),
        books_path=Path(args.books),
        output_dir=Path(args.output),
    )
    print(f"Backup created: {archive_path}")


if __name__ == "__main__":
    main()
