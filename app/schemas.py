from datetime import datetime

from pydantic import BaseModel


class RecordOut(BaseModel):
    model_config = {"from_attributes": True}

    natural_key: str
    occurred_at: datetime | None
    disp_code: str
    disposition: str
    final_radio_code: str
    final_call_type: str
    hundred_block_addr: str
    grid: str | None
