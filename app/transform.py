from datetime import datetime, timezone
from zoneinfo import ZoneInfo

PHOENIX = ZoneInfo("America/Phoenix")


def to_record_row(validated) -> dict:
    occurred_at = datetime.strptime(
        validated.call_received,
        "%m/%d/%Y %I:%M:%S %p",
    )

    if occurred_at.tzinfo is None:
        occurred_at = occurred_at.replace(tzinfo=PHOENIX)

    occurred_at = occurred_at.astimezone(timezone.utc)
    raw_fields = validated.model_dump()

    return {
        "natural_key": validated.incident_num,
        "occurred_at": occurred_at,
        "raw_fields": raw_fields,
        "ingested_at": datetime.now(timezone.utc),
        "disp_code": validated.disp_code,
        "disposition": validated.disposition,
        "final_radio_code": validated.final_radio_code,
        "final_call_type": validated.final_call_type,
        "hundred_block_addr": validated.hundred_block_addr,
        "grid": validated.grid,
    }
