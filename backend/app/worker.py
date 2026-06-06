from __future__ import annotations

import argparse
import time

from .config import get_settings
from .db import init_database
from .worker_service import process_due_email_jobs


def main() -> None:
    parser = argparse.ArgumentParser(description="Process due Antology email jobs.")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process currently due jobs once and exit.",
    )
    args = parser.parse_args()

    settings = get_settings()
    init_database(settings.database_path)

    if args.once:
        process_due_email_jobs(settings.database_path, settings)
        return

    while True:
        process_due_email_jobs(settings.database_path, settings)
        time.sleep(settings.worker_poll_interval_seconds)


if __name__ == "__main__":
    main()
