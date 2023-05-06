
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
    SensorDataIn,
    SensorDataOut,
    SensorMetadataOut
)

from datetime import datetime, timedelta, timezone
from typing import List, Tuple, Optional
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import io
import base64

from contextlib import asynccontextmanager


class SensorDataService:
    def __init__(self, session: Session = Depends(get_session)) -> None:
        self.async_session: Session = session

    async def get_sensor_metadata(self, sensor_id: int) -> Optional[SensorMetadataOut]:
        session: Session = self.async_session

        async with session.begin():
            meta_result = await session.execute(
                select(Sensor)
                .where(Sensor.sensor_id == sensor_id)
                .options(joinedload(Sensor.sensor_type, innerjoin=True))
            )

            meta_row: Optional[Tuple[Sensor]] = meta_result.fetchone()

            if meta_row:
                first_sensor_match = meta_row[0]  # FIXME: How do we get just one? Is this correct?
                return SensorMetadataOut(
                    sensor_urn=first_sensor_match.sensor_urn,
                    sensor_id=first_sensor_match.sensor_id,
                    sensor_type=first_sensor_match.sensor_type.type_name,
                    display_unit=first_sensor_match.sensor_type.default_unit,
                    sensor_name=first_sensor_match.sensor_name,
                    sensor_alias=first_sensor_match.sensor_alias
                )

    async def get_sensor_list(self) -> List[SensorMetadataOut]:
        session: Session = self.async_session

        async with session.begin():
            meta_result = await session.execute(
                select(Sensor)
                .options(joinedload(Sensor.sensor_type, innerjoin=True))
            )
            meta_rows: List[Tuple[Sensor]] = meta_result.fetchall()
            return [
                SensorMetadataOut(
                    sensor_urn=sensor_res[0].sensor_urn,
                    sensor_id=sensor_res[0].sensor_id,
                    sensor_type=sensor_res[0].sensor_type.type_name,
                    display_unit=sensor_res[0].sensor_type.default_unit,
                    sensor_name=sensor_res[0].sensor_name,
                    sensor_alias=sensor_res[0].sensor_alias
                )
                for sensor_res in meta_rows
            ]

    async def get_sensor_data(self,
                              sensor_id: int,
                              timestamp_from: Optional[datetime] = None,
                              timestamp_to: Optional[datetime] = None) -> List[SensorDataOut]:
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

        async with session.begin():
            sensor_data_query = select(SensorData) \
                .where(SensorData.sensor_id == sensor_id) \
                .where(and_(SensorData.timestamp >= timestamp_from, SensorData.timestamp <= timestamp_to))

            data_result = await session.scalars(sensor_data_query)
            sensor_data: List[SensorDataOut] = list(map(SensorDataOut.from_orm, data_result.fetchall()))

            return sensor_data

    async def insert_sensor_data(self, data: SensorDataIn):
        transaction: Transaction
        async with self.async_session.begin() as transaction:
            self.async_session.add(SensorData(**data.dict()))
            await self.async_session.commit()


class GraphPlotService:
    @asynccontextmanager
    async def plot_from_sensor_data(self, sensor_metadata: SensorMetadataOut, sensor_data: List[SensorDataOut]) -> Optional[io.BytesIO]:
        img_file = io.BytesIO()
        df = pd.DataFrame([x.__dict__ for x in sensor_data], index=None)

        try:
            if len(df) > 0:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.sort_values('timestamp', ascending=True, inplace=True)
                # We get a dictionary result in the 'value' column. We need to 'explode' it to separate columns.
                data_value_series = df['value'].apply(pd.Series)
                # Concatenate the data value columns to original df, remove the 'value' column from original
                df = pd.concat([df.drop(['value'], axis=1), data_value_series], axis=1)

                # Generate image plot
                img_file.name = "report_plot.png"
                self.plot_graph(img_file, df, x_axis='timestamp', y_axis='value', x_label="Timestamp",
                                y_label=f"{sensor_metadata.sensor_type} in {sensor_metadata.display_unit}", title=sensor_metadata.sensor_name)
                img_file.seek(0)
            else:
                # No data, so there is nothing to plot. Return None
                yield
            yield img_file
        finally:
            img_file.close()

    def plot_graph(self,
                   save_file: io.BytesIO,
                   df: pd.DataFrame,
                   x_axis,
                   y_axis,
                   x_label=None,
                   y_label=None,
                   title=None):
        # plot the data
        fig, ax = plt.subplots(figsize=(10, 5))
        if y_label is not None:
            ax.set_ylabel(y_label)
            ax.plot(df[x_axis], df[y_axis], label = y_label)
        else:
            ax.plot(df[x_axis], df[y_axis])

        # set the x-axis label and y-axis label
        if x_label is not None:
            ax.set_xlabel(x_label)


        # add title to the plot if provided
        if title is not None:
            ax.set_title(title)

        # format the tick labels on the x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
        for tick in ax.get_xticklabels():
            tick.set_rotation(30)
        ax.legend(loc='upper right', bbox_to_anchor=(1, 1.15))

        # adjust plot margins
        fig.subplots_adjust(top=0.88, left=0.11, bottom=0.3, right=0.9)

        # save plot as png image to memory buffer
        fig.savefig(save_file)
        # fig.savefig("my_plot.png") # Temp for reference

    def image_to_data_uri(self, img_file: io.BytesIO):
        # encode plot image buffer to base64 string
        img_mimetype = 'image/png'
        img_base64 = base64.b64encode(img_file.getvalue()).decode()

        return "data:%s;base64,%s" % (img_mimetype, img_base64)

        # with open("data/sample-graph.png", "rb") as img_file:
        #     img_data64 = base64.b64encode(img_file.read()).decode('utf-8')
        #     img_mimetype = 'image/png'
        #     uri = "data:%s;base64,%s" % (img_mimetype, img_data64)
        #     return uri
