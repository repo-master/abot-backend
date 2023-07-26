import logging
from typing import List, Optional, Dict, Any
from uuid import uuid4 as uuidv4

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, Extra, Field, parse_obj_as

from abotcore.api import LangcornRestClient
from abotcore.db import Session, get_session

from ..models import ChatHistory, UserChatMemory
from ..schemas import (
    ChatMessageIn,
    ChatMessageOut,
    ChatRole,
    ChatStatusOut,
    RestEndpointStatus,
    Memory,
)
from .base import BaseChatServer


# Schemas

LangcornRestStatus = RestEndpointStatus


class LangcornServerStatus(BaseModel):
    functions: List[str]


class LangcornStatusOut(ChatStatusOut):
    status: RestEndpointStatus


# Taken from Langcorn package.
# TODO: import as dependency (in services.py) and use


class LangRequest(BaseModel, extra=Extra.allow):
    # Additional fields for input keys
    memory: List[Memory]


class LangResponse(BaseModel, extra=Extra.allow):
    output: Optional[Dict[str, Any]]
    error: Optional[str]
    memory: List[Memory]


LOGGER = logging.getLogger(__name__)


class LangcornChatServer(BaseChatServer, arbitrary_types_allowed=True):
    chain_name: str
    input_key: str = "input"
    output_key: str = "output"
    dbsession: Session = Field(default_factory=get_session)

    def _chan_name_path(self):
        return self.chain_name.replace(":", ".")

    async def send_chat_message(
        self, chat_message: ChatMessageIn
    ) -> List[ChatMessageOut]:
        if chat_message.sender_id is None:
            chat_message.sender_id = uuidv4().hex

        LOGGER.info(
            "Sending message with sender id %s: %s",
            chat_message.sender_id,
            chat_message.text,
        )

        memory: List[Memory] = await self._get_user_memory(chat_message.sender_id)

        await self._insert_chat_history_user(chat_message)

        async with LangcornRestClient() as client:
            try:
                LOGGER.info("Memory: %s", memory)
                lcorn_message: LangRequest = LangRequest.parse_obj(
                    {self.input_key: chat_message.text, "memory": memory}
                )
                response = await client.post(
                    "/%s/run" % self._chan_name_path(), json=lcorn_message.dict()
                )
                response.raise_for_status()
                resp_data = response.json()
                response_message: LangResponse = LangResponse.parse_obj(resp_data)
                await self._insert_chat_history_ai(response_message, chat_message)
                await self._upsert_user_memory(
                    chat_message.sender_id, response_message.memory
                )
                return self._map_response_to_message(response_message, chat_message)
            except httpx.ConnectError:
                raise HTTPException(
                    500, detail="Failed to connect to the Langcorn REST service"
                )
            except httpx.ReadTimeout:
                raise HTTPException(
                    500, detail="Langcorn REST service took too long to respond"
                )
            except httpx.HTTPStatusError as e:
                LOGGER.warning(
                    'Failed to respond to the chat message by [%s] "%s" due to an exception in Langcorn:',
                    chat_message.sender_id,
                    chat_message.text,
                    exc_info=e,
                )
                LOGGER.info(
                    "Content received (for above exception):\n%s",
                    e.request.content.decode(errors="replace"),
                )
                raise HTTPException(
                    500, detail="Failed to generate response: %s" % str(e)
                )
            except Exception as e:
                LOGGER.exception(
                    'Failed to respond to the chat message by [%s] "%s" due to an exception:',
                    chat_message.sender_id,
                    chat_message.text,
                )
                raise HTTPException(
                    500, detail="Failed to generate response: %s" % str(e)
                )

    async def get_status(self) -> LangcornStatusOut:
        """Get Langcorn server health"""
        async with LangcornRestClient() as client:
            try:
                response = await client.get("/ht")
                endpoints_status: LangcornServerStatus = response.json()
                endpoint_available_functions: List[str] = endpoints_status.get(
                    "functions", []
                )
                if self.chain_name in endpoint_available_functions:
                    return LangcornStatusOut(status=LangcornRestStatus.OK)
                LOGGER.warning(
                    "Langcorn model endpoint '%s' was unavailable. Available ones: [%s]"
                    % (self.chain_name, ", ".join(endpoint_available_functions))
                )
                return LangcornStatusOut(status=LangcornRestStatus.UNREACHABLE)
            except (httpx.ConnectError, httpx.ReadTimeout) as e:
                LOGGER.warning(
                    "Langcorn chat endpoint was unreachable when requested:", exc_info=e
                )
                return LangcornStatusOut(status=LangcornRestStatus.UNREACHABLE)

    def _map_response_to_message(
        self, msg: LangResponse, user_message: ChatMessageIn
    ) -> List[ChatMessageOut]:
        # Langcorn just returns a single message
        # TODO: Maybe split text every paragraph (and keep all assets for first message, buttons for last)
        LOGGER.info(
            "Langcorn reply (%s) {%s}: %s",
            user_message.sender_id,
            ",".join(msg._calculate_keys(None, None, True)),
            msg.output,
        )
        return [ChatMessageOut(recipient_id=user_message.sender_id, **msg.output)]

    async def _insert_chat_history_user(self, user_message: ChatMessageIn):
        self.dbsession.add(
            ChatHistory(
                chat_handler=self.chain_name,
                message_client_id=user_message.sender_id,
                message_role=ChatRole.HUMAN,
                message_content=user_message.text,
            )
        )
        await self.dbsession.commit()

    async def _insert_chat_history_ai(
        self, ai_message: LangResponse, user_message: ChatMessageIn
    ):
        self.dbsession.add(
            ChatHistory(
                chat_handler=self.chain_name,
                message_client_id=user_message.sender_id,
                message_role=ChatRole.AI,
                message_content=ai_message.output.get(self.output_key),
            )
        )
        await self.dbsession.commit()

    async def _get_user_memory(self, user_id: str) -> List[Memory]:
        chat_memory_obj: Optional[UserChatMemory] = await self.dbsession.get(
            UserChatMemory, user_id
        )
        if chat_memory_obj is None:
            return []
        return parse_obj_as(List[Memory], chat_memory_obj.memory_data)

    async def _upsert_user_memory(self, user_id: str, memory_list: List[Memory]):
        await self.dbsession.merge(
            UserChatMemory(
                user_id=user_id, memory_data=list(map(Memory.dict, memory_list))
            )
        )
        await self.dbsession.commit()
