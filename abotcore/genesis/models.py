'''DB models for use as Genesis'''

from datetime import datetime

from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, ForeignKey,
                        Identity, Integer, String, text)
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from abotcore.db_gen import UAT_BASE as Base, ReadableMixin
from .ddl import register_post_relation_handlers


# Abstract Base model

class GenesisBase(Base):
    __abstract__ = True


class Sensor:
     query = "select * from sensor_master"

class Unit:
     query = "select * from unit_master"

class UnitSensorMap:
    query ="select * from unit_sensor_map" 


class VWSensorStatus:
        #UAT vw_get_all_metric_summary_data
        #TWC vw_calc_get_metric_summary_data
        query = """
        SELECT 
	sm.sensor_id as sensor_id, 
	sm.global_sensor_name  as sensor_urn, 
	sm.alias as sensor_alias, 
	sm.sensor_type as sensor_type, 
	sm.upper_limit , 
	sm.lower_limit , 
	sm.metric_unit1 as display_unit, 
	vgacmsd.state as code_name, 
	usm.unit_id as unit_id, 
	um.global_unit_name as unit_urn, 
	um.unit_alias as unit_alias, 
	vgacmsd.location_id as location_id, 
	lm.global_location_name , 
	lm.location_alias,
    vgacmsd.VALUE,
    vgacmsd.asofdatetime
FROM 
	vw_get_all_metric_summary_data vgacmsd
join 
	sensor_master sm  on sm.sensor_id = vgacmsd.sensor_id 
JOIN 
	unit_sensor_map usm on sm.sensor_id = usm.sensor_id 
JOIN 
	unit_master um on um.unit_id = usm.unit_id 
join 
	location_master lm on lm.location_id = vgacmsd.location_id 
    """


# register_post_relation_handlers(GenesisBase)
