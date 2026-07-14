from datetime import date, datetime, time, timedelta, timezone
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.database_models import PipelineRun, Record
from app.schemas import RecordOut


PHOENIX_TIMEZONE = ZoneInfo("America/Phoenix")
DEFAULT_RECORDS_LIMIT = 100
MAX_RECORDS_LIMIT = 500

app = FastAPI()


def phoenix_day_start_utc(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=PHOENIX_TIMEZONE).astimezone(
        timezone.utc
    )


@app.get("/pipeline/status")
def pipeline_status(db: Session = Depends(get_db)):
    stmt = (
        select(PipelineRun)
        .order_by(PipelineRun.started_at.desc())
        .limit(1)
    )
    latest_run = db.scalar(stmt)

    if latest_run is None:
        return {"message": "No pipeline runs yet."}

    return {
        "started_at": latest_run.started_at,
        "finished_at": latest_run.finished_at,
        "records_ingested": latest_run.records_ingested,
        "status": latest_run.status,
        "error": latest_run.error,
    }


@app.get("/records", response_model=list[RecordOut])
def list_records(
    response: Response,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: Annotated[int, Query(ge=1, le=MAX_RECORDS_LIMIT)] = (
        DEFAULT_RECORDS_LIMIT
    ),
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Session = Depends(get_db),
):
    stmt = select(Record)

    if start_date is not None:
        stmt = stmt.where(Record.occurred_at >= phoenix_day_start_utc(start_date))

    if end_date is not None:
        end_exclusive = phoenix_day_start_utc(end_date + timedelta(days=1))
        stmt = stmt.where(Record.occurred_at < end_exclusive)

    stmt = stmt.order_by(Record.id)
    records = list(db.scalars(stmt.limit(limit).offset(offset)).all())

    next_record_stmt = (
        stmt.with_only_columns(Record.id)
        .limit(1)
        .offset(offset + len(records))
    )
    has_more = db.scalar(next_record_stmt) is not None
    response.headers["X-Has-More"] = str(has_more).lower()

    return records
