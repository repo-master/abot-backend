

import asyncio
import logging
import urllib.parse
from datetime import datetime
from itertools import starmap
from typing import Optional, Tuple

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import Response
from sqlalchemy import Result, select

from abotcore.api import AsyncClient
from abotcore.db import Session, get_session

from .models import Fulfillment

logger = logging.getLogger(__name__)

ENDPOINT_ABOT_FULFILLMENTS_QUERY = "/abot"


class FulfillmentSync:
    def __init__(self, session: Session = Depends(get_session)):
        self.async_session: Session = session

    async def perform_fulfillment_request(self, fulfillment_id: int, endpoint_uri: str, request: Request):
        if len(endpoint_uri) == 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Endpoint cannot be empty. Root endpoints need a '/'.")

        found_fulfillment: Optional[Fulfillment] = await self.async_session.get(Fulfillment, fulfillment_id)
        if not found_fulfillment:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Fulfillment with id %d not found" % fulfillment_id)

        fulfillment_url = urllib.parse.urljoin(found_fulfillment.endpoint_base_url, endpoint_uri)

        async with AsyncClient(timeout=30) as client:
            req = client.build_request(
                request.method,
                fulfillment_url,
                headers=request.headers.raw,
                params=request.query_params,
                content=request.stream()
            )

            logger.debug("Sending fulfillment request to %s using %s method",
                        fulfillment_url,
                        request.method)

            res = await client.send(req)
            return Response(
                res.content,
                status_code=res.status_code,
                headers=res.headers
            )

    async def update_fulfillment_record(self, fulfillment: Fulfillment, data: dict):
        for var, value in data.items():
            setattr(fulfillment, var, value) if value else None
        await self.async_session.commit()

    async def sync_fulfillment(self, fulfillment: Fulfillment):
        ff_id, ff_endpoint_url = fulfillment.fulfillment_id, fulfillment.endpoint_base_url
        logger.debug("Syncing fulfillment (%d) URL: %s", ff_id, ff_endpoint_url)
        async with AsyncClient(timeout=30) as cli:
            try:
                query_url = urllib.parse.urljoin(ff_endpoint_url, ENDPOINT_ABOT_FULFILLMENTS_QUERY)
                response = await cli.get(query_url)

                await self.update_fulfillment_record(fulfillment, response.json())

                fulfillment.time_last_sync = datetime.now()
                await self.async_session.commit()
                await self.async_session.flush()
            except (httpx.ConnectError, httpx.ReadTimeout):
                logger.exception("Failed to synchronize fulfillment %s:", ff_endpoint_url)
            else:
                logger.info("Fulfillment \"%s\" synced successfully", ff_endpoint_url)

    async def sync_all(self, force: bool = False):
        result: Result[Tuple[Fulfillment]] = await self.async_session.execute(
            select(Fulfillment)
        )

        coros = starmap(self.sync_fulfillment, result)
        await asyncio.gather(*coros)


__all__ = [
    'FulfillmentSync'
]
