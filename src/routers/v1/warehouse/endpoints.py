"""HTTP endpoints for warehouse v1."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.core import get_async_session
from src.routers.v1.warehouse.actions import _list_stock, _receive_batch
from src.routers.v1.warehouse.dal import StockDAL
from src.routers.v1.warehouse.schemas import ReceiveBatchResponse, ReceiveRequest, StockListResponse

warehouse_router = APIRouter(prefix="/warehouse", tags=["warehouse"])


async def get_dal(
    session: AsyncSession = Depends(get_async_session),
) -> StockDAL:
    return StockDAL(session=session)


@warehouse_router.get("/ping", summary="Warehouse router ping")
async def warehouse_ping() -> dict[str, str]:
    return {"status": "ok", "module": "warehouse"}


@warehouse_router.get(
    "",
    response_model=StockListResponse,
    status_code=status.HTTP_200_OK,
    summary="Список остатков на складе",
)
async def list_stock(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    dal: StockDAL = Depends(get_dal),
) -> StockListResponse:
    return await _list_stock(dal, skip=skip, limit=limit)


@warehouse_router.post(
    "/receive",
    response_model=ReceiveBatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Оприходовать партию",
)
async def receive_batch(
    body: ReceiveRequest,
    dal: StockDAL = Depends(get_dal),
) -> ReceiveBatchResponse:
    return await _receive_batch(body, dal)
