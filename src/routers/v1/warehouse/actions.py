"""Warehouse business logic."""

from src.routers.v1.warehouse.dal import StockDAL


class StockActions:
    def __init__(self, dal: StockDAL):
        self.dal = dal

    async def reserve(self, product_id: int, quantity: int) -> dict:
        return await self.dal.reserve(product_id, quantity)

    async def list_stock(self, skip: int = 0, limit: int = 100) -> list[dict]:
        return await self.dal.get_all(skip, limit)
