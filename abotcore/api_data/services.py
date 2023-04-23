
from fastapi import Depends, Response
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

from .models import (
    Sensor,
    SensorData,
    Unit
)
from .schemas import (
    SensorDataOut,
    SensorMetadataOut
)

from datetime import datetime, timedelta, timezone
from typing import List, Tuple, Optional


class SensorDataService:
    def __init__(self, session: Session = Depends(get_session)) -> None:
        self.async_session: Session = session

    async def get_sensor_metadata(self, sensor_id: int) -> Optional[SensorMetadataOut]:
        session: Session = self.async_session
        meta_query = await session.execute(
            select(Sensor)
            .where(Sensor.sensor_id == sensor_id)
            .options(joinedload(Sensor.sensor_type, innerjoin=True))
        )

        meta_result: Optional[Tuple[Sensor]] = meta_query.fetchone()

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

    async def get_sensor_data(self,
                              sensor_id: int,
                              timestamp_from: Optional[datetime] = None,
                              timestamp_to: Optional[datetime] = None) -> Tuple[SensorMetadataOut, List[SensorDataOut]]:
        transaction: Transaction
        session: Session = self.async_session

        # Default date range - today all day
        if timestamp_from is None:
            timestamp_from = datetime.now() - timedelta(hours=24)
        if timestamp_to is None:
            timestamp_to = datetime.now()

        # Database has timestamp stored as timezone-naive format [timestamp without timezone] in UTC, so:
        # - Convert the given timestamp to UTC from whatever TZ it was
        # - Strip the timezone information to match the DB schema
        timestamp_from = timestamp_from.astimezone(timezone.utc).replace(tzinfo=None)
        timestamp_to = timestamp_to.astimezone(timezone.utc).replace(tzinfo=None)

        async with self.async_session.begin() as transaction:
            sensor_metadata = await self.get_sensor_metadata(sensor_id)

            sensor_data_query = select(SensorData) \
                .where(SensorData.sensor_id == sensor_id) \
                .where(and_(SensorData.timestamp >= timestamp_from, SensorData.timestamp <= timestamp_to))
            data_result = await session.scalars(sensor_data_query)
            sensor_data: List[SensorDataOut] = list(map(SensorDataOut.from_orm, data_result.fetchall()))

            return sensor_metadata, sensor_data


class GraphPlotService:
    async def plot_from_sensor_data(self, sensor_metadata: SensorMetadataOut, sensor_data: SensorDataOut) -> Response:
        with open("data/sample-graph.png", "rb") as img_file:
            image_blob = img_file.read()
            return Response(image_blob, media_type="image/png")
