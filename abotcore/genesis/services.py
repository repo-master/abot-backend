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
from fastapi import Depends, HTTPException
from sqlalchemy import and_, or_, select 
from sqlalchemy import text, literal_column
from sqlalchemy.orm import joinedload

from abotcore.db_gen import Session, Transaction, get_session

from ..statistics.services import DataStatisticsService
from .models import (Sensor, Unit, UnitSensorMap , VWSensorStatus)
from .schemas import (PlotlyFigure,  SensorMetadataBase, SensorStatus,SensorHealthOut,SensorStateOut,SensorDataOut,
                      SensorMetadataOut, UnitMetadata)

SENSOR_TYPE_TABLE = {
    'Temperature' : 'verna_w1_temp_summary_metric',
    'Humidity' : 'verna_w1_rh_summary_metric'
}

class JSONEncodeData(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

class SensorDataService:
    def __init__(self, session : Session = Depends(get_session)) -> None:
        self.async_session: Session = session
    
    @staticmethod
    def create_sensor_metadata(result) :
        # TODO better way to do it (like from ORM)
        if result[8] and result[9] :
            unit_metadata = UnitMetadata(
                unit_urn=result[9],
                unit_id=result[8],
                unit_alias=result[10]
            )
        else: 
            unit_metadata= None
            
        if result[11] and result[12]:
            sensor_status = SensorStateOut(
                #TODO  value dict is hard coded right now will have to update for state and other stuff
                last_value={"value":result[11]},
                last_timestamp=result[12],
                sensor_health=SensorHealthOut(code_name = result[7])
            )
        else: 
            sensor_status = None


        return SensorMetadataOut(
            sensor_urn=result[1],
            sensor_id=result[0],
            sensor_name=result[2],
            sensor_alias=result[2],
            sensor_type=result[3],
            display_unit=result[6],     
            sensor_location = unit_metadata,
            sensor_status=sensor_status   
            )


    async def get_sensor_metadata(self, sensor_id: int) -> Optional[SensorMetadataOut]:
        session: Session = self.async_session        

        query = VWSensorStatus.query+f' where sm.sensor_id={sensor_id}'

        meta_result = await session.execute(text(query))
        meta_rows = meta_result.fetchone()
        try:
            return self.create_sensor_metadata(meta_rows)
        except IndexError:
            return None

    async def get_sensor_list(self) -> List[SensorMetadataOut]:
        session: Session = self.async_session        

        meta_result = await session.execute(
            text(VWSensorStatus.query)
        )

        meta_rows = meta_result.fetchall()
        return list(map(self.create_sensor_metadata, meta_rows))

    async def get_sensor_data(self,
                              sensor_id: int,
                              sensor_type : str,
                              timestamp_from: Optional[datetime] = None,
                              timestamp_to: Optional[datetime] = None) :
        session: Session = self.async_session

        # Default date range - today all day
        if timestamp_from is None:
            timestamp_from = datetime.now() - timedelta(days=1200)#timedelta(hours=240000)
        if timestamp_to is None:
            timestamp_to = datetime.now()

        # # Database has timestamp stored as timezone-naive format [timestamp without timezone] in UTC, so:
        # # - Convert the given timestamp to UTC from whatever TZ it was
        # # - Strip the timezone information to match the DB schema
        timestamp_from = timestamp_from.astimezone(timezone.utc).replace(tzinfo=None)
        timestamp_to = timestamp_to.astimezone(timezone.utc).replace(tzinfo=None)

        table_name = SENSOR_TYPE_TABLE[sensor_type]
        query = f"select * from {table_name} where sensor_id = {sensor_id} and sensor_data_calc_ts between '{timestamp_from}' and '{timestamp_to}'"
        data_result = await session.execute(text(query))

        result_list = []

        for row in data_result:
            if row.temp_avg_15min:
                data_item = SensorDataOut(
                        timestamp = row.sensor_data_calc_ts.strftime("%Y-%m-%dT%H:%M:%S.%f"),
                        sensor_id = row.sensor_id,
                        value = {"value": row.temp_avg_15min}
                )
            result_list.append(data_item)

        return result_list

    async def query_sensor(self,
                           sensor_type: Optional[str],
                           sensor_name: Optional[str],
                           location: Optional[str]) -> List[SensorMetadataOut]:
        session: Session = self.async_session

        # # FIXME: This is incorrect. There should be fallback methods.
        # '''
        # try:
        #     sensor_type_id = await self.get_sensor_type(sensor_type=sensor_type)
        # except TypeError:
        #     # TODO: ???? What is this
        #     return None, "Sensor type does not exist need to raise error"
        # try:
        #     unit_id = await self.get_unit_id(location)
        # except TypeError:
        #     # TODO: This too, what to do here?????
        #     return None, "Unit Does not exist need to raise error"
        # '''

        input_check = False
        # # Construct a query that can search with given parameters, some optional
        sensor_id_search_query = VWSensorStatus.query

        filter_query = []


        if sensor_type is not None and sensor_type != "":
            input_check = True
            filter_query.append(f" sm.sensor_type like '{sensor_type.lower()}'")

        if location is not None and location != "":
            input_check = True
            loc_sanitized = "%{}%".format(location.strip())
            filter_query.append(f" um.global_unit_name like '{loc_sanitized}'")            

        if sensor_name is not None and sensor_name != "":
            input_check = True
            name_sanitized = "%{}%".format(sensor_name.strip())
            filter_query.append(f" sm.global_sensor_name like '{name_sanitized}'")
        
        if input_check:
            sensor_id_search_query = sensor_id_search_query + f" where {filter_query[0]}"
            for i in filter_query[1::]:
                sensor_id_search_query = sensor_id_search_query + f" and {i}"

        if not input_check:
            raise HTTPException(403, "Neither sensor name nor sensor type was provided.")

        # # TODO: Sort by some method (closest match, location, geohash, etc.)

        sensor_search_result = await session.execute(
            text(sensor_id_search_query)
        )

        sensor_rows: List[Tuple[Sensor, Unit,  UnitSensorMap]] = sensor_search_result.fetchall()

        if len(sensor_rows) == 0:
            raise HTTPException(400, detail="Sensor not found")

        return list(map(self.create_sensor_metadata, sensor_rows))


class UnitService:
    def __init__(self, session: Session = Depends(get_session)) -> None:
        self.async_session: Session = session

    @staticmethod
    def create_unit_metadata(result):
        return UnitMetadata(
            unit_id=result[0],
            unit_urn=result[1],
            unit_alias=result[2]
        )

    async def get_unit_metadata(self, unit_id: int) -> Optional[UnitMetadata]:
        session: Session = self.async_session

        session: Session = self.async_session

        meta_result = await session.execute( text(Unit.query + f" where unit_id = {unit_id}"))
        meta_rows = meta_result.fetchone()
        return self.create_unit_metadata(meta_rows)

    async def get_unit_list(self) -> List[UnitMetadata]:
        session: Session = self.async_session

        meta_result = await session.execute( text(Unit.query))
        meta_rows = meta_result.fetchall()
        return list(map(self.create_unit_metadata, meta_rows))




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
                df = pd.concat([df.drop(['value'], axis=1), data_value_series.astype(float)], axis=1)
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
            df = pd.concat([df.drop(['value'], axis=1), data_value_series.astype(float)], axis=1)
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

        if lower_threshold is None:
            if not outliers.empty:
                threshold_array = np.full(len(df[x_axis]), outliers['lower_threshold'][0])
                fig.add_trace(pgo.Scatter(x=df[x_axis], y=threshold_array, line=dict(
                    color="pink",
                    width=1,
                    dash="dashdot"
                ),
                    name="Lower threshold"))
                

        if higher_threshold is None:
            if not outliers.empty:
                threshold_array = np.full(len(df[x_axis]), outliers['higher_threshold'][0])
                fig.add_trace(pgo.Scatter(x=df[x_axis], y=threshold_array, line=dict(
                    color="blue",
                    width=1,
                    dash="dashdot"
                ),
                    name="Upper threshold"))

        return fig
