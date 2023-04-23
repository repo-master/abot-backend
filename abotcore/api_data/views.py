
from fastapi import APIRouter, Depends

from .services import (
    SensorDataService,
    GraphPlotService
)

from datetime import datetime
from typing import Optional


# Endpoint router
router = APIRouter(prefix='/data')


@router.get("/sensor")
async def sensor_data(sensor_id: int,
                      timestamp_from: Optional[datetime] = None,
                      timestamp_to: Optional[datetime] = None,
                      sensor_data: SensorDataService = Depends(SensorDataService)):
    metadata, data = await sensor_data.get_sensor_data(sensor_id, timestamp_from, timestamp_to)
    # TODO: Read parameters (sensor_type) and fetch using sqlalchemy
    return {
        'metadata': metadata,
        'data': data
    }


@router.get('/report')
async def data_report(sensor_id: int,
                      timestamp_from: Optional[datetime] = None,
                      timestamp_to: Optional[datetime] = None,
                      sensor_data: SensorDataService = Depends(SensorDataService),
                      graph_plot: GraphPlotService = Depends(GraphPlotService)):
    metadata, data = await sensor_data.get_sensor_data(sensor_id, timestamp_from, timestamp_to)
    graph_image = await graph_plot.plot_from_sensor_data(metadata, data)
    return graph_image
