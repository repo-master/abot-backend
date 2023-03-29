from fastapi import (
    FastAPI,
    Request, Response,
    HTTPException
)
from fastapi.middleware.cors import CORSMiddleware

from rasa.core.agent import Agent
from rasa.core.utils import AvailableEndpoints
from rasa.core.tracker_store import AwaitableTrackerStore

import os

DEFAULT_LOCATION = './'

ENDPOINTS_PATH = "endpoints.dev.yml"
MODEL_STORE_PATH = "data/models/"

def create_app() -> FastAPI:
  app = FastAPI()

  # Enable cross-origin request, from any domain (*)
  app.add_middleware(
      CORSMiddleware,
      allow_origins=['*'],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )

  # TODO: Load this from FastAPI config object
  endpoints = AvailableEndpoints.read_endpoints(ENDPOINTS_PATH)
  action_endpoint = endpoints.action
  tracker_store = AwaitableTrackerStore.create(endpoints.tracker_store)

  # Load the latest Rasa model present in the "models" folder
  agent = Agent.load(
      MODEL_STORE_PATH,
      action_endpoint=action_endpoint,
      tracker_store=tracker_store
  )

  # Define the chatbot endpoint
  @app.post("/chat")
  async def chat(req: Request):
    '''Get the Rasa model's response to the user's message'''
    message_data : dict = await req.json()
    if 'message' not in message_data:
      raise HTTPException(status_code=400, detail="Required field 'message' is missing")

    return await agent.handle_text(message_data['message'], sender_id=message_data.get("sender_id"))

  @app.get("/chat/status")
  def status():
    return ""

  return app
