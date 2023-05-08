
from fastapi import Depends
from sqlalchemy import (
    select,
    and_, or_
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

    async def get_sensor_id(self,
                            sensor_type: Optional[str],
                            sensor_name: Optional[str],
                            location: Optional[str]) -> Optional[SensorMetadataOut]:
        session: Session = self.async_session

        # FIXME: This is incorrect. There should be fallback methods.
        '''
        try:
            sensor_type_id = await self.get_sensor_type(sensor_type=sensor_type)
        except TypeError:
            # TODO: ???? What is this
            return None, "Sensor type does not exist need to raise error"
        try:
            unit_id = await self.get_unit_id(location)
        except TypeError:
            # TODO: This too, what to do here?????
            return None, "Unit Does not exist need to raise error"
        '''

        sensor_id_search_query = select(UnitSensorMap) \
            .join(Unit) \
            .join(Sensor) \
            .join(SensorType)

        if sensor_type is not None:
            sensor_id_search_query = sensor_id_search_query.where(
                SensorType.type_name == sensor_type.lower()
            )

        if location is not None:
            loc_sanitized = "%{}%".format(location.strip())
            sensor_id_search_query = sensor_id_search_query.where(
                or_(Unit.unit_alias.ilike(loc_sanitized), Unit.global_unit_name.ilike(loc_sanitized))
            )

        sensor_id_search_query = sensor_id_search_query.options(
            joinedload(UnitSensorMap.sensor),
            joinedload(UnitSensorMap.unit)
        )

        # TODO: Sort by some method (closest match, location, geohash, etc.)

        sensor_id_result = await session.execute(
            sensor_id_search_query
        )

        sensor_id_row = sensor_id_result.fetchone()

        if sensor_id_row:
            sensor_id = sensor_id_row[0].sensor_id
            metadata = await self.get_metadata_for_sensor(sensor_id)
            return metadata

    async def get_sensor_type(self, sensor_type: str) -> int:
        session: Session = self.async_session
        sensor_type_result = await session.execute(
            select(SensorType)
            .where(SensorType.type_name == sensor_type)
        )
        sensor_type_result: Optional[Tuple[SensorType]] = sensor_type_result.fetchone()
        return sensor_type_result[0].sensor_type

    async def get_unit_id(self, location: str) -> Optional[int]:
        if len(location.strip()) == 0:
            return

        session: Session = self.async_session
        # need to log it
        print(f"Fetching unit info for {location}")
        # FIXME: Dubious logic
        location = int(location.split(" ")[-1])
        location_result = await session.execute(
            select(Unit)
            .where(Unit.unit_id == location)
        )
        location_result: Optional[Tuple[Unit]] = location_result.fetchone()
        return location_result[0].unit_id

    # TODO: Remove this method, redundant
    async def get_metadata_for_sensor(self, sensor_id: int):
        session: Session = self.async_session

        meta_result = await session.execute(
            select(Sensor)
            .where(Sensor.sensor_id == sensor_id)
            .options(joinedload(Sensor.sensor_type, innerjoin=True))
        )

        meta_row: Sensor = meta_result.fetchone()

        if meta_row:
            first_sensor_match = meta_row[0]  # FIXME: How do we get just one? Is this correct?
            return SensorMetadataOut(
                sensor_urn=first_sensor_match.sensor_urn,
                sensor_id=first_sensor_match.sensor_id,
                sensor_type=first_sensor_match.sensor_type.type_name,
                display_unit=first_sensor_match.sensor_type.default_unit,
                sensor_name=first_sensor_match.sensor_name,
                sensor_alias=first_sensor_match.sensor_alias
            )
