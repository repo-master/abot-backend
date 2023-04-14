
from fastapi import APIRouter

from typing import Optional, List


# Endpoint router
router = APIRouter(prefix='/data')


@router.get("/sensor")
async def sensor_data():
    # TODO: Read parameters (sensor_type) and fetch using sqlalchemy
    return {

    }
