from fastapi import FastAPI
from rasa.core.agent import Agent
from rasa.core.utils import AvailableEndpoints
from uuid import UUID
import os

DEFAULT_LOCATION = './project/'

def create_app() -> FastAPI:
    app = FastAPI()


    endpoints = AvailableEndpoints.read_endpoints(f"{DEFAULT_LOCATION}endpoints.yml")

    # Load the Rasa model
    agent = Agent.load(f"{DEFAULT_LOCATION}models/20230222-152950-rainy-crescendo.tar.gz", action_endpoint=endpoints.action)
   
    @app.get("/home")
    def home():
        return {"Hello": "World"}

    # Define the chatbot endpoint
    @app.post("/chat")
    async def chat(message: str, sender_id : str):
        # Get the Rasa model's response to the user's message
        response = await agent.handle_text("message", sender_id=sender_id)
        print(response)
        return response

    @app.get("/")
    def default():
        return UUID(bytes=os.urandom(16), version=4)
    
    return app