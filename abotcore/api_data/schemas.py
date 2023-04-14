'''Data validation schemas (Pydantic) used by chat endpoints'''

from pydantic import BaseModel, Extra
from typing import Optional, Dict, List, Any
from datetime import datetime


class SensorDataOut(BaseModel):
    timestamp: datetime
    history_id: str
    value: float

    class Config:
        orm_mode = True
