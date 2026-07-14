import time
from typing import Any
import httpx

from app.config import settings

def fetch_phx_data_records() -> list[dict[ str, Any]]:
    all_raw_records = []
    offset = 0
    
    page_size = settings.ingest_limit
    pages_fetched = 0
    
    with httpx.Client() as client:
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
                
                #add the raw records to the list
                #was originally appends but that would make a list inside a list
                all_raw_records.extend(record_responses)
                offset += len(record_responses)
                pages_fetched += 1
                
                #api results could keep changing, this keeps it in check
                if offset >= request_response["result"]["total"]:
                    break
            
            time.sleep(0.15)
            
        return all_raw_records
