
import logging
from typing import AsyncIterator

from sqlalchemy.exc import SQLAlchemyError

from .engine import Session, get_sessionmaker

LOG = logging.getLogger(__name__)


async def get_session() -> AsyncIterator[Session]:
    '''Returns sessionmaker when it is available'''
    db: Session

    try:
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as db:
            yield db
    except SQLAlchemyError:
        LOG.exception("Failed to create SQLaAlchemy session:")
