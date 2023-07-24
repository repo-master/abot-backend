"""DB models used by chat endpoints"""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Identity, Integer, String, Enum, select
from sqlalchemy.orm import Mapped
from sqlalchemy.sql import func

from ..db.common_schemas import AbotBase
from ..db.session import Session
from .schemas import Memory, ChatRole

from typing import List


class ChatHistory(AbotBase):
    __tablename__ = "chat_history"
    chat_message_id: Mapped[int] = Column(
        "chat_message_id", Integer, Identity(start=1), primary_key=True
    )
    chat_handler: Mapped[str] = Column("chat_handler", String)
    message_client_id: Mapped[str] = Column("message_client_id", String, nullable=True)
    message_role: Mapped[ChatRole] = Column(
        "message_role", Enum(ChatRole), default=ChatRole.HUMAN
    )
    message_content: Mapped[str] = Column("message_content", String, nullable=True)
    message_time: Mapped[datetime] = Column(
        "message_time", DateTime(timezone=True), server_default=func.now()
    )
    time_created: Mapped[datetime] = Column(
        "time_created", DateTime(timezone=True), server_default=func.now()
    )
    time_updated: Mapped[datetime] = Column(
        "time_updated", DateTime(timezone=True), onupdate=func.now()
    )

    @classmethod
    async def latest_message(cls, session: Session, client_id: str):
        return await session.scalar(
            select(ChatHistory)
            .filter(ChatHistory.message_client_id == client_id)
            .order_by(ChatHistory.message_time.desc())
            .limit(1)
        )


class UserChatMemory(AbotBase):
    __tablename__ = "user_chat_memory"
    user_id: Mapped[str] = Column("user_id", String, primary_key=True)
    memory_data: Mapped[List[Memory]] = Column("memory_data", JSON, default=[])
    time_created: Mapped[datetime] = Column(
        "time_created", DateTime(timezone=True), server_default=func.now()
    )
    time_updated: Mapped[datetime] = Column(
        "time_updated", DateTime(timezone=True), onupdate=func.now()
    )
