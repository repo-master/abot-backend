
import logging
from typing import Dict, List, Union

import httpx
from fastapi import HTTPException

from abotcore.api import RasaRestClient

from ..schemas import (ChatMessageIn, ChatMessageOut, ChatStatusOut,
                       RestEndpointStatus)
from .base import ChatServer


# Schemas

RasaRestStatus = RestEndpointStatus


class RasaStatusOut(ChatStatusOut):
    status: Union[RasaRestStatus, str]


# Chat server with Rasa REST API

class RasaChatServer(ChatServer):
    name = "rasa"

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
