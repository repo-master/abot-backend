'''Data validation schemas (Pydantic) used by chat endpoints'''

from pydantic import BaseModel, Extra
from typing import Optional, Union, Dict, List, Any
from enum import Enum

# Base


class ChatMessage(BaseModel, extra=Extra.forbid):
    text: str


class ChatMessageIn(ChatMessage):
    '''
    Represents a message sent by the user (only text is allowed).
    Content is given as input to a `UserMessage` class instance
    '''
    sender_id: Optional[str] = None


class ChatMessageOut(ChatMessage):
    recipient_id: str
    text: Optional[str] = None
    image: Optional[str] = None
    buttons: Optional[List[Dict[str, Any]]] = None
    attachment: Optional[str] = None
    custom: Optional[Dict[str, Any]] = None


class RestEndpointStatus(Enum):
    OK = 'ok'
    UNREACHABLE = 'unreachable'


class ChatRole(Enum):
    HUMAN = 'human',
    AI = 'ai'


class ChatStatusOut(BaseModel):
    status: RestEndpointStatus


# Rasa

RasaRestStatus = RestEndpointStatus


class RasaStatusOut(ChatStatusOut):
    status: Union[RasaRestStatus, str]


# Langcorn

LangcornRestStatus = RestEndpointStatus


class LangcornServerStatus(BaseModel):
    functions: List[str]


class LangcornStatusOut(ChatStatusOut):
    status: RestEndpointStatus


# Taken from Langcorn package.
# TODO: import as dependency (in services.py) and use

class MemoryData(BaseModel):
    content: str
    additional_kwargs: dict[str, Any]


class Memory(BaseModel):
    type: str
    data: MemoryData


class LangRequest(BaseModel, extra=Extra.allow):
    # Additional fields for input keys
    memory: List[Memory]


class LangResponse(BaseModel):
    output: str
    error: str
    memory: list[Memory]
