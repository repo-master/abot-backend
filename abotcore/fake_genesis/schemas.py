'''Data validation schemas (Pydantic) used by genesis endpoints'''

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel
from typing_extensions import NotRequired, TypedDict


class SensorValue(TypedDict):
    '''Raw sensor reading, aka value (can have any kind of value)'''
    value: NotRequired[Any]
    state: NotRequired[Any]
    period: NotRequired[timedelta]


class SensorDataBase(BaseModel):
    '''Single recorded instance of sensor's value'''
    timestamp: datetime
    sensor_id: int
    value: SensorValue


class SensorDataOut(SensorDataBase):
    class Config:
        orm_mode = True


class SensorHealthOut(BaseModel):
    code_name: str

    class Config:
        orm_mode = True


class SensorStateOut(BaseModel):
    last_value: Optional[SensorValue]
    last_timestamp: Optional[datetime]
    sensor_health: Optional[SensorHealthOut]

    class Config:
        orm_mode = True


class UnitMetadata(BaseModel):
    '''Information regarding this Unit (room)'''
    unit_urn: str
    unit_id: int
    unit_alias: Optional[str]

    class Config:
        orm_mode = True

class SensorMetadataBase(BaseModel):
    '''Information regarding this sensor. Base class'''
    sensor_urn: str
    sensor_id: int
    sensor_name: Optional[str]
    sensor_alias: Optional[str]
    sensor_type: str
    display_unit: Optional[str]

    class Config:
        orm_mode = True


class SensorMetadataOut(SensorMetadataBase):
    '''Sensor's metadata, but also with location data'''
    sensor_location: Optional[UnitMetadata]
    sensor_status: Optional[SensorStateOut]


class PlotlyTrace(BaseModel):
    mode: str
    name: str
    type: str
    x: Optional[List[Union[float, Any]]]
    y: Optional[List[Union[float, Any]]]


class PlotlyFigure(BaseModel):
    data: List[PlotlyTrace]
    layout: Dict


class PlotlyFigureOut(PlotlyFigure):
    pass
