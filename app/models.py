from pydantic import BaseModel, Field

class CallForService(BaseModel):
    
    # I did Pydantic aliases in this project
    # CKAN returns keys like INCIDENT_NUM, but I want my Python code to use cleaner 
    # field names like incident_num. Using Field(validation_alias="INCIDENT_NUM") keeps the mapping in one model 
    # instead of making a second transformed dictionary before validation. That is simpler and scales better as the number of fields grows.
    incident_num: str = Field(validation_alias="INCIDENT_NUM")
    disp_code: str = Field(validation_alias="DISP_CODE")
    disposition: str = Field(validation_alias="DISPOSITION")
    final_radio_code: str = Field(validation_alias="FINAL_RADIO_CODE")
    final_call_type: str = Field(validation_alias="FINAL_CALL_TYPE")
    call_received: str = Field(validation_alias="CALL_RECEIVED")
    hundred_block_addr: str = Field(validation_alias="HUNDREDBLOCKADDR")
    
    #Grid can be optional because some calls are or fall on the border of others
    grid: str | None = Field(default=None, validation_alias="GRID")