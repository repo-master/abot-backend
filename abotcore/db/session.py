
from typing import AsyncIterator

from sqlalchemy.exc import SQLAlchemyError

from .engine import get_sessionmaker, Session

import logging


LOG = logging.getLogger(__name__)


async def get_session() -> AsyncIterator[Session]:
    '''Returns sessionmaker when it is available'''
    db: Session = None
    try:
        sessionmaker = get_sessionmaker()
        db = sessionmaker()
        yield db
    except SQLAlchemyError as e:
        LOG.exception(e)
    finally:
        if db:
            await db.close()
