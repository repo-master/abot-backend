
from fastapi import APIRouter, Depends

from .schemas import (
    ChatMessageIn,
    ChatMessageOut,
    ChatStatusOut
)
from .services import (
    ChatServer,
    DummyChatServer,
    RasaChatServer,
    LangcornChatServer
)

from enum import Enum
from typing import List, Dict, Type

EnabledChatService = LangcornChatServer


# Endpoint router
router = APIRouter(prefix='/chat')
chat_webhook = APIRouter(prefix='/webhook')


class ChatService(str, Enum):
    langcorn = LangcornChatServer
    dummy = DummyChatServer
    rasa = RasaChatServer


# Chat endpoint service webhook
# @chat_webhook.post("/{service:str}", response_model_exclude_unset=True)
# async def chat_service_hook(msg: ChatMessageIn, service: ChatService) -> List[ChatMessageOut]:
#     '''Get the chat service's response to the user's message'''
#     print(service, type(service))
#     return await service.send_chat_message(msg)


# Default route (/chat)
@router.post("", response_model_exclude_unset=True)
async def chat(msg: ChatMessageIn, chat_service: EnabledChatService = Depends(EnabledChatService)) -> List[ChatMessageOut]:
    '''Get the chat model's response to the user's message'''

    # Generate responses from the Rasa Agent, wait for all replies and send back as JSON.
    # sender_id is optional in this case.
    # Send back all generated responses at once
    return await chat_service.send_chat_message(msg)

# Used as a heartbeat and general status enquiry (/chat/status)


@router.get("/status")
async def status(chat_service: EnabledChatService = Depends(EnabledChatService)) -> ChatStatusOut:
    '''Heartbeat and status enquiry'''
    return await chat_service.get_status()

router.include_router(chat_webhook)
