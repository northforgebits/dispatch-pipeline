from datetime import datetime, timedelta, timezone
import time
import uuid

import structlog
from pydantic import ValidationError

from app.config import settings
from app.database import SessionLocal, upsert_records
from app.database_models import PipelineRun
from app.logging_config import configure_logging
from app.models import CallForService
from app.phoenix_data_client import iter_phx_data_pages
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
        pulled_counter = 0
        valid_counter = 0
        bad_counter = 0
        transform_failed_counter = 0
        skipped_stale_counter = 0
        upserted = 0

        cutoff = datetime.now(timezone.utc) - timedelta(
            days=settings.ingest_lookback_days
        )

        for page in iter_phx_data_pages():
            pulled_counter += len(page)
            rows = []

            for raw_record in page:
                try:
                    validated = CallForService.model_validate(raw_record)
                except ValidationError:
                    bad_counter += 1
                    continue

                valid_counter += 1

                try:
                    row = to_record_row(validated)
                except (TypeError, ValueError):
                    transform_failed_counter += 1
                    continue

                occurred_at = row.get("occurred_at")
                if occurred_at is not None and occurred_at < cutoff:
                    skipped_stale_counter += 1
                    continue

                rows.append(row)

            upserted += upsert_records(rows)

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
            pulled=pulled_counter,
            validated=valid_counter,
            failed=bad_counter + transform_failed_counter,
            transform_failed=transform_failed_counter,
            skipped_stale=skipped_stale_counter,
            upserted=upserted,
            duration_seconds=time.monotonic() - start_time,
            status="success",
        )
    except Exception as error:
        error_to_log = getattr(error, "orig", error)

        logger.error(
            "ingestion_run_failed",
            status="failed",
            error=str(error_to_log),
            duration_seconds=time.monotonic() - start_time,
        )

        try:
            with SessionLocal() as session:
                pipeline_run = session.get(PipelineRun, run_id)
                if pipeline_run is None:
                    raise RuntimeError(f"Pipeline run {run_id} was not found")

                pipeline_run.finished_at = datetime.now(timezone.utc)
                pipeline_run.status = "failed"
                pipeline_run.error = str(error_to_log)
                session.commit()
        except Exception as audit_error:
            audit_error_to_log = getattr(audit_error, "orig", audit_error)
            logger.error(
                "pipeline_run_failure_update_failed",
                error=str(audit_error_to_log),
                ingestion_error=str(error_to_log),
                duration_seconds=time.monotonic() - start_time,
            )

        raise


if __name__ == "__main__":
    main()