
from sqlalchemy import select
from sqlalchemy.engine.result import ScalarResult

from .session import Session


class ReadableMixin:
    @classmethod
    async def read_all(cls, session: Session) -> ScalarResult:
        return await session.scalars(select(cls))
