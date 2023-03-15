from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from rasa.core.agent import Agent
from rasa.core.utils import AvailableEndpoints
from uuid import uuid4
import os

DEFAULT_LOCATION = './'

def create_app() -> FastAPI:
    app = FastAPI()

    # Enable cross-origin request, from any domain (*)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*']
    )

    endpoints = AvailableEndpoints.read_endpoints(os.path.join(DEFAULT_LOCATION, "endpoints.yml"))

    # Load the latest Rasa model present in the "models" folder
    agent = Agent.load(
        os.path.join(DEFAULT_LOCATION, "models/"),
        action_endpoint=endpoints.action
    )

    # Define the chatbot endpoint
    @app.post("/chat")
    async def chat(message: str, sender_id : str):
        '''Get the Rasa model's response to the user's message'''
        response = await agent.handle_text(message, sender_id=sender_id)
        #print(response)
        return response

    @app.get("/")
    def default():
        '''Create a new random ID'''
        return {
            "sender_id": uuid4()
        }
    
    @app.get("/chat/heartbeat")
    def heartbeat():
        return ""
    
    return app