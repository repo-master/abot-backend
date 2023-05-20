
import json
import urllib.parse
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse

from .schemas import SensorDataIn, PlotlyFigureOut
from .services import (GraphPlotService, InteractiveGraphService,
                       JSONEncodeData, SensorDataService, UnitService)


class FixedJSONResponse(JSONResponse):
    def __init__(self, *args, json_encoder=None, **kwargs):
        self._encoder = json_encoder
        super().__init__(*args, **kwargs)

    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            cls=self._encoder,
            separators=(",", ":"),
        ).encode("utf-8")


# Main endpoint router for fake Genesis
router = APIRouter(prefix='/genesis')

# Endpoints for reading sensor data/datasets
data_router = APIRouter(prefix="/data")

# Endpoints for querying various aspects of the system itself
query_router = APIRouter(prefix="/query")

# TODO: TEST ONLY!! See below for real endpoint


@router.get('/test_plotly')
async def test_plotly_chart(
        sensor_id: int,
        timestamp_from: Optional[datetime] = None,
        timestamp_to: Optional[datetime] = None,
        sensor_data: SensorDataService = Depends(SensorDataService),
        ig_service: InteractiveGraphService = Depends(InteractiveGraphService)):
    sensor_metadata = await sensor_data.get_sensor_metadata(sensor_id)
    sensor_point_data = await sensor_data.get_sensor_data(sensor_id, timestamp_from, timestamp_to)

    fig = await ig_service.figure_from_sensor_data(sensor_metadata, sensor_point_data)
    if fig:
        return HTMLResponse(fig.to_html())
    raise HTTPException(400, detail="Failed to generate figure. There was no data to process.")

#### /genesis/data/ ####


@data_router.get("/sensor")
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


@data_router.get('/report')
async def data_report(sensor_id: int,
                      timestamp_from: Optional[datetime] = None,
                      timestamp_to: Optional[datetime] = None,
                      sensor_data: SensorDataService = Depends(SensorDataService),
                      graph_plot: GraphPlotService = Depends(GraphPlotService),
                      ig_service: InteractiveGraphService = Depends(InteractiveGraphService)):
    graph_data_uri: Optional[str] = None
    sensor_metadata = await sensor_data.get_sensor_metadata(sensor_id)
    sensor_point_data = await sensor_data.get_sensor_data(sensor_id, timestamp_from, timestamp_to)

    # Generate plot image
    async with graph_plot.plot_from_sensor_data(sensor_metadata, sensor_point_data) as graph_image:
        if graph_image is not None:
            graph_data_uri = graph_plot.image_to_data_uri(graph_image)

    fig_interactive = await ig_service.plot_from_sensor_data_json(sensor_metadata, sensor_point_data)

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
        'preview_image': graph_data_uri,
        'plot_interactive': fig_interactive
    }

    return FixedJSONResponse(response, json_encoder=JSONEncodeData)

# Generate plotly chart JSON


@data_router.get('/report/interactive')
async def interactive_plot(
        sensor_id: int,
        timestamp_from: Optional[datetime] = None,
        timestamp_to: Optional[datetime] = None,
        sensor_data: SensorDataService = Depends(SensorDataService),
        ig_service: InteractiveGraphService = Depends(InteractiveGraphService)) -> PlotlyFigureOut:
    sensor_metadata = await sensor_data.get_sensor_metadata(sensor_id)
    sensor_point_data = await sensor_data.get_sensor_data(sensor_id, timestamp_from, timestamp_to)
    fig = await ig_service.plot_from_sensor_data_json(sensor_metadata, sensor_point_data)
    return FixedJSONResponse(fig, json_encoder=JSONEncodeData)


@data_router.post('/sensor/insert')
async def insert_sensor_data(data: SensorDataIn,
                             sensor_data: SensorDataService = Depends(SensorDataService)):
    await sensor_data.insert_sensor_data(data)
    return {"status": "ok"}


#### /genesis/query/ ####

@query_router.get("/sensor")
async def get_sensor_metadata(sensor_id: int,
                              sensor_data: SensorDataService = Depends(SensorDataService)):
    sensor_metadata = await sensor_data.get_sensor_metadata(sensor_id)
    if sensor_metadata is None:
        raise HTTPException(400, detail="Sensor of id %d does not exist" % sensor_id)
    return sensor_metadata

# TODO: Add filters


@query_router.get("/sensor/list")
async def sensor_list(sensor_data: SensorDataService = Depends(SensorDataService)):
    all_sensors = await sensor_data.get_sensor_list()
    return all_sensors


@query_router.get("/sensor/find")
async def find_sensor(sensor_type: Optional[str] = None,
                      sensor_name: Optional[str] = None,
                      location: Optional[str] = None,
                      sensor_data: SensorDataService = Depends(SensorDataService)):
    sensor_metadata = await sensor_data.query_sensor(sensor_type, sensor_name, location)
    if sensor_metadata is None:
        raise HTTPException(400, detail="Sensor not found")

    return sensor_metadata


@query_router.get("/unit")
async def get_unit_metadata(unit_id: int, unit_service: UnitService = Depends(UnitService)):
    unit_metadata = await unit_service.get_unit_metadata(unit_id)
    if unit_metadata is None:
        raise HTTPException(400, detail="Unit of id %d does not exist" % unit_id)
    return unit_metadata

# TODO: Add filters


@query_router.get("/unit/list")
async def unit_list(unit_service: UnitService = Depends(UnitService)):
    all_units = await unit_service.get_unit_list()
    return all_units


##### Nested routers #####

router.include_router(data_router)
router.include_router(query_router)
