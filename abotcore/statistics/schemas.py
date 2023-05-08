
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel
from typing_extensions import NotRequired, TypedDict


class DataIn(BaseModel):
    data: List[Dict[str, Any]]
    index: Optional[str]
    columns: Optional[List[str]]


class AggregationMethod(str, Enum):
    RECENT = 'recent'
    AVERAGE = 'average'
    MINIMUM = 'minimum'
    MAXIMUM = 'maximum'


class AggregationIn(DataIn, BaseModel):
    method: Union[AggregationMethod, List[AggregationMethod]] = AggregationMethod.RECENT
    aggregation_column: Optional[str]
