"""DB models for use in Abot schemas"""

from datetime import datetime
from typing import Dict, List

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Identity,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from ..db.common_schemas import AbotBase


class Fulfillment(AbotBase):
    __tablename__ = "fulfillments"
    fulfillment_id: Mapped[int] = Column(
        "fulfillment_id", Integer, Identity(start=1), primary_key=True
    )
    endpoint_base_url: Mapped[str] = Column("endpoint_base_url", String)
    app_class: Mapped[str] = Column("app_class", String, nullable=True)
    friendly_name: Mapped[str] = Column("friendly_name", String, nullable=True)
    description: Mapped[str] = Column("description", String, nullable=True)
    version: Mapped[str] = Column("version", String, nullable=True)
    services: Mapped[List[Dict]] = Column("services", JSON, nullable=True)
    time_created: Mapped[datetime] = Column(
        "time_created", DateTime(timezone=True), server_default=func.now()
    )
    time_updated: Mapped[datetime] = Column(
        "time_updated", DateTime(timezone=True), onupdate=func.now()
    )
    time_last_sync: Mapped[datetime] = Column(
        "time_last_sync", DateTime(timezone=True), nullable=True
    )
