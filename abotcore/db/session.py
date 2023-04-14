
from typing import AsyncIterator

from sqlalchemy.exc import SQLAlchemyError

from .engine import sessionmaker_async, Session

import logging


LOG = logging.getLogger(__name__)


async def get_session() -> AsyncIterator[Session]:
    '''Returns sessionmaker when it is available'''
    db: Session = None
    try:
        db = sessionmaker_async()
        yield db
    except SQLAlchemyError as e:
        LOG.exception(e)
    finally:
        if db:
            await db.close()
