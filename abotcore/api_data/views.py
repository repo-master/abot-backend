
from fastapi import APIRouter, Request, Depends

from .services import (
    SensorDataService
)

# Endpoint router
router = APIRouter(prefix='/data')


@router.get("/sensor")
async def sensor_data(request: Request, sensor_data: SensorDataService = Depends(SensorDataService)):
    sensor_data = await sensor_data.get_sensor_data()
    # TODO: Read parameters (sensor_type) and fetch using sqlalchemy
    return {
        'data': sensor_data
    }
