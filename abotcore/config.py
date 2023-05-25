'''Root of all configuration (mostly from environment variables)'''

import logging
from typing import List, Union, Optional

from pydantic import AnyUrl, BaseSettings, PostgresDsn


class Settings(BaseSettings):
    cors_origins: List[str] = ['*']
    log_level: Union[int, str] = logging.INFO

class EndpointSettings(BaseSettings):
    rasa_rest_endpoint_base: AnyUrl = "http://localhost:5005"
    actions_endpoint_base: AnyUrl = "http://localhost:5055"


class DBSettings(BaseSettings):
    # DB to connect to (from environment variable). Default is in-memory DB (content will be lost!)
    db_uri: Union[PostgresDsn, AnyUrl] = 'sqlite+aiosqlite:///:memory:'
    db_schema_map: Optional[List[str]] = None

    class Config:
        '''Yo dawg, I heard you like configs, so I put a config in your config'''
        env_file = ".env"
