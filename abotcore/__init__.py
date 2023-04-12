
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager

# App lifespan
from abotcore.mlmodels.rasa_agent import rasa_agent_lifespan

# Routers
from abotcore import (
  chat
)

from typing import List, Optional, Coroutine

# Configuration
from decouple import config as deconf, Csv


CORS_ORIGINS = deconf('CORS_ORIGINS', default='*', cast=Csv())

@asynccontextmanager
async def app_lifespan(app : FastAPI):
  tasks = [
    rasa_agent_lifespan(app)
  ]
  cleanup : List[Optional[Coroutine]] = await asyncio.gather(*tasks)
  yield
  await asyncio.gather(*filter(asyncio.iscoroutine, cleanup))

def create_app() -> FastAPI:
  app = FastAPI(lifespan=app_lifespan)

  # Enable cross-origin request, from any domain (*)
  app.add_middleware(
      CORSMiddleware,
      allow_origins=CORS_ORIGINS,
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )

  # Add routes to the application
  app.include_router(chat.router)

  return app
