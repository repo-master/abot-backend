from fastapi import FastAPI, Response
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
      allow_origins=['*']
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
  async def chat(message: str, sender_id: str):
    '''Get the Rasa model's response to the user's message'''
    return await agent.handle_text(message, sender_id=sender_id)

  @app.get("/chat/status")
  def status():
    return ""

  return app
