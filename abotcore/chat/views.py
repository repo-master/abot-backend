
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

from typing import List, Dict, Type

EnabledChatService = DummyChatServer


# Endpoint router
router = APIRouter(prefix='/chat')
chat_webhook = APIRouter(prefix='/webhook')


service_hook_map: Dict[str, Type[ChatServer]] = {
    service.name: service for service in [DummyChatServer, LangcornChatServer, RasaChatServer]
}

def chat_server_hook_class(service: str) -> Type[ChatServer]:
    ServiceClass = service_hook_map[service]
    class ChatServerHook(metaclass=ServiceClass):
        def __init__(self, service: ServiceClass = Depends(ServiceClass)):
            pass
    return ChatServerHook

# Chat endpoint service webhook
@chat_webhook.post("/{service:str}", response_model_exclude_unset=True)
async def chat_service_hook(msg: ChatMessageIn, chat_service: ChatServer = Depends(chat_server_hook_class)) -> List[ChatMessageOut]:
    '''Get the chat service's response to the user's message'''
    print(chat_service)
    print(chat_service.name)
    return await chat_service.send_chat_message(msg)


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
