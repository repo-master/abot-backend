
from httpx import AsyncClient

from .config import RASA_REST_ENDPOINT_BASE, ACTIONS_ENDPOINT_BASE


def RasaRestClient(**kwargs) -> AsyncClient:
    return AsyncClient(base_url=RASA_REST_ENDPOINT_BASE, **kwargs)

def RasaActionsClient(**kwargs) -> AsyncClient:
    return AsyncClient(base_url=ACTIONS_ENDPOINT_BASE, **kwargs)
