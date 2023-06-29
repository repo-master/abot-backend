
from uuid import uuid4 as uuidv4
from typing import Dict, List, Type
import logging

import httpx
from fastapi import HTTPException

from abotcore.api import LangcornRestClient, RasaRestClient

from .schemas import (ChatMessageIn, ChatMessageOut,
                      ChatStatusOut, LangchainRestStatus, LangcornServerStatus,
                      LangcornStatusOut, LangResponse, RasaRestStatus,
                      RasaStatusOut, RestEndpointStatus)

LOGGER = logging.getLogger(__name__)


class ChatServer:
    async def send_chat_message(self, chat_message: ChatMessageIn) -> List[ChatMessageOut]:
        return []

    async def get_status(self) -> ChatStatusOut:
        return {
            "status": RestEndpointStatus.UNREACHABLE
        }


class RasaChatServer(ChatServer):
    async def send_chat_message(self, chat_message: ChatMessageIn) -> List[ChatMessageOut]:
        async with RasaRestClient() as client:
            try:
                # Format that Rasa's REST channel uses is slightly different
                rasa_message = {
                    "message": chat_message.text,
                    "sender": chat_message.sender_id
                }
                response = await client.post("/webhooks/rest/webhook", json=rasa_message)
                response_messages: List[Dict] = response.json()
                return [ChatMessageOut(**msg) for msg in response_messages]
            except httpx.ConnectError:
                raise HTTPException(500, detail="Failed to connect to Rasa REST service")
            except httpx.ReadTimeout:
                raise HTTPException(500, detail="Rasa REST service took too long to respond")

    async def get_status(self) -> RasaStatusOut:
        async with RasaRestClient() as client:
            try:
                response = await client.get("/webhooks/rest")
                return RasaStatusOut(**response.json())
            except (httpx.ConnectError, httpx.ReadTimeout):
                return RasaStatusOut(status=RasaRestStatus.UNREACHABLE)


class LangcornChatServer(ChatServer):
    CHAIN_NAME = 'genesis.chat_chain'
    INPUT_VAR = 'input'

    async def send_chat_message(self, chat_message: ChatMessageIn) -> List[ChatMessageOut]:
        async with LangcornRestClient() as client:
            try:
                if chat_message.sender_id is None:
                    chat_message.sender_id = uuidv4().hex
                lcorn_message = {
                    self.INPUT_VAR: chat_message.text,
                    "memory": [
                        {}
                    ]
                }
                response = await client.post("/%s/run" % self.CHAIN_NAME, json=lcorn_message)
                response_message: LangResponse = response.json()
                return self._map_response_to_message(response_message, chat_message.sender_id)
            except httpx.ConnectError:
                raise HTTPException(500, detail="Failed to connect to the Langcorn REST service")
            except httpx.ReadTimeout:
                raise HTTPException(500, detail="Langcorn REST service took too long to respond")

    def _map_response_to_message(self, msg: LangResponse, sender_id: str) -> List[ChatMessageOut]:
        # Langcorn just returns a single message
        # TODO: Maybe split text every paragraph (and keep all assets for first message, buttons for last)
        return [
            ChatMessageOut(
                recipient_id=sender_id,
                text=msg['output']
            )
        ]

    async def get_status(self) -> LangcornStatusOut:
        '''Get Langcorn server health'''
        async with LangcornRestClient() as client:
            try:
                response = await client.get("/ht")
                endpoints_status: LangcornServerStatus = response.json()
                endpoint_available_functions = [x.split(':')[0] for x in endpoints_status.get('functions', [])]
                if self.CHAIN_NAME in endpoint_available_functions:
                    return LangcornStatusOut(status=LangchainRestStatus.OK)
                LOGGER.warning("Langcorn model endpoint '%s' was unavailable. Available ones: [%s]" % ', '.join(
                    endpoint_available_functions))
                return LangcornStatusOut(status=LangchainRestStatus.UNREACHABLE)
            except (httpx.ConnectError, httpx.ReadTimeout) as e:
                LOGGER.warning("Langcorn chat endpoint was unreachable when requested:", exc_info=e)
                return LangcornStatusOut(status=LangchainRestStatus.UNREACHABLE)


def make_chat_service_class(handler_base: Type[ChatServer] = ChatServer):
    class ChatMessageService(handler_base):
        def __init__(self) -> None:
            pass

    return ChatMessageService
