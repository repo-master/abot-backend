
from .base import Base


# Abstract Base model

class AbotBase(Base):
    __abstract__ = True
    __table_args__ = {'schema': 'abot'}
