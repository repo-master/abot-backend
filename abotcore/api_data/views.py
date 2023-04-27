
import urllib.parse

from fastapi import APIRouter, HTTPException, Depends

from .services import (
    SensorDataService,
    GraphPlotService
)
from .schemas import (
    SensorDataIn
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
    sensor_metadata = await sensor_data.get_sensor_metadata(sensor_id)
    sensor_point_data = await sensor_data.get_sensor_data(sensor_id, timestamp_from, timestamp_to)

    return {
        'metadata': sensor_metadata,
        'data': sensor_point_data
    }


@router.get('/report')
async def data_report(sensor_id: int,
                      timestamp_from: Optional[datetime] = None,
                      timestamp_to: Optional[datetime] = None,
                      sensor_data: SensorDataService = Depends(SensorDataService),
                      graph_plot: GraphPlotService = Depends(GraphPlotService)):
    graph_data_uri: Optional[str] = None
    sensor_metadata = await sensor_data.get_sensor_metadata(sensor_id)
    sensor_point_data = await sensor_data.get_sensor_data(sensor_id, timestamp_from, timestamp_to)

    # Generate plot image
    async with graph_plot.plot_from_sensor_data(sensor_metadata, sensor_point_data) as graph_image:
        if graph_image is None:
            # Image was not generated
            raise HTTPException(404, detail="Sensor data unavailable")
        graph_data_uri = graph_plot.image_to_data_uri(graph_image)

    report_page_params = {
        'sensor_id': sensor_id
    }

    if timestamp_from is not None:
        report_page_params.update({'time_from': timestamp_from.isoformat()})
    if timestamp_to is not None:
        report_page_params.update({'time_to': timestamp_to.isoformat()})

    interactive_report_url = 'https://example.com/report/?%s' % urllib.parse.urlencode(report_page_params)

    response = {
        'interactive_report_route': interactive_report_url,
        'preview_image': graph_data_uri
    }

    return response


@router.post('/sensor/insert')
async def insert_sensor_data(data: SensorDataIn,
                             sensor_data: SensorDataService = Depends(SensorDataService)):
    await sensor_data.insert_sensor_data(data)
    return {"status": "ok"}
