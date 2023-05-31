
from typing import Any, Callable, Dict, List, Optional, Set

import pandas as pd

from .schemas import (AggregationIn, AggregationMethod, AggregationOut, DataIn,
                      OutliersIn)

PERCENTILE_25 = 0.25
PERCENTILE_75 = 0.75


class DataStatisticsService:
    ### Aggregation methods ###
    # Takes a series as input (it has data and index) and performs some statistical operation on it.

    def data_agg_recent(data: pd.Series, **kwargs) -> float:
        '''Grabs the most recent (by index) value'''
        return data.sort_index(ascending=False).iloc[0].astype(float)

    def data_agg_arithmetic_mean(data: pd.Series, **kwargs) -> float:
        '''Calculates arithmetic mean (sum/count)'''
        return data.mean().astype(float)

    def data_agg_max(data: pd.Series, **kwargs) -> float:
        '''Grabs the largest value'''
        return data.max().astype(float)

    def data_agg_min(data: pd.Series, **kwargs) -> float:
        '''Grabs the smallest value'''
        return data.min().astype(float)

    def data_std_dev(data: pd.Series, **kwargs) -> float:
        '''Returns the std value'''
        return data.std().astype(float)

    def data_std_median(data: pd.Series, **kwargs) -> float:
        '''Returns the std value'''
        return data.median().astype(float)

    def data_agg_count(data: pd.Series, **kwargs) -> int:
        '''Returns the number of records'''
        # Yes it's that simple.
        return data.count()

    def data_agg_compliance(data: pd.Series, lower_target: Optional[float] = None, upper_target: Optional[float] = None, **kwargs) -> float:
        if data.count() == 0:
            return 0.0
        if lower_target is None:
            lower_target = data.min()
        if upper_target is None:
            upper_target = data.max()

        return round(
            data.between(lower_target, upper_target).sum() / data.count(), 3)

    def data_agg_quantile(data: pd.Series, quantile_size: float = 0.5, **kwargs) -> float:
        return data.quantile(quantile_size).astype(float)

    def data_get_outliers(data: pd.Series, only_outliers: bool = True, **kwargs) -> pd.DataFrame:
        # Calculate the IQR of the value column
        Q1 = data.quantile(PERCENTILE_25)
        Q3 = data.quantile(PERCENTILE_75)

        IQR = Q3 - Q1

        # Define the outlier threshold
        threshold = (
            Q1 - 1.5 * IQR,     # Lower limit
            Q3 + 1.5 * IQR      # Upper limit
        )

        # Identify the outliers, mark them accordingly
        outliers = data.to_frame()
        outliers["is_extreme_low"] = (data < threshold[0])
        outliers["is_extreme_high"] = (data > threshold[1])
        outliers['lower_threshold'] = threshold[0]
        outliers['higher_threshold'] = threshold[1]
        # Filter out only actual outliers
        if only_outliers:
            outliers = outliers[outliers["is_extreme_high"] | outliers['is_extreme_low']]
        return outliers.reset_index()

    # Enum->Method map
    # Collection of all aggregation methods mapped to the enum

    AGG_METHODS: Dict[AggregationMethod, Callable[[pd.Series], float]] = {
        AggregationMethod.RECENT: data_agg_recent,
        AggregationMethod.AVERAGE: data_agg_arithmetic_mean,
        AggregationMethod.MAXIMUM: data_agg_max,
        AggregationMethod.MINIMUM: data_agg_min,
        AggregationMethod.STDDEV: data_std_dev,
        AggregationMethod.MEDIAN: data_std_median,
        AggregationMethod.COUNT: data_agg_count,
        AggregationMethod.COMPLIANCE: data_agg_compliance,
        AggregationMethod.QUANTILE: data_agg_quantile
    }

    AGG_SUMMARY_METHODS: Set[AggregationMethod] = {
        AggregationMethod.RECENT,
        AggregationMethod.MINIMUM,
        AggregationMethod.AVERAGE,
        AggregationMethod.MAXIMUM,
        AggregationMethod.STDDEV,
        AggregationMethod.MEDIAN,
        AggregationMethod.COUNT
    }

    async def extract_data(self, data_in: DataIn) -> pd.DataFrame:
        df = pd.DataFrame(**data_in.dict(
            include=DataIn.__fields__.keys(),
            exclude={"index_column_names", "datetime_column_names"},
            exclude_unset=True
        ))
        if data_in.datetime_column_names is not None:
            dt_cols = data_in.datetime_column_names
            if isinstance(dt_cols, str):
                df[dt_cols] = pd.to_datetime(df[dt_cols], errors='ignore')
            elif isinstance(dt_cols, list):
                df[dt_cols] = df[dt_cols].apply(
                    lambda col: pd.to_datetime(col, errors='ignore'), axis=0)
        if data_in.index_column_names is not None:
            df.set_index(data_in.index_column_names, inplace=True)
        return df

    async def aggregation(self, agg_data: AggregationIn) -> AggregationOut:
        '''Calculates aggregation on given data using the given method or methods'''
        df = await self.extract_data(agg_data)

        def _do_aggregation(data: pd.Series, methods: Set[AggregationMethod], options: Dict[str, Any]) -> AggregationOut:
            result: AggregationOut = {}
            for mthd in methods:
                if mthd == AggregationMethod.SUMMARY:
                    result.update(_do_aggregation(
                        data,
                        self.AGG_SUMMARY_METHODS,
                        options
                    ))
                    continue
                result[mthd] = self.AGG_METHODS[mthd](data, **options)
            return result

        methods: Set[AggregationMethod] = {AggregationMethod(agg_data.method)} if isinstance(
            agg_data.method, str) else set(map(AggregationMethod, agg_data.method))
        data_series: pd.Series = df[agg_data.aggregation_column or df.columns[-1]]
        agg_options: Dict[str, Any] = agg_data.aggregation_options or {}

        return _do_aggregation(data_series, methods, agg_options)

    async def outliers(self, data: OutliersIn) -> List[dict]:
        df = await self.extract_data(data)
        return DataStatisticsService.data_get_outliers(df[data.outliers_column or df.columns[-1]]).to_dict(orient='records')
