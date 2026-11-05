from datetime import datetime, timedelta, timezone

import pytest

from app import phoenix_data_client


def test_fetch_raises_when_max_pages_reached_before_total(monkeypatch):
    requests = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "success": True,
                "result": {
                    "records": [{"INCIDENT_NUM": "one"}],
                    "total": 2,
                },
            }

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def get(self, url, params):
            requests.append((url, params))
            return FakeResponse()

    monkeypatch.setattr(phoenix_data_client.settings, "max_pages", 1)
    monkeypatch.setattr(phoenix_data_client.httpx, "Client", FakeClient)
    monkeypatch.setattr(phoenix_data_client.time, "sleep", lambda seconds: None)

    with pytest.raises(RuntimeError, match="^Safety Cap Reached$"):
        list(phoenix_data_client.iter_phx_data_pages())

    assert len(requests) == 1


CALL_RECEIVED_FORMAT: str = "%m/%d/%Y %I:%M:%S %p"


def make_fake_client(
    all_rows: list[dict],
    requests: list[dict],
):
    """Fake CKAN client over all_rows, which are stored oldest first.

    It only returns newest first when the request says sort=_id desc,
    like the real datastore_search does.
    """

    class FakeResponse:
        def __init__(self, records: list[dict]) -> None:
            self.records = records

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "success": True,
                "result": {"records": self.records, "total": len(all_rows)},
            }

    class FakeClient:
        def __init__(self, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback) -> bool:
            return False

        def get(self, url: str, params: dict) -> FakeResponse:
            requests.append(params)

            ordered_rows = list(all_rows)
            if params.get("sort") == "_id desc":
                ordered_rows.reverse()

            start: int = params["offset"]
            end: int = start + params["limit"]
            return FakeResponse(ordered_rows[start:end])

    return FakeClient


def make_row(row_id: int, days_ago: int) -> dict:
    received = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return {
        "_id": row_id,
        "INCIDENT_NUM": f"INC{row_id}",
        "CALL_RECEIVED": received.strftime(CALL_RECEIVED_FORMAT),
    }


def test_stops_after_a_full_old_page_instead_of_paging_the_whole_dataset(
    monkeypatch,
):
    page_size: int = 5
    total_pages: int = 120
    rows_in_window: int = 2 * page_size

    # oldest first: 110 pages of old rows, then the last 2 pages inside the window
    all_rows: list[dict] = []
    for row_id in range(1, total_pages * page_size + 1):
        is_recent: bool = row_id > total_pages * page_size - rows_in_window
        all_rows.append(make_row(row_id, days_ago=1 if is_recent else 100))

    requests: list[dict] = []

    monkeypatch.setattr(phoenix_data_client.settings, "ingest_limit", page_size)
    monkeypatch.setattr(phoenix_data_client.settings, "max_pages", 200)
    monkeypatch.setattr(phoenix_data_client.settings, "lookback_days", 21)
    monkeypatch.setattr(
        phoenix_data_client.httpx, "Client", make_fake_client(all_rows, requests)
    )
    monkeypatch.setattr(phoenix_data_client.time, "sleep", lambda seconds: None)

    pages = list(phoenix_data_client.iter_phx_data_pages())

    fetched_ids: set[int] = set()
    for page in pages:
        for record in page:
            fetched_ids.add(record["_id"])

    # both in-window pages were fetched
    assert {row["_id"] for row in all_rows[-rows_in_window:]} <= fetched_ids
    # 2 in-window pages plus the one full old page that ends the run
    assert len(requests) == 3
    assert requests[0]["sort"] == "_id desc"


def test_a_few_old_rows_inside_a_page_do_not_end_the_run(monkeypatch):
    page_size: int = 5

    # newest-last storage, but page 2 from the top mixes old and recent rows
    all_rows: list[dict] = []
    for row_id in range(1, 6):
        all_rows.append(make_row(row_id, days_ago=100))
    # row 6 is old but arrives out of order among recent rows
    all_rows.append(make_row(6, days_ago=100))
    for row_id in range(7, 16):
        all_rows.append(make_row(row_id, days_ago=1))

    requests: list[dict] = []

    monkeypatch.setattr(phoenix_data_client.settings, "ingest_limit", page_size)
    monkeypatch.setattr(phoenix_data_client.settings, "max_pages", 200)
    monkeypatch.setattr(phoenix_data_client.settings, "lookback_days", 21)
    monkeypatch.setattr(
        phoenix_data_client.httpx, "Client", make_fake_client(all_rows, requests)
    )
    monkeypatch.setattr(phoenix_data_client.time, "sleep", lambda seconds: None)

    pages = list(phoenix_data_client.iter_phx_data_pages())

    fetched_ids: set[int] = set()
    for page in pages:
        for record in page:
            fetched_ids.add(record["_id"])

    # desc pages: [15..11] [10..6] [5..1]. Page 2 has one old row (6) but
    # four recent ones, so it must not stop the run. Page 3 is all old.
    assert len(requests) == 3
    assert 7 in fetched_ids
