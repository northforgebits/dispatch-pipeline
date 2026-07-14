from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import get_db
from app.database_models import PipelineRun, Record
from app.main import app


@pytest.fixture
def records_client(clean_records_table):
    occurred_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    clean_records_table.add_all(
        [
            Record(
                natural_key=f"page-{index:03}",
                occurred_at=occurred_at + timedelta(minutes=index),
                raw_fields={},
                disp_code="N",
                disposition="No action needed",
                final_radio_code="N",
                final_call_type="TEST",
                hundred_block_addr=f"{index} TEST ST",
                grid=None,
            )
            for index in range(105)
        ]
    )
    clean_records_table.commit()

    bind = clean_records_table.get_bind()

    def override_get_db():
        with Session(bind) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def pipeline_status_client(clean_records_table):
    bind = clean_records_table.get_bind()

    def override_get_db():
        with Session(bind) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client, clean_records_table
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_pipeline_status_returns_200_when_no_runs_exist(
    pipeline_status_client,
):
    client, _ = pipeline_status_client

    response = client.get("/pipeline/status")

    assert response.status_code == 200
    assert response.json() == {"message": "No pipeline runs yet."}


def test_pipeline_status_returns_most_recent_run(pipeline_status_client):
    client, db = pipeline_status_client
    older_started_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    latest_started_at = datetime(2026, 1, 2, tzinfo=timezone.utc)
    latest_finished_at = latest_started_at + timedelta(minutes=5)
    db.add_all(
        [
            PipelineRun(
                id="00000000-0000-4000-8000-000000000002",
                started_at=latest_started_at,
                finished_at=latest_finished_at,
                records_ingested=42,
                status="success",
            ),
            PipelineRun(
                id="00000000-0000-4000-8000-000000000001",
                started_at=older_started_at,
                finished_at=older_started_at + timedelta(minutes=1),
                records_ingested=None,
                status="failed",
                error="older failure",
            ),
        ]
    )
    db.commit()

    response = client.get("/pipeline/status")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "started_at",
        "finished_at",
        "records_ingested",
        "status",
        "error",
    }
    assert datetime.fromisoformat(body["started_at"]) == latest_started_at
    assert datetime.fromisoformat(body["finished_at"]) == latest_finished_at
    assert body["records_ingested"] == 42
    assert body["status"] == "success"
    assert body["error"] is None


def test_pipeline_status_is_registered_in_docs(pipeline_status_client):
    client, _ = pipeline_status_client

    assert client.get("/docs").status_code == 200
    openapi = client.get("/openapi.json").json()
    assert "/pipeline/status" in openapi["paths"]


def test_records_default_limit_is_bounded(records_client):
    response = records_client.get("/records")

    assert response.status_code == 200
    assert len(response.json()) == 100
    assert response.headers["x-has-more"] == "true"


def test_records_rejects_limit_over_ceiling(records_client):
    response = records_client.get("/records?limit=501")

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "limit"]


def test_records_returns_non_overlapping_pages_and_has_more(records_client):
    first = records_client.get("/records?limit=10&offset=0")
    second = records_client.get("/records?limit=10&offset=10")
    final = records_client.get("/records?limit=10&offset=100")

    assert first.status_code == second.status_code == final.status_code == 200

    first_keys = {record["natural_key"] for record in first.json()}
    second_keys = {record["natural_key"] for record in second.json()}
    assert len(first_keys) == len(second_keys) == 10
    assert first_keys.isdisjoint(second_keys)

    assert first.headers["x-has-more"] == "true"
    assert second.headers["x-has-more"] == "true"
    assert len(final.json()) == 5
    assert final.headers["x-has-more"] == "false"
