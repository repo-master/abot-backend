'''DB models used by chat endpoints'''

from abotcore.db import Base, Session
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    Float,
    Identity,
    ForeignKey,
    JSON
)
from sqlalchemy import (
    select
)
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.orm import (
    relationship
)

from datetime import datetime


class ReadableMixin:
    @classmethod
    async def read_all(cls, session: Session) -> ScalarResult:
        return await session.scalars(select(cls))


class SensorType(Base):
    __tablename__ = 'sensor_type'
    sensor_type = Column(
        'sensor_type',
        Integer,
        Identity(start=1),
        primary_key=True
    )
    type_name = Column(
        'type_name',
        String
    )
    default_unit = Column(
        'default_unit',
        String
    )


class Sensor(ReadableMixin, Base):
    __tablename__ = 'sensors'

    # Columns
    sensor_id = Column(
        'sensor_id',
        Integer,
        Identity(start=1),
        primary_key=True
    )
    sensor_urn = Column(
        'sensor_urn',
        String
    )
    sensor_type = Column(
        'sensor_type',
        ForeignKey('sensor_type.sensor_type')
    )


class SensorData(ReadableMixin, Base):
    __tablename__ = 'sensor_data'

    # Columns
    data_id = Column(
        'data_id',
        Integer,
        Identity(start=1),
        primary_key=True
    )
    timestamp = Column(
        'timestamp',
        DateTime
    )
    sensor_id = Column(
        'sensor_id',
        ForeignKey('sensor_master.sensor_id')
    )
    value = Column(
        'value',
        JSON(none_as_null=True)
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
        'unit_sensor_id',
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
