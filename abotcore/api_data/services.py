
from fastapi import Depends
from sqlalchemy import (
    select
)
from sqlalchemy.orm import joinedload

from abotcore.db import (
    get_session,
    Session,
    Transaction
)

from .models import (
    Sensor,
    SensorData,
    Unit
)
from .schemas import (
    SensorDataOut,
    SensorMetadataOut
)

from typing import List, Tuple, Optional


class SensorDataService:
    def __init__(self, session: Session = Depends(get_session)) -> None:
        self.async_session: Session = session

    async def get_sensor_metadata(self, sensor_id: int) -> Optional[SensorMetadataOut]:
        session : Session = self.async_session
        meta_query = await session.execute(
            select(Sensor) \
                .where(Sensor.sensor_id == sensor_id) \
                .options(joinedload(Sensor.sensor_type, innerjoin=True))
        )

        meta_result : Sensor = meta_query.fetchone()

        if meta_result:
            first_sensor_match = meta_result[0] # FIXME: How do we get just one? Is this correct?
            return SensorMetadataOut(
                sensor_urn=first_sensor_match.sensor_urn,
                sensor_id=first_sensor_match.sensor_id,
                sensor_type=first_sensor_match.sensor_type.type_name,
                display_unit=first_sensor_match.sensor_type.default_unit,
                sensor_name=first_sensor_match.sensor_name,
                sensor_alias=first_sensor_match.sensor_alias
            )

    async def get_sensor_data(self, sensor_id : int) -> Tuple[SensorMetadataOut, List[SensorDataOut]]:
        transaction: Transaction
        session : Session = self.async_session
        async with self.async_session.begin() as transaction:
            sensor_metadata = await self.get_sensor_metadata(sensor_id)

            sensor_data_query = select(SensorData) \
                .where(SensorData.sensor_id == sensor_id)
            data_result = await session.scalars(sensor_data_query)
            sensor_data : List[SensorDataOut] = list(map(SensorDataOut.from_orm, data_result.fetchall()))

            return sensor_metadata, sensor_data
