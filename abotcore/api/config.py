
from decouple import config


RASA_REST_ENDPOINT_BASE = config("RASA_REST_ENDPOINT_BASE", default="http://localhost:5005")
ACTIONS_ENDPOINT_BASE = config("ACTIONS_ENDPOINT_BASE", default="http://localhost:5055")
