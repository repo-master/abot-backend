
from typing import Optional, Union, List

from fastapi import APIRouter, Depends, HTTPException

from .services import DataStatisticsService
from .schemas import AggregationIn, AggregationOut, OutliersIn

router = APIRouter(prefix='/statistics')


#### /statistics/ ####

@router.post("/aggregation")
async def data_aggregation(agg_data: AggregationIn,
                           stat_serv: DataStatisticsService = Depends(DataStatisticsService)
                           ) -> AggregationOut:
    return await stat_serv.aggregation(agg_data)


@router.post("/outliers")
async def data_outliers(agg_data: OutliersIn, stat_serv: DataStatisticsService = Depends(DataStatisticsService)):
    return await stat_serv.outliers(agg_data)
