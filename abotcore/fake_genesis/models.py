'''DB models for use as Genesis'''

from datetime import datetime

from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, ForeignKey,
                        Identity, Integer, String)
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from abotcore.db import Base, ReadableMixin
from .ddl import register_post_relation_handlers


# Abstract Base model

class GenesisBase(Base):
    __abstract__ = True
    __table_args__ = {'schema': 'genesis'}


# Enum classes

class SensorType(GenesisBase):
    __tablename__ = 'sensor_type'
    sensor_type: Mapped[int] = Column(
        'sensor_type',
        Integer,
        Identity(start=1),
        primary_key=True
    )
    type_name: Mapped[str] = Column(
        'type_name',
        String
    )
    default_unit: Mapped[str] = Column(
        'default_unit',
        String
    )


class SensorHealth(GenesisBase):
    __tablename__ = 'sensor_health'
    sensor_health_id: Mapped[int] = Column(
        'sensor_health_id',
        Integer,
        Identity(start=1),
        primary_key=True
    )
    code_name: Mapped[str] = Column(
        'code_name',
        String,
        nullable=False
    )


# Data relations

class Sensor(ReadableMixin, GenesisBase):
    __tablename__ = 'sensors'

    # Columns
    sensor_id: Mapped[int] = Column(
        'sensor_id',
        Integer,
        Identity(start=1),
        primary_key=True
    )
    sensor_urn: Mapped[str] = Column(
        'sensor_urn',
        String
    )
    sensor_type_id: Mapped[int] = Column(
        'sensor_type',
        ForeignKey(SensorType.sensor_type)
    )
    sensor_name: Mapped[str] = Column(
        'sensor_name',
        String
    )
    sensor_alias: Mapped[str] = Column(
        'sensor_alias',
        String
    )

    sensor_type: Mapped["SensorType"] = relationship(SensorType)


class SensorData(ReadableMixin, GenesisBase):
    __tablename__ = 'sensor_data'

    # Columns
    data_id: Mapped[int] = Column(
        'data_id',
        Integer,
        Identity(start=1),
        primary_key=True
    )
    sensor_id: Mapped[int] = Column(
        'sensor_id',
        ForeignKey(Sensor.sensor_id)
    )
    timestamp: Mapped[datetime] = Column(
        'timestamp',
        DateTime
    )
    value: Mapped[dict] = Column(
        'value',
        JSON(none_as_null=True)
    )


class SensorStatus(GenesisBase):
    __tablename__ = 'sensor_status'

    # Columns
    sensor_status_id: Mapped[int] = Column(
        'sensor_status_id',
        Integer,
        Identity(start=1),
        primary_key=True
    )
    sensor_id: Mapped[int] = Column(
        'sensor_id',
        ForeignKey(Sensor.sensor_id),
        unique=True
    )
    time_created: Mapped[datetime] = Column(
        'time_created',
        DateTime(timezone=True),
        server_default=func.now()
    )
    time_updated: Mapped[datetime] = Column(
        'time_updated',
        DateTime(timezone=True),
        onupdate=func.now()
    )
    last_value: Mapped[dict] = Column(
        'last_value',
        JSON(none_as_null=True)
    )
    # TODO: Rename to last_value_time
    last_timestamp: Mapped[datetime] = Column(
        'last_timestamp',
        DateTime
    )
    sensor_health_id: Mapped[dict] = Column(
        'sensor_health_id',
        ForeignKey(SensorHealth.sensor_health_id),
    )
    last_health_time: Mapped[datetime] = Column(
        'last_health_time',
        DateTime,
        server_default=func.now()
    )
    sensor_health: Mapped["SensorHealth"] = relationship(SensorHealth, lazy=False)


class Unit(ReadableMixin, GenesisBase):
    __tablename__ = 'units'

    # Columns
    unit_id = Column(Integer, primary_key=True, autoincrement=True)
    unit_urn = Column(String, nullable=False, unique=True)
    unit_alias = Column(String, unique=True)
    is_active = Column(Boolean)
    is_warehouse_level_unit = Column(Boolean, default=False)
    time_created: Mapped[datetime] = Column(
        'time_created',
        DateTime(timezone=True),
        server_default=func.now()
    )
    time_updated: Mapped[datetime] = Column(
        'time_updated',
        DateTime(timezone=True),
        onupdate=func.now()
    )


class UnitSensorMap(ReadableMixin, GenesisBase):
    __tablename__ = 'unit_sensor_map'
    # Columns
    unit_sensor_map_id: Mapped[int] = Column(
        'unit_sensor_id',
        Integer,
        Identity(start=1),
        primary_key=True
    )
    unit_id: Mapped[int] = Column(
        'unit_id',
        ForeignKey(Unit.unit_id)
    )
    sensor_id: Mapped[int] = Column(
        'sensor_id',
        ForeignKey(Sensor.sensor_id)
    )

    unit: Mapped[Unit] = relationship(Unit)
    sensor: Mapped[Sensor] = relationship(Sensor)


# register_post_relation_handlers(GenesisBase)
