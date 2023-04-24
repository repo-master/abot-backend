
from fastapi import APIRouter, Depends

from .schemas import (
    ChatMessageIn,
    ChatMessageOut,
    RasaStatusOut
)
from .services import (
    ChatMessageService
)

from typing import List


# Endpoint router
router = APIRouter(prefix='/chat')


# Default route (/chat)
@router.post("", response_model_exclude_unset=True)
async def chat(msg: ChatMessageIn, chat_service: ChatMessageService = Depends(ChatMessageService)) -> List[ChatMessageOut]:
    '''Get the Rasa model's response to the user's message'''

    # Generate responses from the Rasa Agent, wait for all replies and send back as JSON.
    # sender_id is optional in this case.
    # Send back all generated responses at once
    return await chat_service.send_chat_message(msg)

# Used as a heartbeat and general status enquiry (/chat/status)


@router.get("/status")
async def status(chat_service: ChatMessageService = Depends(ChatMessageService)) -> RasaStatusOut:
    '''Heartbeat and status enquiry'''
    return await chat_service.get_status()
