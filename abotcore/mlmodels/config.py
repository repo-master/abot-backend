
from decouple import config as deconf

from typing import Optional


# Configuration variables (from environment or .env)
# Point to the endpoints configuration file
ENDPOINTS_PATH : str = deconf('ENDPOINTS_FILE', default="endpoints.dev.yml")
CREDENTIALS_PATH : str = deconf('CREDENTIALS_FILE', default=None)
# Optional path to model stored locally on disk (can be folder path, will choose latest model)
MODEL_STORE_PATH : Optional[str] = deconf('MODEL_PATH', default=None)
