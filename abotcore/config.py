"""Root of all configuration (mostly from environment variables)"""

import logging
from functools import lru_cache
from typing import List, Union, Optional

from .schemas import ChatServiceType

from pydantic import AnyUrl, BaseSettings, PostgresDsn, DirectoryPath


class BaseBackendSettings(BaseSettings):
    class Config:
        env_file = ".env"
        env_prefix = "abot_backend_"


class ServerSettings(BaseBackendSettings):
    cors_origins: List[str] = ["*"]
    app_log_level: Union[int, str] = logging.INFO
    static_serve_directory: Optional[DirectoryPath] = None


class EndpointSettings(BaseBackendSettings):
    rasa_rest_endpoint_base: AnyUrl = "http://localhost:5005"
    actions_endpoint_base: AnyUrl = "http://localhost:5055"
    langcorn_endpoint_base: AnyUrl = "http://localhost:7860"
    cache_public_base: AnyUrl = "http://localhost:8000/static/"


class ChatEndpointSettings(BaseBackendSettings):
    chat_endpoint_server: ChatServiceType = ChatServiceType.DUMMY
    """Which endpoint server handles the /chat endpoint (See ChatServiceType enum in schemas.py)"""


class DBSettings(BaseBackendSettings):
    # DB to connect to (from environment variable). Default is in-memory DB (content will be lost!)
    db_uri: Union[PostgresDsn, AnyUrl] = "sqlite+aiosqlite:///:memory:"
    db_schema_map: Optional[List[str]] = None


@lru_cache()
def get_cache_base():
    return EndpointSettings().cache_public_base


def joinurl(baseurl, path):
    return '/'.join([baseurl.rstrip('/'), path.lstrip('/')])
