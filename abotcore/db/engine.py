
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncTransaction
from sqlalchemy.orm import sessionmaker

from abotcore.config import DB_URI


Session = AsyncSession
Transaction = AsyncTransaction

async_engine = create_async_engine(
    DB_URI,
    pool_pre_ping=True
)

sessionmaker_async = sessionmaker(
    bind=async_engine,
    class_=Session,
    autoflush=False,
    future=True
)
