
from fastapi import APIRouter, Depends

from .services import (
    SensorDataService
)

from datetime import datetime
from typing import Optional


# Endpoint router
router = APIRouter(prefix='/query')


@router.get("/sensor_id")
async def fetch_sensor_id(sensor_type: Optional[str] = None,
                          sensor_name: Optional[str] = None,
                          location: Optional[str] = None,
                          sensor_data: SensorDataService = Depends(SensorDataService)):
    metadata = await sensor_data.get_sensor_id(sensor_type, sensor_name, location)

    return {
        'sensor': metadata
    }
