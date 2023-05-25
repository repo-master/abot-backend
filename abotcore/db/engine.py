
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

from typing import Optional, Dict


Session = AsyncSession
Transaction = AsyncTransaction
Connection = AsyncConnection


@lru_cache()
def get_engine() -> AsyncEngine:
    '''Create and return a db engine using the config'''
    db_settings = DBSettings()
    schema_mapping = get_schema_mapping()

    return create_async_engine(
        db_settings.db_uri,
        pool_pre_ping=True,
        execution_options={
            "schema_translate_map": schema_mapping
        }
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

@lru_cache()
def get_schema_mapping() -> Dict[str, str]:
    db_settings = DBSettings()
    if db_settings.db_schema_map:
        return dict(mapping.split(':') for mapping in db_settings.db_schema_map)
    return {}
