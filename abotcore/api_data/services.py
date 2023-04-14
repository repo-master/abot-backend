
from fastapi import Depends

from abotcore.db import (
    get_session,
    Session,
    Transaction
)

from .models import (
    SensorData,
    Unit
)
from .schemas import (
    SensorDataOut
)

from typing import List


class SensorDataService:
    def __init__(self, session: Session = Depends(get_session)) -> None:
        self.async_session: Session = session

    async def get_sensor_data(self) -> List[SensorDataOut]:
        transaction: Transaction
        session : Session = self.async_session
        async with self.async_session.begin() as transaction:
            result = await SensorData.read_all(session)
            return [SensorDataOut.from_orm(x) for x in result.fetchall()]
