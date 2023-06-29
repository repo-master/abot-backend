
from httpx import AsyncClient

from .config import get_endpoint_settings


def RasaRestClient(**kwargs) -> AsyncClient:
    settings = get_endpoint_settings()
    return AsyncClient(base_url=settings.rasa_rest_endpoint_base, timeout=30, **kwargs)


def LangcornRestClient(**kwargs) -> AsyncClient:
    settings = get_endpoint_settings()
    return AsyncClient(base_url=settings.langcorn_endpoint_base, timeout=30, **kwargs)


def RasaActionsClient(**kwargs) -> AsyncClient:
    settings = get_endpoint_settings()
    return AsyncClient(base_url=settings.actions_endpoint_base, timeout=30, **kwargs)
