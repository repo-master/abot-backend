"""Data validation schemas (Pydantic) used by chat endpoints"""

from pydantic import BaseModel, Extra, Field
from typing import Optional, Dict, List, Any
from enum import Enum

# Base


class ChatButton(BaseModel):
    title: str
    payload: str


class ChatMessage(BaseModel, extra=Extra.forbid):
    text: str


class ChatMessageIn(ChatMessage):
    """
    Represents a message sent by the user (only text is allowed).
    Content is given as input to a `UserMessage` class instance
    """

    sender_id: Optional[str] = None


class ChatMessageOut(
    ChatMessage, extra=Extra.ignore, allow_population_by_field_name=True
):
    recipient_id: str
    text: Optional[str] = Field(alias="output")
    image: Optional[str] = None
    buttons: Optional[List[ChatButton]] = None
    attachment: Optional[str] = None
    custom: Optional[Dict[str, Any]] = None


class RestEndpointStatus(Enum):
    OK = "ok"
    UNREACHABLE = "unreachable"


class ChatRole(Enum):
    HUMAN = ("human",)
    AI = "ai"


class ChatStatusOut(BaseModel):
    status: RestEndpointStatus


class MemoryData(BaseModel):
    content: str
    additional_kwargs: dict[str, Any]


class Memory(BaseModel):
    type: str
    data: MemoryData
