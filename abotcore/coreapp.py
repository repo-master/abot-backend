
import asyncio
import logging

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
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
    ### Application instance ###
    app = FastAPI(lifespan=app_lifespan)
    logger = logging.getLogger(__name__)


    ### Middleware ###

    # Enable cross-origin request, from any domain (*)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


    ### Exception handlers ###

    @app.exception_handler(OSError)
    async def unhandled_oserror_exception_handler(request: Request, exc: OSError):
        logger.exception("Unhandled OSError while serving a request:", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"exception": 'OSError', "detail": str(exc)}
        )


    ### Routes ###

    # Add routes to the application
    app.include_router(chat.router)
    app.include_router(api_data.router)

    return app
