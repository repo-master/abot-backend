'''Implements services for the fake Genesis service'''

from xhtml2pdf import pisa
import base64
import os
import io
import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional, Tuple, Callable

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as pgo
from fastapi import Depends, HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import joinedload

from abotcore.db import Session, Transaction, get_session

from ..statistics.services import DataStatisticsService
from .models import (Sensor, SensorData, SensorStatus, SensorType, Unit,
                     UnitSensorMap)
from .schemas import (PlotlyFigure, SensorValue, SensorDataOut, SensorMetadataBase,
                      SensorMetadataOut, UnitMetadata, SensorStateOut, SensorHealthOut)


def TIME_LOCAL_NOW(): return datetime.now()
def TIME_LOCAL_PAST_24H(): return (datetime.now() - timedelta(hours=24))


class JSONEncodeData(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


def time_range_parameters(default_from_func: Callable[[], datetime] = TIME_LOCAL_PAST_24H,
                          default_to_func: Callable[[], datetime] = TIME_LOCAL_NOW):
    async def _wrapped_time_range_params(
            timestamp_from: Optional[datetime] = None,
            timestamp_to: Optional[datetime] = None) -> Tuple[datetime, datetime]:
        # Default date range - today all day
        if timestamp_from is None:
            timestamp_from = default_from_func()
        if timestamp_to is None:
            timestamp_to = default_to_func()
        return timestamp_from, timestamp_to

    return _wrapped_time_range_params


class SensorDataService:
    def __init__(self, session: Session = Depends(get_session)) -> None:
        self.async_session: Session = session

    @staticmethod
    def create_sensor_metadata(result: Tuple[Sensor, Unit, SensorStatus]) -> SensorMetadataOut:
        return SensorMetadataOut(
            sensor_urn=result[0].sensor_urn,
            sensor_id=result[0].sensor_id,
            sensor_type=result[0].sensor_type.type_name,
            display_unit=result[0].sensor_type.default_unit,
            sensor_name=result[0].sensor_name,
            sensor_alias=result[0].sensor_alias,
            sensor_location=UnitMetadata.from_orm(result[1]) if result[1] else None,
            sensor_status=SensorStateOut.from_orm(result[2]) if result[2] else None
        )

    async def get_sensor_metadata(self, sensor_id: int) -> Optional[SensorMetadataOut]:
        session: Session = self.async_session

        meta_result = await session.execute(
            select(Sensor, Unit, SensorStatus)
            .join(UnitSensorMap, UnitSensorMap.sensor_id == Sensor.sensor_id, isouter=True)
            .join(Unit, Unit.unit_id == UnitSensorMap.unit_id, isouter=True)
            .join(SensorStatus, isouter=True)
            .where(Sensor.sensor_id == sensor_id)
            .options(
                joinedload(Sensor.sensor_type, innerjoin=True)
            )
        )

        meta_row: Optional[Tuple[Sensor, Unit, SensorStatus]] = meta_result.fetchone()

        if meta_row:
            return self.create_sensor_metadata(meta_row)

    async def get_sensor_list(self) -> List[SensorMetadataOut]:
        session: Session = self.async_session

        meta_result = await session.execute(
            select(Sensor, Unit, SensorStatus)
            .join(UnitSensorMap, UnitSensorMap.sensor_id == Sensor.sensor_id, isouter=True)
            .join(Unit, Unit.unit_id == UnitSensorMap.unit_id, isouter=True)
            .join(SensorStatus, isouter=True)
            .options(joinedload(Sensor.sensor_type, innerjoin=True))
        )
        meta_rows: List[Tuple[Sensor, Unit, SensorStatus]] = meta_result.fetchall()

        # Wrap rows into `SensorMetadataOut` objects
        return list(map(self.create_sensor_metadata, meta_rows))

    async def get_sensor_data(self,
                              sensor_id: int,
                              timestamp_from: datetime,
                              timestamp_to: datetime) -> List[SensorDataOut]:
        session: Session = self.async_session

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

    async def insert_sensor_data(self, data: SensorData):
        self.async_session.add(SensorData(**data.dict()))
        await self.async_session.commit()

    # TODO: Query by only single string
    async def query_sensor(self,
                           sensor_type: Optional[str],
                           sensor_name: Optional[str],
                           location: Optional[str]) -> List[SensorMetadataOut]:
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

        input_check = False
        # Construct a query that can search with given parameters, some optional

        sensor_id_search_query = select(Sensor, Unit, SensorStatus, UnitSensorMap) \
            .join(Unit) \
            .join(Sensor) \
            .join(SensorType) \
            .join(SensorStatus, isouter=True)

        if sensor_type is not None and sensor_type != "":
            input_check = True
            sensor_id_search_query = sensor_id_search_query.where(
                SensorType.type_name == sensor_type.lower()
            )

        if location is not None and location != "":
            input_check = True
            loc_sanitized = "%{}%".format(location.strip())
            sensor_id_search_query = sensor_id_search_query.where(
                or_(Unit.unit_alias.ilike(loc_sanitized), Unit.unit_urn.ilike(loc_sanitized))
            )

        if sensor_name is not None and sensor_name != "":
            input_check = True
            name_sanitized = "%{}%".format(sensor_name.strip())
            sensor_id_search_query = sensor_id_search_query.where(
                or_(Sensor.sensor_alias.ilike(name_sanitized), Sensor.sensor_name.ilike(name_sanitized))
            )

        if not input_check:
            raise HTTPException(403, "Neither sensor name nor sensor type was provided.")

        sensor_search_query = sensor_id_search_query.options(
            joinedload(UnitSensorMap.sensor),
            joinedload(UnitSensorMap.unit),
            joinedload(Sensor.sensor_type, innerjoin=True)
        )

        # TODO: Sort by some method (closest match, location, geohash, etc.)

        sensor_search_result = await session.execute(
            sensor_search_query
        )

        sensor_rows: List[Tuple[Sensor, Unit, SensorStatus, UnitSensorMap]] = sensor_search_result.fetchall()

        if len(sensor_rows) == 0:
            raise HTTPException(400, detail="Sensor not found")

        return list(map(self.create_sensor_metadata, sensor_rows))


class UnitService:
    def __init__(self, session: Session = Depends(get_session)) -> None:
        self.async_session: Session = session

    async def get_unit_metadata(self, unit_id: int) -> Optional[UnitMetadata]:
        session: Session = self.async_session

        meta_result = await session.execute(
            select(Unit)
            .where(Unit.unit_id == unit_id)
        )

        meta_row: Optional[Tuple[Unit]] = meta_result.fetchone()

        if meta_row:
            first_unit_match, = meta_row
            return UnitMetadata.from_orm(first_unit_match)

    async def get_unit_list(self) -> List[UnitMetadata]:
        session: Session = self.async_session

        meta_result = await session.execute(
            select(Unit)
        )
        meta_rows: List[Tuple[Unit]] = meta_result.fetchall()
        return list(map(UnitMetadata.from_orm, [x[0] for x in meta_rows]))


class GraphPlotService:
    @asynccontextmanager
    async def plot_from_sensor_data(self, sensor_metadata: SensorMetadataBase, sensor_data: List[SensorDataOut]) -> Optional[io.BytesIO]:
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
                yield img_file
            else:
                # No data, so there is nothing to plot. Return None
                yield
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
                   lower_threshold=None,
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
        if not outliers.empty:
            ax.plot(outliers[x_axis], outliers[y_axis], label="outlier", marker='o', linestyle='None')

        if lower_threshold is None:
            if not outliers.empty:
                threshold = np.full(len(df[x_axis]), outliers['lower_threshold'][0])
                ax.plot(df[x_axis], threshold, linestyle="dashdot", color="red", alpha=0.4, label="Lower threshold")

        if higher_threshold is None:
            if not outliers.empty:
                threshold = np.full(len(df[x_axis]), outliers['higher_threshold'][0])
                ax.plot(df[x_axis], threshold, linestyle="dashdot", color="red", alpha=0.4, label="Upper threshold")

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
                                      sensor_metadata: SensorMetadataBase,
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
            return self.plot_sensor_graph(df, 'timestamp', 'value', 'Timestamp', f"{sensor_metadata.sensor_type} in {sensor_metadata.display_unit}", sensor_metadata.sensor_name)
        else:
            # No data, so there is nothing to plot. Return None
            return None

    async def plot_from_sensor_data_json(self,
                                         sensor_metadata: SensorMetadataBase,
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
                          lower_threshold=None,
                          higher_threshold=None) -> pgo.Figure:

        # Create traces
        fig = pgo.Figure()
        fig.add_trace(pgo.Scatter(x=df[x_axis], y=df[y_axis],
                                  mode='lines',
                                  name='y_axis'))
        if x_label is not None:
            fig.update_layout(xaxis_title=x_label)

        # set the x-axis label and y-axis label
        if y_label is not None:
            fig.update_layout(yaxis_title=y_label)
            fig.data[0].name = y_label
        # add title to the plot if provided
        if title is not None:
            fig.update_layout(title=title)

        outliers = DataStatisticsService.data_get_outliers(df.set_index(x_axis)[y_axis])

        if not outliers.empty:
            fig.add_trace(pgo.Scatter(x=outliers[x_axis], y=outliers[y_axis],
                                      mode='markers', name='outlier'))

        thresh_default_lower, thresh_default_upper = DataStatisticsService.get_quantile_threshold(
            df.set_index(x_axis)[
            y_axis]
        )

        if lower_threshold is None:
            lower_threshold = thresh_default_lower

        threshold_array_lower = np.full(len(df[x_axis]), lower_threshold)
        fig.add_trace(pgo.Scatter(x=df[x_axis], y=threshold_array_lower, line=dict(
            color="pink",
            width=1,
            dash="dashdot"
        ), name="Lower threshold"))

        if higher_threshold is None:
            higher_threshold = thresh_default_upper

        threshold_array_upper = np.full(len(df[x_axis]), higher_threshold)
        fig.add_trace(pgo.Scatter(x=df[x_axis], y=threshold_array_upper, line=dict(
            color="blue",
            width=1,
            dash="dashdot"
        ),
            name="Upper threshold"))

        return fig


class GraphConvertService:
    def _convert_pdf(fig: pgo.Figure, dest_file):
        pisa.CreatePDF(fig.to_html(), dest=dest_file)

    CONVERTERS = {
        'pdf': _convert_pdf
    }

    @asynccontextmanager
    async def convert(self, fig: pgo.Figure, format: str = 'pdf', filename: Optional[str] = None, auto_close: bool = True):
        io_file = io.BytesIO()
        cvt = self.CONVERTERS.get(format)
        try:
            if cvt:
                cvt(fig, io_file)
                if filename:
                    io_file.name = os.path.extsep.join([filename, format])
                io_file.seek(0)
                yield io_file
            else:
                yield # No content, so yield None
        finally:
            if auto_close:
                io_file.close()
