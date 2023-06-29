
from typing import List

from ..schemas import (ChatMessageIn, ChatMessageOut, ChatStatusOut,
                       RestEndpointStatus)


class ChatServer:
    async def send_chat_message(self, chat_message: ChatMessageIn) -> List[ChatMessageOut]:
        return []

    async def get_status(self) -> ChatStatusOut:
        return {
            "status": RestEndpointStatus.UNREACHABLE
        }
