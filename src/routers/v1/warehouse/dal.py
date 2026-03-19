"""Warehouse DAL."""

from sqlalchemy.ext.asyncio import AsyncSession


class StockDAL:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def reserve(self, product_id: int, quantity: int) -> dict:
        return {"product_id": product_id, "reserved": quantity, "status": "ok"}

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[dict]:
        return []
