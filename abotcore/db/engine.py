
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncTransaction,
    AsyncConnection,
    AsyncEngine
)

from sqlalchemy.orm import sessionmaker

from abotcore.config import DBSettings

from functools import lru_cache


Session = AsyncSession
Transaction = AsyncTransaction
Connection = AsyncConnection


@lru_cache()
def get_engine() -> AsyncEngine:
    '''Create and return a db engine using the config'''
    db_settings = DBSettings()
    return create_async_engine(
        db_settings.db_uri,
        pool_pre_ping=True
    )


@lru_cache()
def get_sessionmaker():
    '''Return a sessionmaker object that uses the above engine'''
    engine = get_engine()
    return sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        future=True
    )
