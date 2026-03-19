"""Warehouse v1 HTTP endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from src.routers.v1.warehouse.actions import StockActions
from src.routers.v1.warehouse.dal import StockDAL

warehouse_router = APIRouter(prefix="/warehouse", tags=["warehouse"])


async def get_actions() -> StockActions:
    dal = StockDAL(session=None)  # type: ignore
    return StockActions(dal)


@warehouse_router.post("/stock/reserve", summary="Reserve stock")
async def reserve_stock(
    product_id: int,
    quantity: int,
    actions: Annotated[StockActions, Depends(get_actions)],
) -> dict:
    return await actions.reserve(product_id, quantity)


@warehouse_router.get("/stock", summary="List stock")
async def list_stock(
    skip: int = 0,
    limit: int = 50,
    actions: Annotated[StockActions, Depends(get_actions)] = Depends(
        get_actions
    ),
) -> list[dict]:
    return await actions.list_stock(skip, limit)
