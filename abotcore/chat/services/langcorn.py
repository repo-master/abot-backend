
from uuid import uuid4 as uuidv4
from typing import List
import logging

import httpx
from fastapi import HTTPException

from abotcore.api import LangcornRestClient

from ..schemas import (ChatMessageIn, ChatMessageOut,
                      LangchainRestStatus, LangcornServerStatus,
                      LangcornStatusOut, LangResponse)

from .base import ChatServer


LOGGER = logging.getLogger(__name__)


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
            except Exception as e:
                LOGGER.exception("Failed to respond to the chat message by [%s] \"%s\" due to an exception:", chat_message.sender_id, chat_message.text)
                raise HTTPException(500, detail="Failed to generate response: %s" % str(e))

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
