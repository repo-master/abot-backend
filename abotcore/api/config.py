from abotcore.config import EndpointSettings

from functools import lru_cache


@lru_cache()
def get_endpoint_settings() -> EndpointSettings:
    return EndpointSettings()
