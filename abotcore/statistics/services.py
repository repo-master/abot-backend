
from typing import List, Set, Dict, Callable, Optional, Tuple

from .schemas import DataIn, AggregationIn, AggregationMethod

import pandas as pd

from fastapi import Response


class DataStatisticsService:
    ### Aggregation methods ###
    # Takes a series as input (it has data and index) and performs some statistical operation on it.

    def __data_agg_recent(data: pd.Series) -> float:
        '''Grabs the most recent (by index) value'''
        return data.sort_index(ascending=False).iloc[0].astype(float)

    def __data_agg_arithmetic_mean(data: pd.Series) -> float:
        '''Calculates arithmetic mean (sum/count)'''
        return data.mean().astype(float)

    def __data_agg_max(data: pd.Series) -> float:
        '''Grabs the largest value'''
        return data.max().astype(float)

    def __data_agg_min(data: pd.Series) -> float:
        '''Grabs the smallest value'''
        return data.min().astype(float)

    # Enum->Method map
    # Collection of all aggregation methods mapped to the enum

    AGG_METHODS: Dict[AggregationMethod, Callable[[pd.Series], float]] = {
        AggregationMethod.RECENT: __data_agg_recent,
        AggregationMethod.AVERAGE: __data_agg_arithmetic_mean,
        AggregationMethod.MAXIMUM: __data_agg_max,
        AggregationMethod.MINIMUM: __data_agg_min
    }

    async def extract_data(self, data_in: DataIn) -> pd.DataFrame:
        return pd.DataFrame(**data_in.dict(
            include=DataIn.__fields__.keys(),
            exclude_unset=True
        ))

    async def aggregation(self, agg_data: AggregationIn):
        df = await self.extract_data(agg_data)

        def _do_aggregation(data: pd.Series, methods: Set[AggregationMethod]) -> Dict[AggregationMethod, float]:
            result: Dict[AggregationMethod, float] = {}
            for mthd in methods:
                result[mthd] = self.AGG_METHODS[mthd](data)
            return result

        methods: Set[AggregationMethod] = {AggregationMethod(agg_data.method)} if isinstance(
            agg_data.method, str) else set(map(AggregationMethod, agg_data.method))
        data_series: pd.Series = df[agg_data.aggregation_column or df.columns[-1]]

        return _do_aggregation(data_series, methods)
