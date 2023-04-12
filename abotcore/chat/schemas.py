'''Data validation schemas (Pydantic) used by chat endpoints'''

from pydantic import BaseModel, Extra
from typing import Optional, Dict, List, Any


class ChatMessage(BaseModel):
  text : str

  class Config:
    extra = Extra.forbid

class ChatMessageIn(ChatMessage):
  '''
  Represents a message sent by the user (only text is allowed).
  Content is given as input to a `UserMessage` class instance
  '''
  sender_id : Optional[str] = None

class ChatMessageOut(ChatMessage):
  recipient_id : str
  image : Optional[str] = None
  buttons : Optional[List[Dict[str, Any]]] = None
  attachment : Optional[str] = None
  custom : Optional[Dict[str, Any]] = None
