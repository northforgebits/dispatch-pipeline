import time
import uuid

import structlog
from pydantic import ValidationError

from app.logging_config import configure_logging
from app.models import CallForService
from app.phoenix_data_client import fetch_phx_data_records


def main():
    configure_logging()

    run_id = str(uuid.uuid4())
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(run_id=run_id)

    logger = structlog.get_logger()
    logger.info("run_started", status="started")
    start_time = time.monotonic()

    try:
        raw_records = fetch_phx_data_records()

        valid_counter = 0
        bad_counter = 0

        for raw_record in raw_records:
            try:
                CallForService.model_validate(raw_record)
                valid_counter += 1
            except ValidationError:
                bad_counter += 1

        logger.info(
            "run_completed",
            pulled=len(raw_records),
            validated=valid_counter,
            failed=bad_counter,
            duration_seconds=time.monotonic() - start_time,
            status="completed",
        )
    except Exception as error:
        logger.error(
            "run_failed",
            status="failed",
            error=str(error),
            duration_seconds=time.monotonic() - start_time,
        )
        raise


if __name__ == "__main__":
    main()
