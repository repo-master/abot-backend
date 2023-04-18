
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager

# Routers
from abotcore import (
    chat,
    api_data
)

from abotcore.config import CORS_ORIGINS

from typing import List, Optional, Coroutine


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    tasks = [

    ]
    cleanup: List[Optional[Coroutine]] = await asyncio.gather(*tasks)
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
    app.include_router(api_data.router)

    return app
