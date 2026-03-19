"""Warehouse schemas."""

from pydantic import BaseModel


class StockBase(BaseModel):
    pass


class StockResponse(BaseModel):
    pass
