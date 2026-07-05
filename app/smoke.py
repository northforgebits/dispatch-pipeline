import httpx

BASE_URL = "https://www.phoenixopendata.com/api/3/action/datastore_search"
RESOURCE_ID = "ed707785-26b6-4949-9b04-5700b8a0125c"  # 2026 Calls for Service


def main():
    params_query = {
        "resource_id": RESOURCE_ID,
        "limit": 5,
    }

    with httpx.Client() as client:
        response = client.get(BASE_URL, params=params_query)
        data = response.json()
        
        if not data["success"]:  
            print(data["error"]) 
        else:
            records = data["result"]["records"]
            total = data["result"]["total"]
            print(len(records))
            print(total)


if __name__ == "__main__":
    main()