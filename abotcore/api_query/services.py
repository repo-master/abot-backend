
from fastapi import Depends
from sqlalchemy import (
    select,
    and_
)
from sqlalchemy.orm import joinedload

from abotcore.db import (
    get_session,
    Session,
    Transaction
)

from ..api_data.models import (
    Sensor,
    SensorData,
    SensorType,
    UnitSensorMap,
    Unit
)
from ..api_data.schemas import (
    SensorDataOut,
    SensorMetadataOut
)

from datetime import datetime, timedelta
from typing import List, Tuple, Optional


class SensorDataService:
    def __init__(self, session: Session = Depends(get_session)) -> None:
        self.async_session: Session = session

    async def get_sensor_id(self, sensor_type : str, location : str) -> int:
        session: Session = self.async_session
        try:
            sensor_type_id = await self.get_sensor_type(sensor_type= sensor_type)
        except TypeError:
            return None, "Sensor type does not exist need to raise error"
        try: 
            unit_id = await self.get_unit_id(location)
        except TypeError:
            return None, "Unit Does not exist need to raise error"
        sensor_id_query = await session.execute(
            select(UnitSensorMap).join(Unit).join(Sensor).where(Unit.unit_id == unit_id, Sensor.sensor_type_id == sensor_type_id)
            .options( joinedload(UnitSensorMap.sensor), joinedload(UnitSensorMap.unit),)
        )
        try:
            sensor_id = sensor_id_query.fetchone()[0].sensor_id
        except TypeError:
            return None, "Sensor id does not exist"
        metadata = await self.get_metadata_for_sensor(sensor_id)
        return sensor_id , metadata

    
    async def get_sensor_type(self, sensor_type : str) -> int:
        session : Session = self.async_session
        sensor_type_query = await session.execute(
            select(SensorType)
            .where(SensorType.type_name == sensor_type)
        )
        sensor_type_result : Optional[Tuple[SensorType]] = sensor_type_query.fetchone()
        return sensor_type_result[0].sensor_type

    async def get_unit_id(self, location : str) -> int:
        session : Session = self.async_session
        #need to log it
        print(f"Fetching unit info for {location}")
        location = int(location.split(" ")[-1])
        location_query = await session.execute(
            select(Unit)
            .where(Unit.unit_id == location)
        )
        location_result :Optional[Tuple[Unit]] = location_query.fetchone()
        return location_result[0].unit_id
    
    async def get_metadata_for_sensor(self, sensor_id : int):
        session: Session = self.async_session

        meta_query = await session.execute(
            select(Sensor)
            .where(Sensor.sensor_id == sensor_id)
            .options(joinedload(Sensor.sensor_type, innerjoin=True))
        )

        meta_result: Sensor = meta_query.fetchone()

        if meta_result:
            first_sensor_match = meta_result[0]  # FIXME: How do we get just one? Is this correct?
            return SensorMetadataOut(
                sensor_urn=first_sensor_match.sensor_urn,
                sensor_id=first_sensor_match.sensor_id,
                sensor_type=first_sensor_match.sensor_type.type_name,
                display_unit=first_sensor_match.sensor_type.default_unit,
                sensor_name=first_sensor_match.sensor_name,
                sensor_alias=first_sensor_match.sensor_alias
            )
