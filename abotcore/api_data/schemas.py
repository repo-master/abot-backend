'''Data validation schemas (Pydantic) used by chat endpoints'''

from pydantic import BaseModel

from typing import Optional, Dict, List, Any
from typing_extensions import TypedDict, NotRequired
from datetime import datetime, timedelta


class SensorValue(TypedDict):
    value: NotRequired[Any]
    state: NotRequired[Any]
    period: NotRequired[timedelta]

class SensorDataOut(BaseModel):
    timestamp: datetime
    sensor_id: str
    value: SensorValue

    class Config:
        orm_mode = True

class SensorMetadataOut(BaseModel):
    sensor_urn: str
    sensor_id: int
    sensor_name: Optional[str]
    sensor_alias: Optional[str]
    sensor_type: str
    display_unit: Optional[str]

    class Config:
        orm_mode = True
