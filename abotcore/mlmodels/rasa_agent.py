
import logging

import asyncio
from fastapi import FastAPI

from rasa.core.channels import UserMessage
from abotcore.channel.customchannel import CustomInputChannel

from typing import Optional, Coroutine, List, Dict, Any

from .config import ENDPOINTS_PATH, CREDENTIALS_PATH, MODEL_STORE_PATH


LOG = logging.getLogger(__name__)
#TODO: Use ContextVar to set this correctly
rasa_agent = None

async def rasa_agent_lifespan(app : FastAPI) -> Optional[Coroutine]:
  global rasa_agent
  # Rasa Agent (ML model execution)
  from rasa.core.agent import Agent, load_agent
  from rasa.core.utils import AvailableEndpoints
  from rasa.core.run import create_http_input_channels

  assert isinstance(ENDPOINTS_PATH, str)
  endpoints = AvailableEndpoints.read_endpoints(ENDPOINTS_PATH)

  # Credentials file for various channels (Telegram, Messenger, etc.)
  cred_file = CREDENTIALS_PATH
  if isinstance(cred_file, str) and len(cred_file) == 0:
    cred_file = None

  input_channels = create_http_input_channels(None, cred_file)

  LOG.info("Creating Rasa Agent from endpoints (%s)", ENDPOINTS_PATH)
  agent : Agent = await load_agent(model_path=MODEL_STORE_PATH, endpoints=endpoints)
  if agent.processor is not None:
    LOG.info("Loaded model '%s'", agent.processor.model_filename)
    rasa_agent = agent

  futures = asyncio.gather(*[chn.init_agent(agent) for chn in input_channels if isinstance(chn, CustomInputChannel)])

  await futures

async def handle_message(message : UserMessage) -> Optional[List[Dict[str, Any]]]:
  return await rasa_agent.handle_message(message)
