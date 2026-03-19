"""Warehouse v1 endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.core import get_async_session
from src.routers.v1.warehouse.actions import (
    _list_stock,
    _receive_batch,
    _release_stock,
    _reserve_stock,
)
from src.routers.v1.warehouse.dal import StockDAL
from src.routers.v1.warehouse.description import (
    LIST_STOCK_DESC,
    RECEIVE_BATCH_DESC,
    RELEASE_STOCK_DESC,
    RESERVE_STOCK_DESC,
)
from src.routers.v1.warehouse.schemas import (
    ReceiveRequest,
    ReceiveBatchResponse,
    ReleaseRequest,
    ReleaseResponse,
    ReserveRequest,
    ReserveResponse,
    StockListResponse,
)
from src.routers.v1.warehouse.summary import (
    LIST_STOCK_SUMMARY,
    RECEIVE_BATCH_SUMMARY,
    RELEASE_STOCK_SUMMARY,
    RESERVE_STOCK_SUMMARY,
)

warehouse_router = APIRouter(prefix="/warehouse", tags=["warehouse"])


async def get_dal(
    session: AsyncSession = Depends(get_async_session),
) -> StockDAL:
    """Dependency: get StockDAL instance."""
    return StockDAL(session=session)


@warehouse_router.get(
    "/stock",
    response_model=StockListResponse,
    status_code=status.HTTP_200_OK,
    summary=LIST_STOCK_SUMMARY,
    description=LIST_STOCK_DESC,
)
async def list_stock(
    skip: int = 0,
    limit: Annotated[int, 1:100] = 50,
    dal: StockDAL = Depends(get_dal),
) -> StockListResponse:
    """Get inventory."""
    return await _list_stock(dal, skip=skip, limit=limit)


@warehouse_router.post(
    "/stock/reserve",
    response_model=ReserveResponse,
    status_code=status.HTTP_201_CREATED,
    summary=RESERVE_STOCK_SUMMARY,
    description=RESERVE_STOCK_DESC,
)
async def reserve_stock(
    reserve_req: ReserveRequest,
    dal: StockDAL = Depends(get_dal),
) -> ReserveResponse:
    """Reserve stock."""
    return await _reserve_stock(reserve_req, dal)


@warehouse_router.post(
    "/stock/release",
    response_model=ReleaseResponse,
    status_code=status.HTTP_200_OK,
    summary=RELEASE_STOCK_SUMMARY,
    description=RELEASE_STOCK_DESC,
)
async def release_stock(
    release_req: ReleaseRequest,
    dal: StockDAL = Depends(get_dal),
) -> ReleaseResponse:
    """Release reservation."""
    result = await _release_stock(release_req, dal)
    return ReleaseResponse(**result)


@warehouse_router.post(
    "/stock/receive",
    response_model=ReceiveBatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary=RECEIVE_BATCH_SUMMARY,
    description=RECEIVE_BATCH_DESC,
)
async def receive_batch(
    receive_req: ReceiveRequest,
    dal: StockDAL = Depends(get_dal),
) -> ReceiveBatchResponse:
    """Receive batch."""
    return await _receive_batch(receive_req, dal)
