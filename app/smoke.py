import httpx
from pydantic import ValidationError

from app.config import settings
from app.models import CallForService

def main():
    params_query = {
        "resource_id": settings.resource_id,
        "limit": settings.ingest_limit,
    }

    with httpx.Client() as client:
        response = client.get(settings.ckan_base_url, params=params_query)
        data = response.json()
        
        if not data["success"]:  
            print(data["error"]) 
        else:
            records = data["result"]["records"]
            total = data["result"]["total"]
            
            grid_counter = 0
            
            for record in records:
                try:
                    validate_record = CallForService.model_validate(record)
                    print(validate_record)
                    
                    if validate_record.grid is None:
                        grid_counter = grid_counter + 1
                        
                except ValidationError as error:
                    print("Bad record:")
                    print(error)
                
            print(f"Grid was empty: {grid_counter} times")
            print(len(records))
            print(total)


if __name__ == "__main__":
    main()