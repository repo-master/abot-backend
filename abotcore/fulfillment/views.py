
from fastapi import APIRouter, Depends, Request

from .services import FulfillmentSync

# Main endpoint router for fake Genesis
router = APIRouter(prefix='/fulfillment')


@router.api_route('/{id:int}{endpoint:path}')
async def perform_fulfillment(id: int, endpoint: str, request: Request, ff_sync: FulfillmentSync = Depends(FulfillmentSync)):
    return await ff_sync.perform_fulfillment_request(id, endpoint, request)
