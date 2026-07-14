import pytest

from app import smoke
from app.database_models import PipelineRun


class FakeAuditSession:
    def __init__(self, runs, commits):
        self.runs = runs
        self.commits = commits
        self.pending_run = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def add(self, pipeline_run):
        self.pending_run = pipeline_run

    def get(self, model, run_id):
        assert model is PipelineRun
        return self.runs.get(run_id)

    def commit(self):
        if self.pending_run is not None:
            self.runs[self.pending_run.id] = self.pending_run

        pipeline_run = self.pending_run or next(iter(self.runs.values()))
        self.commits.append(
            {
                "status": pipeline_run.status,
                "finished_at": pipeline_run.finished_at,
                "records_ingested": pipeline_run.records_ingested,
                "error": pipeline_run.error,
            }
        )


def fake_session_local(runs, commits):
    return lambda: FakeAuditSession(runs, commits)


def test_completion_log_reports_upserted_without_skipped(monkeypatch):
    events = []
    runs = {}
    commits = []

    class FakeLogger:
        def info(self, event, **fields):
            events.append((event, fields))

        def error(self, event, **fields):
            raise AssertionError(f"unexpected error log: {event} {fields}")

    run_id = "success-run"
    raw_records = [{"id": 1}, {"id": 2}]

    def fetch_records():
        assert runs[run_id].status == "running"
        assert [commit["status"] for commit in commits] == ["running"]
        return raw_records

    monkeypatch.setattr(smoke, "configure_logging", lambda: None)
    monkeypatch.setattr(
        smoke.structlog.contextvars,
        "clear_contextvars",
        lambda: None,
    )
    monkeypatch.setattr(
        smoke.structlog.contextvars,
        "bind_contextvars",
        lambda **fields: None,
    )
    monkeypatch.setattr(smoke.structlog, "get_logger", FakeLogger)
    monkeypatch.setattr(smoke.uuid, "uuid4", lambda: run_id)
    monkeypatch.setattr(
        smoke,
        "SessionLocal",
        fake_session_local(runs, commits),
    )
    monkeypatch.setattr(smoke, "fetch_phx_data_records", fetch_records)
    monkeypatch.setattr(
        smoke.CallForService,
        "model_validate",
        lambda raw: raw,
    )
    monkeypatch.setattr(smoke, "to_record_row", lambda validated: validated)
    monkeypatch.setattr(smoke, "upsert_records", lambda rows: len(rows))

    smoke.main()

    completed = next(
        fields
        for event, fields in events
        if event == "ingestion_run_completed"
    )

    assert completed["pulled"] == 2
    assert completed["validated"] == 2
    assert completed["failed"] == 0
    assert completed["upserted"] == 2
    assert completed["status"] == "success"
    assert "inserted" not in completed
    assert "skipped" not in completed

    pipeline_run = runs[run_id]
    assert pipeline_run.finished_at is not None
    assert pipeline_run.records_ingested == 2
    assert pipeline_run.status == "success"
    assert pipeline_run.error is None
    assert [commit["status"] for commit in commits] == [
        "running",
        "success",
    ]


def test_failed_run_updates_separately_committed_start_row(monkeypatch):
    events = []
    runs = {}
    commits = []
    run_id = "failed-run"

    class FakeLogger:
        def info(self, event, **fields):
            events.append((event, fields))

        def error(self, event, **fields):
            events.append((event, fields))

    def fail_fetch():
        assert runs[run_id].status == "running"
        assert [commit["status"] for commit in commits] == ["running"]
        raise RuntimeError("Safety Cap Reached")

    monkeypatch.setattr(smoke, "configure_logging", lambda: None)
    monkeypatch.setattr(
        smoke.structlog.contextvars,
        "clear_contextvars",
        lambda: None,
    )
    monkeypatch.setattr(
        smoke.structlog.contextvars,
        "bind_contextvars",
        lambda **fields: None,
    )
    monkeypatch.setattr(smoke.structlog, "get_logger", FakeLogger)
    monkeypatch.setattr(smoke.uuid, "uuid4", lambda: run_id)
    monkeypatch.setattr(
        smoke,
        "SessionLocal",
        fake_session_local(runs, commits),
    )
    monkeypatch.setattr(smoke, "fetch_phx_data_records", fail_fetch)

    with pytest.raises(RuntimeError, match="Safety Cap Reached"):
        smoke.main()

    pipeline_run = runs[run_id]
    assert pipeline_run.finished_at is not None
    assert pipeline_run.records_ingested is None
    assert pipeline_run.status == "failed"
    assert pipeline_run.error == "Safety Cap Reached"
    assert [commit["status"] for commit in commits] == [
        "running",
        "failed",
    ]

    failed_log = next(
        fields for event, fields in events if event == "ingestion_run_failed"
    )
    assert failed_log["status"] == "failed"
    assert failed_log["error"] == "Safety Cap Reached"
