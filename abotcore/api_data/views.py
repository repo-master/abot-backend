
from fastapi import APIRouter, Request, Depends

from .services import (
    SensorDataService
)

# Endpoint router
router = APIRouter(prefix='/data')


@router.get("/sensor")
async def sensor_data(sensor_id: int, sensor_data: SensorDataService = Depends(SensorDataService)):
    metadata, data = await sensor_data.get_sensor_data(sensor_id)
    # TODO: Read parameters (sensor_type) and fetch using sqlalchemy
    return {
        'metadata': metadata,
        'data': data
    }
