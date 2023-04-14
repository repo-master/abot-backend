'''DB models used by chat endpoints'''

from abotcore.db import Base, Session
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    Float,
    Identity
)
from sqlalchemy import (
    select
)
from sqlalchemy.engine.result import ScalarResult

from datetime import datetime


class ReadableMixin:
    @classmethod
    async def read_all(cls, session: Session) -> ScalarResult:
        return await session.scalars(select(cls))


class Sensor(ReadableMixin, Base):
    __tablename__ = 'sensor_master'

    # Columns
    sensor_id = Column(
        'id',
        Integer,
        Identity(start=1),
        primary_key=True
    )
    sensor_name = Column(
        'sensor_name',
        String
    )


class SensorData(ReadableMixin, Base):
    __tablename__ = 'history_num'

    # Columns
    timestamp = Column(
        'timestamp',
        DateTime,
        primary_key=True
    )
    history_id = Column(
        'history_id',
        String
    )
    value = Column(
        'value',
        Float()
    )


class Unit(ReadableMixin, Base):
    __tablename__ = 'unit_master'
    # Columns
    unit_id = Column(Integer, primary_key=True, autoincrement=True)
    global_unit_name = Column(String, nullable=False, unique=True)
    unit_alias = Column(String, unique=True)
    is_active = Column(Boolean)
    is_warehouse_level_unit = Column(Boolean, default=False)
    from_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    to_date = Column(DateTime)
    created_by = Column(String, nullable=False, default='Admin')
    created_ts = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_by = Column(String)
    updated_ts = Column(DateTime)


class UnitSensorMap(ReadableMixin, Base):
    __tablename__ = 'unit_sensor_map'
    # Columns
    unit_sensor_map_id = Column(
        'unit_sensor_map_id',
        Integer,
        Identity(start=1),
        primary_key=True
    )
    unit_id = Column(
        'unit_id',
        Integer
    )
    sensor_id = Column(
        'sensor_id',
        Integer
    )
