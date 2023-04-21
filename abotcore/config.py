'''Root of all configuration (mostly from environment variables)'''

from typing import List, Union
from pydantic import (
    BaseSettings,
    AnyUrl,
    PostgresDsn
)


class Settings(BaseSettings):
    cors_origins: List[str] = ['*']

class EndpointSettings(BaseSettings):
    rasa_rest_endpoint_base: AnyUrl = "http://localhost:5005"
    actions_endpoint_base: AnyUrl = "http://localhost:5055"

class DBSettings(BaseSettings):
    # DB to connect to (from environment variable). Default is in-memory DB (content will be lost!)
    db_uri: Union[PostgresDsn, AnyUrl] = 'sqlite+aiosqlite:///:memory:'

    class Config:
        '''Yo dawg, I heard you like configs, so I put a config in your config'''
        env_file = ".env"
