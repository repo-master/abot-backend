'''DB models for use as Genesis'''

from datetime import datetime

from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, ForeignKey,
                        Identity, Integer, String)
from sqlalchemy.orm import Mapped, relationship

from abotcore.db import Base, ReadableMixin


class SensorType(Base):
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


class Sensor(ReadableMixin, Base):
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
        ForeignKey('sensor_type.sensor_type')
    )
    sensor_name: Mapped[str] = Column(
        'sensor_name',
        String
    )
    sensor_alias: Mapped[str] = Column(
        'sensor_alias',
        String
    )

    sensor_type: Mapped["SensorType"] = relationship("SensorType")


class SensorData(ReadableMixin, Base):
    __tablename__ = 'sensor_data'

    # Columns
    data_id: Mapped[int] = Column(
        'data_id',
        Integer,
        Identity(start=1),
        primary_key=True
    )
    timestamp: Mapped[datetime] = Column(
        'timestamp',
        DateTime
    )
    sensor_id: Mapped[int] = Column(
        'sensor_id',
        ForeignKey('sensors.sensor_id')
    )
    value: Mapped[dict] = Column(
        'value',
        JSON(none_as_null=True)
    )


class Unit(ReadableMixin, Base):
    __tablename__ = 'units'

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
    unit_sensor_map_id: Mapped[int] = Column(
        'unit_sensor_id',
        Integer,
        Identity(start=1),
        primary_key=True
    )
    unit_id: Mapped[int] = Column(
        'unit_id',
        ForeignKey('units.unit_id')
    )
    sensor_id: Mapped[int] = Column(
        'sensor_id',
        ForeignKey('sensors.sensor_id')
    )

    unit: Mapped["Unit"] = relationship("Unit")
    sensor: Mapped["Sensor"] = relationship("Sensor")
