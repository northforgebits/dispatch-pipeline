from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.database_models import PipelineRun, Record
from app.transform import phoenix_day_start_utc

router = APIRouter()

STATS_CACHE_HEADER = "public, max-age=300"


@router.get("/stats/summary")
def stats_summary(response: Response, db: Session = Depends(get_db)):
    total_records = db.scalar(select(func.count()).select_from(Record))

    runs_total = db.scalar(select(func.count()).select_from(PipelineRun))
    runs_succeeded = db.scalar(
        select(func.count())
        .select_from(PipelineRun)
        .where(PipelineRun.status == "success")
    )

    avg_run_seconds = db.scalar(
        select(
            func.avg(
                func.extract(
                    "epoch",
                    PipelineRun.finished_at - PipelineRun.started_at,
                )
            )
        ).where(
            PipelineRun.status == "success",
            PipelineRun.finished_at.is_not(None),
        )
    )

    # Anchors the UI's default date range to real data instead of the
    # wall clock , the source feed can lag "today" by more than a week,
    # and a wall-clock default would land new visitors on an empty page
    # until the pipeline catches up.
    latest_occurred_at = db.scalar(select(func.max(Record.occurred_at)))

    response.headers["Cache-Control"] = STATS_CACHE_HEADER
    return {
        "total_records": total_records,
        "runs_total": runs_total,
        "runs_succeeded": runs_succeeded,
        "avg_run_seconds": (
            float(avg_run_seconds) if avg_run_seconds is not None else None
        ),
        "latest_occurred_at": (
            latest_occurred_at.isoformat()
            if latest_occurred_at is not None
            else None
        ),
    }


@router.get("/stats/daily")
def stats_daily(
    response: Response,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    phoenix_day = func.date(
        func.timezone("America/Phoenix", Record.occurred_at)
    ).label("day")

    stmt = (
        select(phoenix_day, func.count().label("count"))
        .where(
            Record.occurred_at >= phoenix_day_start_utc(start_date),
            Record.occurred_at
            < phoenix_day_start_utc(end_date + timedelta(days=1)),
        )
        .group_by(phoenix_day)
        .order_by(phoenix_day)
    )

    response.headers["Cache-Control"] = STATS_CACHE_HEADER
    return [
        {"day": row.day.isoformat(), "count": row.count}
        for row in db.execute(stmt)
    ]


@router.get("/stats/call-types")
def stats_call_types(
    response: Response,
    limit: int = Query(default=6, ge=1, le=20),
    db: Session = Depends(get_db),
):
    stmt = (
        select(
            Record.final_call_type.label("call_type"),
            func.count().label("count"),
        )
        .group_by(Record.final_call_type)
        .order_by(func.count().desc())
        .limit(limit)
    )

    response.headers["Cache-Control"] = STATS_CACHE_HEADER
    return [
        {"call_type": row.call_type, "count": row.count}
        for row in db.execute(stmt)
    ]


@router.get("/pipeline/runs")
def pipeline_runs(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = (
        select(PipelineRun)
        .order_by(PipelineRun.started_at.desc())
        .limit(limit)
    )

    return [
        {
            "started_at": run.started_at,
            "finished_at": run.finished_at,
            "records_ingested": run.records_ingested,
            "status": run.status,
            "error": run.error,
        }
        for run in db.scalars(stmt)
    ]