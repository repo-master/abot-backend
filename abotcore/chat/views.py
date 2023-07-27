from fastapi import APIRouter, Depends, HTTPException, UploadFile

import os
from tempfile import mkstemp

from .schemas import ChatMessageIn, ChatMessageOut, ChatStatusOut
from .services import (
    BaseChatServer,
    DummyChatServer,
    RasaChatServer,
    LangcornChatServer,
)

from abotcore.db import Session, get_session
from abotcore.schemas import ChatServiceType
from abotcore.config import (
    ChatEndpointSettings,
    FileCacheServerSettings,
    joinurl,
)

from typing import List, Dict, Callable
from functools import partial


_base_endpoint = ChatEndpointSettings()


# Endpoint router
router = APIRouter(prefix="/chat")
chat_webhook = APIRouter(prefix="/webhook")


CHAT_SERVICE_MAP: Dict[str, Callable[..., BaseChatServer]] = {
    ChatServiceType.DUMMY: DummyChatServer,
    ChatServiceType.RASA: RasaChatServer,
    ChatServiceType.LANGCHAIN_GENESIS: partial(
        LangcornChatServer, chain_name="genesis.langcorn:chain"
    ),
    ChatServiceType.LANGCHAIN_FUNCTION: partial(
        LangcornChatServer, chain_name="logic:chain"
    ),
}


async def get_chat_server(
    service: ChatServiceType = _base_endpoint.chat_endpoint_server,
    abot_dbsession: Session = Depends(get_session),
) -> BaseChatServer:
    return CHAT_SERVICE_MAP[service](dbsession=abot_dbsession)


# Default route (/chat)
# Chat endpoint service webhook
@router.post(
    "",
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    response_model_by_alias=False,
)
@chat_webhook.post(
    "/{service:str}",
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def chat_service_hook(
    msg: ChatMessageIn, server: BaseChatServer = Depends(get_chat_server)
) -> List[ChatMessageOut]:
    """Get the selected chat server's response to the user's message"""
    return await server(msg)


# Chat endpoint status webhook
@router.get("/status")
@chat_webhook.get("/{service:str}/status")
async def chat_service_status(
    server: BaseChatServer = Depends(get_chat_server),
) -> ChatStatusOut:
    """Heartbeat and status enquiry of selected server"""
    return await server.get_status()


def resolve_cache_file_public_url(cache_save: str, file_path: str):
    cache_base_url = FileCacheServerSettings.get_cache_base()
    # cache_save must be the same directory that is served by cache_base_url

    return joinurl(cache_base_url, os.path.relpath(file_path, cache_save))


@router.post("/cache")
async def gen_cache(file: UploadFile) -> dict:
    cache_save = FileCacheServerSettings.get_cache_storage_path()

    if cache_save is None:
        return HTTPException(501, detail="Cache was not set-up, can't create the file.")

    if not cache_save.exists():
        return HTTPException(501, detail="Cache storage directory isn't properly initialized, can't create the file.")

    in_fname = file.filename or 'download'

    tmp_fd, file_path = mkstemp(dir=cache_save, suffix="_%s" % in_fname)

    with os.fdopen(tmp_fd, "wb") as f:
        f.write(await file.read())

    await file.close()

    return {"url": resolve_cache_file_public_url(cache_save, file_path)}


router.include_router(chat_webhook)
