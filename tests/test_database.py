from types import SimpleNamespace

from sqlalchemy.dialects import postgresql

from app import database
from app.database_models import PipelineRun


def test_pipeline_run_model_matches_audit_schema():
    columns = PipelineRun.__table__.columns

    assert PipelineRun.__tablename__ == "pipeline_runs"
    assert columns.id.type.python_type is str
    assert columns.id.type.length == 36
    assert columns.id.primary_key is True
    assert columns.id.default is None
    assert columns.started_at.type.timezone is True
    assert columns.started_at.nullable is False
    assert columns.finished_at.type.timezone is True
    assert columns.finished_at.nullable is True
    assert columns.records_ingested.nullable is True
    assert columns.status.nullable is False
    assert columns.error.nullable is True


def test_upsert_records_uses_named_constraint_and_safe_update_columns():
    captured = {}

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, stmt):
            captured["stmt"] = stmt
            return SimpleNamespace(rowcount=1)

        def commit(self):
            captured["committed"] = True

    affected = database.upsert_records(
        [
            {
                "natural_key": "incident-1",
                "occurred_at": None,
                "raw_fields": {"incident_num": "incident-1"},
            }
        ],
        session=FakeSession(),
    )

    sql = str(
        captured["stmt"].compile(dialect=postgresql.dialect())
    )
    update_clause = sql.split("DO UPDATE SET ", maxsplit=1)[1]

    assert "ON CONFLICT ON CONSTRAINT uq_records_natural_key" in sql
    assert "occurred_at = excluded.occurred_at" in update_clause
    assert "raw_fields = excluded.raw_fields" in update_clause
    assert "ingested_at = now()" in update_clause
    assert "disp_code = excluded.disp_code" in update_clause
    assert "disposition = excluded.disposition" in update_clause
    assert "final_radio_code = excluded.final_radio_code" in update_clause
    assert "final_call_type = excluded.final_call_type" in update_clause
    assert "hundred_block_addr = excluded.hundred_block_addr" in update_clause
    assert "grid = excluded.grid" in update_clause
    assert "natural_key" not in update_clause
    assert captured["committed"] is True
    assert affected == 1


def test_upsert_records_returns_zero_for_an_empty_batch(monkeypatch):
    def fail_if_session_opens():
        raise AssertionError("empty batches should not open a database session")

    monkeypatch.setattr(database, "SessionLocal", fail_if_session_opens)

    assert database.upsert_records([]) == 0
