'''Root of all configuration (mostly from environment variables)'''

from decouple import config as deconf, Csv


CORS_ORIGINS = deconf('CORS_ORIGINS', default='*', cast=Csv())

RASA_REST_ENDPOINT_BASE = deconf("RASA_REST_ENDPOINT_BASE", default="http://localhost:5005")
ACTIONS_ENDPOINT_BASE = deconf("ACTIONS_ENDPOINT_BASE", default="http://localhost:5055")

# DB to connect to (from environment variable). Default is in-memory DB (content will be lost!)
DB_URI = deconf('DB_URI', default='sqlite+aiosqlite:///:memory:')
