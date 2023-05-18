'''Implements services for the fake Genesis service'''

import base64
import io
import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional, Tuple

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as pgo
from fastapi import Depends
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import joinedload

from abotcore.db import Session, Transaction, get_session

from ..statistics.services import DataStatisticsService
from .models import Sensor, SensorData, SensorType, Unit, UnitSensorMap
from .schemas import (SensorDataIn, SensorDataOut, SensorMetadataLocationOut,
                      SensorMetadataOut, UnitMetadataOut, PlotlyFigure)


class JSONEncodeData(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, np.ndarray):
            return o.tolist()
        return super().default(o)


class SensorDataService:
    def __init__(self, session: Session = Depends(get_session)) -> None:
        self.async_session: Session = session

    async def get_sensor_metadata(self, sensor_id: int) -> Optional[SensorMetadataLocationOut]:
        session: Session = self.async_session

        meta_result = await session.execute(
            select(Sensor, Unit)
            .join(UnitSensorMap, UnitSensorMap.sensor_id == Sensor.sensor_id)
            .join(Unit, Unit.unit_id == UnitSensorMap.unit_id)
            .where(Sensor.sensor_id == sensor_id)
            .options(joinedload(Sensor.sensor_type, innerjoin=True))
        )

        # meta_row: Optional[Tuple[Sensor]] = meta_result.fetchone()


        meta_row: List[Tuple[Sensor, Unit]] = meta_result.fetchall()[0]
        print(meta_row)
        return SensorMetadataLocationOut(
                sensor_urn=meta_row[0].sensor_urn,
                sensor_id=meta_row[0].sensor_id,
                sensor_type=meta_row[0].sensor_type.type_name,
                display_unit=meta_row[0].sensor_type.default_unit,
                sensor_name=meta_row[0].sensor_name,
                sensor_alias=meta_row[0].sensor_alias,
                sensor_location=UnitMetadataOut(
                    unit_id=meta_row[1].unit_id,
                    unit_urn=meta_row[1].global_unit_name,
                    unit_alias=meta_row[1].unit_alias
                )
        )


        # if meta_row:
        #     first_sensor_match, = meta_row
        #     return SensorMetadataLocationOut(
        #         sensor_urn=first_sensor_match.sensor_urn,
        #         sensor_id=first_sensor_match.sensor_id,
        #         sensor_type=first_sensor_match.sensor_type.type_name,
        #         display_unit=first_sensor_match.sensor_type.default_unit,
        #         sensor_name=first_sensor_match.sensor_name,
        #         sensor_alias=first_sensor_match.sensor_alias,
        #         sensor_location = 
        #     )

    async def get_sensor_list(self) -> List[SensorMetadataLocationOut]:
        session: Session = self.async_session

        meta_result = await session.execute(
            select(Sensor, Unit)
            .join(UnitSensorMap, UnitSensorMap.sensor_id == Sensor.sensor_id)
            .join(Unit, Unit.unit_id == UnitSensorMap.unit_id)
            .options(joinedload(Sensor.sensor_type, innerjoin=True))
        )
        meta_rows: List[Tuple[Sensor, Unit]] = meta_result.fetchall()

        # Wrap rows into `SensorMetadataLocationOut` objects
        return [
            SensorMetadataLocationOut(
                sensor_urn=sensor_res[0].sensor_urn,
                sensor_id=sensor_res[0].sensor_id,
                sensor_type=sensor_res[0].sensor_type.type_name,
                display_unit=sensor_res[0].sensor_type.default_unit,
                sensor_name=sensor_res[0].sensor_name,
                sensor_alias=sensor_res[0].sensor_alias,
                sensor_location=UnitMetadataOut(
                    unit_id=sensor_res[1].unit_id,
                    unit_urn=sensor_res[1].global_unit_name,
                    unit_alias=sensor_res[1].unit_alias
                )
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

        sensor_data_query = select(SensorData) \
            .where(SensorData.sensor_id == sensor_id) \
            .where(and_(SensorData.timestamp >= timestamp_from, SensorData.timestamp <= timestamp_to))

        data_result = await session.scalars(sensor_data_query)
        sensor_data: List[SensorDataOut] = list(map(SensorDataOut.from_orm, data_result.fetchall()))

        return sensor_data

    async def insert_sensor_data(self, data: SensorDataIn):
        self.async_session.add(SensorData(**data.dict()))
        await self.async_session.commit()

    async def query_sensor(self,
                            sensor_type: Optional[str],
                            sensor_name: Optional[str],
                            location: Optional[str]) -> Optional[SensorMetadataLocationOut]:
        session: Session = self.async_session

        # FIXME: This is incorrect. There should be fallback methods.
        '''
        try:
            sensor_type_id = await self.get_sensor_type(sensor_type=sensor_type)
        except TypeError:
            # TODO: ???? What is this
            return None, "Sensor type does not exist need to raise error"
        try:
            unit_id = await self.get_unit_id(location)
        except TypeError:
            # TODO: This too, what to do here?????
            return None, "Unit Does not exist need to raise error"
        '''

        # Construct a query that can search with given parameters, some optional

        sensor_id_search_query = select(UnitSensorMap) \
            .join(Unit) \
            .join(Sensor) \
            .join(SensorType)

        if sensor_type != "":
            sensor_id_search_query = sensor_id_search_query.where(
                SensorType.type_name == sensor_type.lower()
            )

        if location != "":
            loc_sanitized = "%{}%".format(location.strip())
            sensor_id_search_query = sensor_id_search_query.where(
                or_(Unit.unit_alias.ilike(loc_sanitized), Unit.global_unit_name.ilike(loc_sanitized))
            )
       
        if sensor_name != "":
            name_sanitized = "%{}%".format(sensor_name.strip())
            sensor_id_search_query = sensor_id_search_query.where(
                or_(Sensor.sensor_alias.ilike(name_sanitized), Sensor.sensor_name.ilike(name_sanitized))
            )

        sensor_id_search_query = sensor_id_search_query.options(
            joinedload(UnitSensorMap.sensor),
            joinedload(UnitSensorMap.unit)
        )

        # TODO: Sort by some method (closest match, location, geohash, etc.)

        sensor_id_result = await session.execute(
            sensor_id_search_query
        )

        sensor_id_row: Optional[Tuple[UnitSensorMap]] = sensor_id_result.fetchone()

        if sensor_id_row:
            sensor_id = sensor_id_row[0].sensor_id
            metadata = await self.get_sensor_metadata(sensor_id)
            return metadata


class UnitService:
    def __init__(self, session: Session = Depends(get_session)) -> None:
        self.async_session: Session = session

    async def get_unit_metadata(self, unit_id: int) -> Optional[UnitMetadataOut]:
        session: Session = self.async_session

        meta_result = await session.execute(
            select(Unit)
            .where(Unit.unit_id == unit_id)
        )

        meta_row: Optional[Tuple[Unit]] = meta_result.fetchone()

        if meta_row:
            first_unit_match, = meta_row
            return UnitMetadataOut(
                unit_urn=first_unit_match.global_unit_name,
                unit_id=first_unit_match.unit_id,
                unit_alias=first_unit_match.unit_alias
            )

    async def get_unit_list(self) -> List[UnitMetadataOut]:
        session: Session = self.async_session

        meta_result = await session.execute(
            select(Unit)
        )
        meta_rows: List[Tuple[Unit]] = meta_result.fetchall()
        return [
            UnitMetadataOut(
                unit_urn=unit_res[0].global_unit_name,
                unit_id=unit_res[0].unit_id,
                unit_alias=unit_res[0].unit_alias
            )
            for unit_res in meta_rows
        ]


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
                   title=None,
                   lower_threshold= None,
                   higher_threshold=None):
        # plot the data
        fig, ax = plt.subplots(figsize=(10, 5))
        if y_label is not None:
            ax.set_ylabel(y_label)
            ax.plot(df[x_axis], df[y_axis], label=y_label)
        else:
            ax.plot(df[x_axis], df[y_axis])

        # ploting outliers on chart
        outliers = DataStatisticsService.data_get_outliers(df.set_index(x_axis)[y_axis])
        ax.plot(outliers[x_axis], outliers[y_axis], label = "outlier", marker='o',linestyle='None')

        if lower_threshold is None:
            threshold = np.full(len(df[x_axis]), outliers['lower_threshold'][0])
            ax.plot(df[x_axis], threshold,linestyle="dashdot",color="red", alpha=0.4, label="lower_threshold")
        
        if higher_threshold is None:
            threshold = np.full(len(df[x_axis]), outliers['higher_threshold'][0])
            ax.plot(df[x_axis], threshold, linestyle="dashdot",color="red", alpha=0.4, label="higher_threshold")

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
        ax.legend(loc='upper right', bbox_to_anchor=(0, -0.1))

        # adjust plot margins
        fig.subplots_adjust(top=0.88, left=0.2, bottom=0.3, right=.95)

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

class InteractiveGraphService:
    async def figure_from_sensor_data(self,
                                    sensor_metadata: SensorMetadataOut,
                                    sensor_data: List[SensorDataOut]) -> Optional[pgo.Figure]:
        df = pd.DataFrame([x.__dict__ for x in sensor_data], index=None)
        if len(df) > 0:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.sort_values('timestamp', ascending=True, inplace=True)
            # We get a dictionary result in the 'value' column. We need to 'explode' it to separate columns.
            data_value_series = df['value'].apply(pd.Series)
            # Concatenate the data value columns to original df, remove the 'value' column from original
            df = pd.concat([df.drop(['value'], axis=1), data_value_series], axis=1)

            # Generate plotly chart
            return self.plot_sensor_graph(df, 'timestamp', 'value' , 'Timestamp', f"{sensor_metadata.sensor_type} in {sensor_metadata.display_unit}", sensor_metadata.sensor_name
                # TODO
            )
        else:
            # No data, so there is nothing to plot. Return None
            return None

    async def plot_from_sensor_data_json(self,
                                    sensor_metadata: SensorMetadataOut,
                                    sensor_data: List[SensorDataOut]) -> Optional[PlotlyFigure]:
        fig = await self.figure_from_sensor_data(sensor_metadata, sensor_data)
        if fig:
            return fig.to_dict()
        return None

    def plot_sensor_graph(self,
                    df: pd.DataFrame,
                    x_axis,
                    y_axis,
                    x_label=None,
                    y_label=None,
                    title=None,
                    lower_threshold= None,
                    higher_threshold=None) -> pgo.Figure:



        # Create traces
        fig = pgo.Figure()
        fig.add_trace(pgo.Scatter(x=df[x_axis], y=df[y_axis],
                            mode='lines',
                            name='y_axis'))
        if x_label is not None:
            fig.update_layout(xaxis_title=x_label )


        # set the x-axis label and y-axis label
        if y_label is not None:
            fig.update_layout(yaxis_title=y_label)
            fig.data[0].name = y_label        
        # add title to the plot if provided
        if title is not None:
            fig.update_layout(title=title)

        outliers = DataStatisticsService.data_get_outliers(df.set_index(x_axis)[y_axis])

        fig.add_trace(pgo.Scatter(x=outliers[x_axis], y=outliers[y_axis],
                            mode='markers', name='outlier'))


        if lower_threshold is None:
            threshold_array = np.full(len(df[x_axis]), outliers['lower_threshold'][0])
            fig.add_trace(pgo.Scatter(x=df[x_axis] , y=threshold_array, line=dict(
            color="pink",
            width=1,
            dash="dashdot"
        ),
        name="lower_threshold"))
        
        if higher_threshold is None:
            threshold_array = np.full(len(df[x_axis]), outliers['higher_threshold'][0])
            fig.add_trace(pgo.Scatter(x=df[x_axis] , y=threshold_array, line=dict(
            color="blue",
            width=1,
            dash="dashdot"
        ),
        name="higher_threshold"))



        return fig
