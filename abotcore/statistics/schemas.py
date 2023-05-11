
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel
from typing_extensions import NotRequired, TypedDict


class DataIn(BaseModel):
    # Pandas DataFrame parameters
    data: List[Dict[str, Any]]
    index: Optional[List[Any]]
    columns: Optional[List[str]]

    # Other optional settings
    index_column_names: Optional[Union[str, List[str]]]
    datetime_column_names: Optional[Union[str, List[str]]]


class AggregationMethod(str, Enum):
    RECENT = 'recent'
    AVERAGE = 'average'
    MINIMUM = 'minimum'
    MAXIMUM = 'maximum'
    STD_DEV = 'std_dev'
    COUNT = 'count'
    COMPLIANCE = 'compliance'
    QUANTILE = 'quantile'

class AggregationIn(DataIn, BaseModel):
    method: Union[AggregationMethod, List[AggregationMethod]] = AggregationMethod.RECENT
    aggregation_column: Optional[str] = None
    aggregation_options: Optional[Dict[str, Any]] = None

AggregationOut = Dict[AggregationMethod, Union[float, int]]

class OutliersIn(DataIn, BaseModel):
    outliers_column: Optional[str]
