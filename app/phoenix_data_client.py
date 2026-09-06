import time
from typing import Any, Iterator
import httpx

from app.config import settings

def iter_phx_data_pages() -> Iterator[list[dict[str, Any]]]:
    offset = 0
    
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
                
                #api results could keep changing, this keeps it in check
                if offset >= request_response["result"]["total"]:
                    break
            
            time.sleep(0.15)