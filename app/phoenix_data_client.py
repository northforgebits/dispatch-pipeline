import time
from datetime import datetime, timedelta, timezone
from typing import Any, Iterator
import httpx

from app.config import settings
from app.transform import parse_call_received


def page_is_all_older_than(
    records: list[dict[str, Any]], cutoff: datetime
) -> bool:
    #a row we can't read is not proof the page is old, so it keeps us going
    for record in records:
        try:
            occurred_at = parse_call_received(str(record["CALL_RECEIVED"]))
        except (KeyError, ValueError):
            return False

        if occurred_at >= cutoff:
            return False

    return True


def iter_phx_data_pages() -> Iterator[list[dict[str, Any]]]:
    offset = 0
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.lookback_days)
    
    page_size = settings.ingest_limit
    pages_fetched = 0
    
    with httpx.Client(timeout=30.0) as client:
        while True:
            
            if pages_fetched >= settings.max_pages:
                raise RuntimeError("Safety Cap Reached")
            
            #limit is the maximum number of rows to return,
            #and offset skips that many rows before returning results
            params = {
                "resource_id": settings.resource_id,
                "limit": page_size,
                "offset": offset,
                #newest first, so the run can stop once it reaches old rows.
                #_id is the datastore's insert order. CALL_RECEIVED is text,
                #so sorting on it would not be chronological.
                "sort": "_id desc",
            }
        
            client_request = client.get(settings.ckan_base_url, params=params)
            
            #check http status first
            client_request.raise_for_status()

            request_response = client_request.json()
            
            if not request_response["success"]:
                
                raise RuntimeError(request_response["error"])
            
            else:
                record_responses = request_response["result"]["records"]
                
                if len(record_responses) == 0:
                    break
                
                #yield one page at a time instead of building one big list,
                #so the caller never holds more than a page in memory
                yield record_responses
                offset += len(record_responses)
                pages_fetched += 1

                #stop only when a whole page is older than the cutoff, so a
                #few out-of-order rows can't end the run early
                if page_is_all_older_than(record_responses, cutoff):
                    break
                
                #api results could keep changing, this keeps it in check
                if offset >= request_response["result"]["total"]:
                    break
            
            time.sleep(0.15)