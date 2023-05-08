
from typing import Optional, Union, List

from fastapi import APIRouter, Depends, HTTPException

from .services import DataStatisticsService
from .schemas import AggregationIn

router = APIRouter(prefix='/statistics')


#### /statistics/ ####

@router.post("/aggregation")
async def data_aggregation(agg_data: AggregationIn, stat_serv: DataStatisticsService = Depends(DataStatisticsService)):
    return await stat_serv.aggregation(agg_data)
