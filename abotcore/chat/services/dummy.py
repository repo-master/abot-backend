from uuid import uuid4 as uuidv4
from typing import List
import logging

from ..schemas import ChatMessageIn, ChatMessageOut, ChatStatusOut, RestEndpointStatus

from .base import BaseChatServer


LOGGER = logging.getLogger(__name__)


TEST_MESSAGE = "Test message response.\nMarkdown working? *Yes*.\n[Link test](http://www.google.com).\n\n__Special text__"  # noqa: E501


class DummyChatServer(BaseChatServer):
    async def send_chat_message(
        self, chat_message: ChatMessageIn
    ) -> List[ChatMessageOut]:
        if chat_message.sender_id is None:
            chat_message.sender_id = uuidv4().hex

        chat_message.text = chat_message.text.lower()

        if "test" in chat_message.text:
            return [
                ChatMessageOut(
                    recipient_id=chat_message.sender_id,
                    text=TEST_MESSAGE,
                )
            ]

        elif "hello" in chat_message.text:
            return [
                ChatMessageOut(
                    recipient_id=chat_message.sender_id, text="Hi! How may I help?"
                )
            ]

        elif "ping" in chat_message.text:
            return [ChatMessageOut(recipient_id=chat_message.sender_id, text="Pong")]

        elif "button" in chat_message.text:
            return [
                ChatMessageOut(
                    recipient_id=chat_message.sender_id,
                    text="Message with buttons",
                    buttons=[
                        {"title": "Ping", "payload": "ping"},
                        {"title": "Test message", "payload": "test"},
                        {"title": "More buttons", "payload": "btn_many"},
                    ],
                )
            ]

        elif "btn_many" in chat_message.text:
            return [
                ChatMessageOut(
                    recipient_id=chat_message.sender_id,
                    text="Message with many buttons",
                    buttons=[
                        {"title": "Button %d (does nothing)" % (i + 1), "payload": ""}
                        for i in range(10)
                    ],
                )
            ]
        return [
            ChatMessageOut(
                recipient_id=chat_message.sender_id,
                text='Don\'t know how to handle message "%s"' % chat_message.text,
            )
        ]

    async def get_status(self) -> ChatStatusOut:
        """Get Langcorn server health"""
        return ChatStatusOut(status=RestEndpointStatus.OK)
