from fastapi import FastAPI
import uvicorn
from rasa.core.agent import Agent
from rasa.core.utils import AvailableEndpoints
from uuid import UUID
import os

app = FastAPI()

endpoints = AvailableEndpoints.read_endpoints("endpoints.yml")
# agent = Agent.load("xxxxxx", action_endpoint=endpoints.action)

# Load the Rasa model
agent = Agent.load("models/20230222-152950-rainy-crescendo.tar.gz", action_endpoint=endpoints.action)


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


if __name__ == '__main__':
    uvicorn.run(app,host ='localhost', port=5005)
