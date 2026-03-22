"""Warehouse schemas and models."""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class StockResponse(BaseModel):
    """Stock item response."""

    product_id: int = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    available: float = Field(..., ge=0, description="Available quantity")
    reserved: float = Field(..., ge=0, description="Reserved quantity")
    total: float = Field(..., ge=0, description="Total quantity")
    expiry_date: datetime = Field(..., description="Batch expiry date")
    cell_location: str = Field(..., description="Warehouse cell location")
    batch_id: int = Field(..., description="Batch ID")


class StockListResponse(BaseModel):
    """Paginated list of stock items."""

    items: List[StockResponse]
    total: int = Field(..., ge=0, description="Total items count")
    skip: int = Field(..., ge=0, description="Pagination offset")
    limit: int = Field(..., ge=1, le=100, description="Pagination limit")


class ReserveRequest(BaseModel):
    """Request for stock reservation."""

    product_id: int = Field(..., gt=0, description="Product ID")
    quantity: int = Field(..., gt=0, description="Quantity to reserve")
    order_id: int = Field(..., gt=0, description="Order ID")
    unit_type: str = Field(default="unit", description="Unit type (unit, kg, etc)")


class ReserveResponse(BaseModel):
    """Stock reservation response."""

    reservation_id: int = Field(..., description="Reservation ID")
    product_id: int = Field(..., description="Product ID")
    reserved_qty: int = Field(..., description="Reserved quantity")
    batch_id: int = Field(..., description="Batch ID")
    expiry_date: datetime = Field(..., description="Batch expiry date")
    status: str = Field(default="active", description="Reservation status")


class ReleaseRequest(BaseModel):
    """Request to release reservation."""

    reservation_id: int = Field(..., gt=0, description="Reservation ID")


class ReleaseResponse(BaseModel):
    """Release response."""

    status: str = Field(..., description="Release status")


class ReceiveRequest(BaseModel):
    """Request to receive batch."""

    product_id: int = Field(..., gt=0, description="Product ID")
    quantity: int = Field(..., gt=0, description="Quantity received")
    unit_type: str = Field(default="unit", description="Unit type")
    expiry_date: datetime = Field(..., description="Batch expiry date")
    cell_location: str = Field(..., min_length=1, description="Warehouse cell location")
    batch_reference: str = Field(..., min_length=1, description="Reference number from supplier")


class ReceiveBatchResponse(BaseModel):
    """Batch receive response."""

    batch_id: int = Field(..., description="Batch ID")
    product_id: int = Field(..., description="Product ID")
    quantity_received: int = Field(..., description="Quantity received")
    status: str = Field(..., description="Batch status")
