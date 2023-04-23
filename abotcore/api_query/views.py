
from fastapi import APIRouter, Depends

from .services import (
    SensorDataService
)

from datetime import datetime
from typing import Optional


# Endpoint router
router = APIRouter(prefix='/query')


@router.get("/sensor_id")
async def fetch_sensor_id(sensor_type: str,
                          location: str,
                          sensor_data: SensorDataService = Depends(SensorDataService)):
    sensor_id, metadata = await sensor_data.get_sensor_id(sensor_type, location)
    return {
        'sensor_id': sensor_id,
        'metadata': metadata
    }
