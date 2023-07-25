'''Application to host the [private] Statistics API endpoints'''

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Routers
from abotcore import statistics
from abotcore.config import ServerSettings


def create_app() -> FastAPI:
    ### Application instance ###
    app = FastAPI()
    settings = ServerSettings()

    logging.basicConfig(level=settings.app_log_level)

    logger = logging.getLogger(__name__)

    ### Middleware ###

    # Enable cross-origin request, from any domain (*)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    ### Exception handlers ###

    @app.exception_handler(OSError)
    async def unhandled_oserror_exception_handler(request: Request, exc: OSError):
        logger.exception("Unhandled OSError while serving a request:", exc_info=exc)
        return JSONResponse(
            status_code=500, content={"exception": "OSError", "detail": str(exc)}
        )

    ### Routes ###

    # Add routes to the application

    app.include_router(statistics.router)

    return app
