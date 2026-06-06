from __future__ import annotations

import argparse
import logging
import time

from .config import get_settings
from .db import init_database
from .logging_utils import configure_logging
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
    configure_logging(settings.app_env)
    logger = logging.getLogger("antology.worker")
    init_database(settings.database_path)

    if args.once:
        result = process_due_email_jobs(settings.database_path, settings)
        logger.info(
            "worker_cycle_complete",
            extra={
                "event": "worker_cycle_complete",
                "mode": "once",
                "processed_count": result.processed_count,
                "sent_count": result.sent_count,
                "failed_count": result.failed_count,
            },
        )
        return

    while True:
        result = process_due_email_jobs(settings.database_path, settings)
        logger.info(
            "worker_cycle_complete",
            extra={
                "event": "worker_cycle_complete",
                "mode": "loop",
                "processed_count": result.processed_count,
                "sent_count": result.sent_count,
                "failed_count": result.failed_count,
            },
        )
        time.sleep(settings.worker_poll_interval_seconds)


if __name__ == "__main__":
    main()
