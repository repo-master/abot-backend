
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Routers
from abotcore import chat, fake_genesis, statistics
from abotcore.config import Settings


def create_app() -> FastAPI:
    ### Application instance ###
    app = FastAPI()
    settings = Settings()

    logging.basicConfig(
        level=settings.log_level
    )

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

    ### App events ###
    @app.on_event("startup")
    async def init_tables():
        import asyncio
        from abotcore.db import Base, Connection, get_engine, get_schema_mapping
        from sqlalchemy.schema import CreateSchema

        engine = get_engine()
        conn: Connection

        schema_mapping = get_schema_mapping()

        async with engine.begin() as conn:
            logger.info("Creating/updating DB schema (if needed)...")
            await asyncio.gather(*[
                conn.execute(
                    CreateSchema(schema_mapping.get(schema_name), if_not_exists=True)
                )
                # TODO: Auto-get this list from SQLAlchemy somehow...
                for schema_name in [
                    'genesis'
                ]
                if schema_mapping.get(schema_name)
            ])
            logger.info("Creating/updating tables (if needed)...")
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
    app.include_router(statistics.router)

    return app
