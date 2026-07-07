from pydantic import ValidationError

from app.models import CallForService
from app.phoenix_data_client import fetch_phx_data_records


def main():
    raw_records = fetch_phx_data_records()

    grid_counter = 0
    valid_counter = 0
    bad_counter = 0

    for raw_record in raw_records:
        try:
            validated_record = CallForService.model_validate(raw_record)
            valid_counter += 1

            if validated_record.grid is None:
                grid_counter += 1

        except ValidationError as error:
            bad_counter += 1
            print("Bad record:")
            print(error)

    print(f"Fetched raw records: {len(raw_records)}")
    print(f"Valid records: {valid_counter}")
    print(f"Bad records: {bad_counter}")
    print(f"Grid was empty: {grid_counter} times")


if __name__ == "__main__":
    main()