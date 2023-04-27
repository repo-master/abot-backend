
from httpx import AsyncClient

from .config import get_endpoint_settings


def RasaRestClient(**kwargs) -> AsyncClient:
    settings = get_endpoint_settings()
    return AsyncClient(base_url=settings.rasa_rest_endpoint_base, **kwargs)


def RasaActionsClient(**kwargs) -> AsyncClient:
    settings = get_endpoint_settings()
    return AsyncClient(base_url=settings.actions_endpoint_base, **kwargs)