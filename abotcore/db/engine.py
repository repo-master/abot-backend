
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncTransaction
from sqlalchemy.orm import sessionmaker

from decouple import config


# DB to connect to (from environment variable). Default is in-memory DB (content will be lost!)
DB_URI = config('DB_URL', default='sqlite+aiosqlite:///:memory:')

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
