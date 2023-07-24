from typing import List

from pydantic import BaseModel, Extra

from ..schemas import ChatMessageIn, ChatMessageOut, ChatStatusOut, RestEndpointStatus


class BaseChatServer(BaseModel, extra=Extra.ignore):
    async def send_chat_message(
        self, chat_message: ChatMessageIn
    ) -> List[ChatMessageOut]:
        return []

    async def get_status(self) -> ChatStatusOut:
        return {"status": RestEndpointStatus.UNREACHABLE}

    async def __call__(self, chat_message: ChatMessageIn):
        return await self.send_chat_message(chat_message)
