
from typing import Type

from .base import ChatServer


def make_chat_service_class(handler_base: Type[ChatServer] = ChatServer):
    class ChatMessageService(handler_base):
        def __init__(self) -> None:
            pass

    return ChatMessageService
