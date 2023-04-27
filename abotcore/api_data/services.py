
import base64

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
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import io
import base64


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
    async def plot_from_sensor_data(self, sensor_metadata: SensorMetadataOut, sensor_data: SensorDataOut) -> str:
        df = pd.DataFrame([s.__dict__ for s in sensor_data])
        df['value'] = [x['value'] for x in df['value']]
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        graph_image = self.plot_graph(df, x_axis='timestamp', y_axis='value', x_label="Timestamp", y_label="Value",title=sensor_metadata.sensor_name)
        return graph_image


    def plot_graph(self, df, x_axis, y_axis, x_label=None, y_label=None, title=None):
        # plot the data
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df[x_axis], df[y_axis])
        
        # set the x-axis label and y-axis label
        if x_label is not None:
            ax.set_xlabel(x_label)

        if y_label is not None:
            ax.set_ylabel(y_label)
        
        # add title to the plot if provided
        if title is not None:
            ax.set_title(title)
        
        # format the tick labels on the x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
        for tick in ax.get_xticklabels():
            tick.set_rotation(30)
            
        # adjust plot margins
        fig.subplots_adjust(top=0.88, left=0.11, bottom=0.3, right=0.9)
        
        # save plot as png image to memory buffer
        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format='png') 
        # fig.savefig("my_plot.png")#Temp for reffrence
        img_buffer.seek(0)
        
        # encode plot image buffer to base64 string
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        # clear the buffer
        img_buffer.truncate(0)
            
        return img_base64
        # with open("data/sample-graph.png", "rb") as img_file:
        #     img_data64 = base64.b64encode(img_file.read()).decode('utf-8')
        #     img_mimetype = 'image/png'
        #     uri = "data:%s;base64,%s" % (img_mimetype, img_data64)
        #     return uri
