from sqlalchemy import create_engine, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def upsert_records(
    rows: list[dict],
    *,
    session: Session | None = None,
) -> int:
    from app.database_models import Record

    if not rows:
        return 0

    stmt = insert(Record).values(rows)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_records_natural_key",
        set_={
            "occurred_at": stmt.excluded.occurred_at,
            "raw_fields": stmt.excluded.raw_fields,
            "ingested_at": func.now(),
            "disp_code": stmt.excluded.disp_code,
            "disposition": stmt.excluded.disposition,
            "final_radio_code": stmt.excluded.final_radio_code,
            "final_call_type": stmt.excluded.final_call_type,
            "hundred_block_addr": stmt.excluded.hundred_block_addr,
            "grid": stmt.excluded.grid,
        },
    )

    if session is not None:
        result = session.execute(stmt)
        session.commit()
        return result.rowcount

    with SessionLocal() as owned_session:
        result = owned_session.execute(stmt)
        owned_session.commit()

    return result.rowcount
