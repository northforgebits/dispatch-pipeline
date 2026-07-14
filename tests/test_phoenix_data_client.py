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
        phoenix_data_client.fetch_phx_data_records()

    assert len(requests) == 1
