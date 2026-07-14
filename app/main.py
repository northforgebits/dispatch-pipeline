from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.database_models import Record
from app.schemas import RecordOut


PHOENIX_TIMEZONE = ZoneInfo("America/Phoenix")

app = FastAPI()


def phoenix_day_start_utc(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=PHOENIX_TIMEZONE).astimezone(
        timezone.utc
    )


@app.get("/records", response_model=list[RecordOut])
def list_records(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(Record)

    if start_date is not None:
        stmt = stmt.where(Record.occurred_at >= phoenix_day_start_utc(start_date))

    if end_date is not None:
        end_exclusive = phoenix_day_start_utc(end_date + timedelta(days=1))
        stmt = stmt.where(Record.occurred_at < end_exclusive)

    return list(db.scalars(stmt).all())
