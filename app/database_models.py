from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Record(Base):
    __tablename__ = "records"
    __table_args__ = (
        UniqueConstraint("natural_key", name="uq_records_natural_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    natural_key: Mapped[str] = mapped_column(Text)
    occurred_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        index=True,
    )
    raw_fields: Mapped[dict[str, Any]] = mapped_column(JSONB)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    disp_code: Mapped[str] = mapped_column(Text)
    disposition: Mapped[str] = mapped_column(Text)
    final_radio_code: Mapped[str] = mapped_column(Text)
    final_call_type: Mapped[str] = mapped_column(Text)
    hundred_block_addr: Mapped[str] = mapped_column(Text)
    grid: Mapped[str | None] = mapped_column(Text)


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    records_ingested: Mapped[int | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
