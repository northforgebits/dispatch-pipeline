from datetime import datetime, timezone
import time
import uuid

import structlog
from pydantic import ValidationError

from app.database import SessionLocal, upsert_records
from app.database_models import PipelineRun
from app.logging_config import configure_logging
from app.models import CallForService
from app.phoenix_data_client import fetch_phx_data_records
from app.transform import to_record_row


def main():
    configure_logging()

    run_id = str(uuid.uuid4())
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(run_id=run_id)

    logger = structlog.get_logger()
    start_time = time.monotonic()

    with SessionLocal() as session:
        session.add(
            PipelineRun(
                id=run_id,
                started_at=datetime.now(timezone.utc),
                status="running",
            )
        )
        session.commit()

    logger.info("ingestion_run_started", status="started")

    try:
        raw_records = fetch_phx_data_records()

        validated_records = []
        valid_counter = 0
        bad_counter = 0

        for raw_record in raw_records:
            try:
                validated = CallForService.model_validate(raw_record)
                validated_records.append(validated)
                valid_counter += 1
            except ValidationError:
                bad_counter += 1

        rows = []
        transform_failed_counter = 0

        for validated in validated_records:
            try:
                rows.append(to_record_row(validated))
            except (TypeError, ValueError):
                transform_failed_counter += 1

        upserted = upsert_records(rows)

        with SessionLocal() as session:
            pipeline_run = session.get(PipelineRun, run_id)
            if pipeline_run is None:
                raise RuntimeError(f"Pipeline run {run_id} was not found")

            pipeline_run.finished_at = datetime.now(timezone.utc)
            pipeline_run.records_ingested = upserted
            pipeline_run.status = "success"
            session.commit()

        logger.info(
            "ingestion_run_completed",
            pulled=len(raw_records),
            validated=valid_counter,
            failed=bad_counter + transform_failed_counter,
            transform_failed=transform_failed_counter,
            upserted=upserted,
            duration_seconds=time.monotonic() - start_time,
            status="success",
        )
    except Exception as error:
        error_to_log = getattr(error, "orig", error)

        with SessionLocal() as session:
            pipeline_run = session.get(PipelineRun, run_id)
            if pipeline_run is None:
                raise RuntimeError(f"Pipeline run {run_id} was not found")

            pipeline_run.finished_at = datetime.now(timezone.utc)
            pipeline_run.status = "failed"
            pipeline_run.error = str(error_to_log)
            session.commit()

        logger.error(
            "ingestion_run_failed",
            status="failed",
            error=str(error_to_log),
            duration_seconds=time.monotonic() - start_time,
        )
        raise


if __name__ == "__main__":
    main()
