from app import smoke


def test_completion_log_reports_upserted_without_skipped(monkeypatch):
    events = []

    class FakeLogger:
        def info(self, event, **fields):
            events.append((event, fields))

        def error(self, event, **fields):
            raise AssertionError(f"unexpected error log: {event} {fields}")

    raw_records = [{"id": 1}, {"id": 2}]

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
    monkeypatch.setattr(smoke, "fetch_phx_data_records", lambda: raw_records)
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
