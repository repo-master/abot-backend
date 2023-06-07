'''Data validation schemas (Pydantic) used by genesis endpoints'''

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel
from typing_extensions import NotRequired, TypedDict







class SensorHealthOut(BaseModel):
    code_name: str


class SensorStateOut(BaseModel):
    last_value: dict #Optional[SensorValue]
    last_timestamp: str#Optional[datetime]
    sensor_health: Optional[SensorHealthOut]

class UnitMetadata(BaseModel):
    '''Information regarding this Unit (room)'''
    unit_urn: str
    unit_id: int
    unit_alias: Optional[str]


class SensorMetadataBase(BaseModel):
    '''Information regarding this sensor. Base class'''
    sensor_urn: str
    sensor_id: int
    sensor_name : Optional[str]
    sensor_alias: Optional[str]
    sensor_type: Optional[str]
    display_unit: Optional[str]



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

class SensorStatus(BaseModel):
    '''Information regarding sensor Status'''
    sensor_id : int
    state : str
    location_id : Optional[int]

class SensorDataOut(BaseModel):
    sensor_id : int
    value : Optional[dict]
    timestamp : str
