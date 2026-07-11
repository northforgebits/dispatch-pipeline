from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def write_records(rows: list[dict]) -> int:
    from app.database_models import Record

    with SessionLocal() as session:
        session.add_all([Record(**row) for row in rows])
        session.commit()

    return len(rows)
