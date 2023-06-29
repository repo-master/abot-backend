'''Root of all configuration (mostly from environment variables)'''

import logging
from typing import List, Union, Optional

from pydantic import AnyUrl, BaseSettings, PostgresDsn


class BaseBackendSettings(BaseSettings):
    class Config:
        env_file = ".env"
        env_prefix = 'abot_backend_'


class ServerSettings(BaseBackendSettings):
    cors_origins: List[str] = ['*']
    app_log_level: Union[int, str] = logging.INFO


class EndpointSettings(BaseBackendSettings):
    rasa_rest_endpoint_base: AnyUrl = "http://localhost:5005"
    actions_endpoint_base: AnyUrl = "http://localhost:5055"
    langcorn_endpoint_base: AnyUrl = "http://localhost:7860"


class DBSettings(BaseBackendSettings):
    # DB to connect to (from environment variable). Default is in-memory DB (content will be lost!)
    db_uri: Union[PostgresDsn, AnyUrl] = 'sqlite+aiosqlite:///:memory:'
    db_schema_map: Optional[List[str]] = None
