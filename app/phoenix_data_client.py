import time
from typing import Any, Iterator
import httpx

from app.config import settings


def iter_phx_data_pages() -> Iterator[list[dict[str, Any]]]:
    offset = 0
    page_size = settings.ingest_limit
    pages_fetched = 0

    with httpx.Client() as client:
        while True:
            if pages_fetched >= settings.max_pages:
                raise RuntimeError("Safety Cap Reached")

            params = {
                "resource_id": settings.resource_id,
                "limit": page_size,
                "offset": offset,
            }

            client_request = client.get(settings.ckan_base_url, params=params)
            client_request.raise_for_status()
            request_response = client_request.json()

            if not request_response["success"]:
                raise RuntimeError(request_response["error"])

            record_responses = request_response["result"]["records"]

            if len(record_responses) == 0:
                break

            # yield one page instead of accumulating into one big list
            yield record_responses

            offset += len(record_responses)
            pages_fetched += 1

            if offset >= request_response["result"]["total"]:
                break

            time.sleep(0.15)