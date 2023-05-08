
import asyncio
import logging

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager

# Routers
from abotcore import (
    chat,
    fake_genesis
)

from abotcore.config import Settings

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
    settings = Settings()

    ### Middleware ###

    # Enable cross-origin request, from any domain (*)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    ### App events ###
    @app.on_event("startup")
    async def init_tables():
        from abotcore.db import Base, Connection, get_engine
        engine = get_engine()
        conn: Connection
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

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

    ##### PUBLIC #####
    app.include_router(chat.router)
    app.include_router(fake_genesis.router)

    ##### PRIVATE #####

    return app
