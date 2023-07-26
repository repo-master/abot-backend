
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


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
    STDDEV = 'stddev'
    COUNT = 'count'
    COMPLIANCE = 'compliance'
    QUANTILE = 'quantile'
    MEDIAN = 'median'
    SUMMARY = 'summary'


class AggregationIn(DataIn, BaseModel):
    method: Union[AggregationMethod, List[AggregationMethod]] = AggregationMethod.RECENT
    aggregation_column: Optional[str] = None
    aggregation_options: Optional[Dict[str, Any]] = None


AggregationOut = Dict[AggregationMethod, Union[float, int]]


class OutliersIn(DataIn, BaseModel):
    outliers_column: Optional[str]
