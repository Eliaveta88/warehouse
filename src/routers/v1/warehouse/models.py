"""SQLAlchemy ORM models for warehouse service."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import mapped_column

from src.database.core import Base


class Batch(Base):
    """Warehouse batch/lot database model."""

    __tablename__ = "batches"

    id: int = mapped_column(Integer, primary_key=True)
    product_id: int = mapped_column(Integer, nullable=False, index=True)
    quantity_received: float = mapped_column(Float, nullable=False)
    unit_type: str = mapped_column(String(50), nullable=False)
    expiry_date: datetime = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    batch_reference: str = mapped_column(String(100), nullable=False, unique=True, index=True)
    status: str = mapped_column(
        String(50), default="in_stock", nullable=False, index=True
    )  # in_stock, partially_reserved, fully_reserved, expired
    created_at: datetime = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "product_id": self.product_id,
            "quantity_received": self.quantity_received,
            "expiry_date": self.expiry_date,
            "batch_reference": self.batch_reference,
            "status": self.status,
        }


class Stock(Base):
    """Stock inventory database model."""

    __tablename__ = "stock"

    id: int = mapped_column(Integer, primary_key=True)
    batch_id: int = mapped_column(
        Integer,
        ForeignKey("batches.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    product_id: int = mapped_column(Integer, nullable=False, index=True)
    product_name: str = mapped_column(String(255), nullable=False)
    quantity_available: float = mapped_column(Float, nullable=False, default=0)
    quantity_reserved: float = mapped_column(Float, nullable=False, default=0)
    unit_type: str = mapped_column(String(50), nullable=False)  # unit, kg, liter, piece, etc
    cell_location: str = mapped_column(String(100), nullable=False, index=True)
    expiry_date: datetime = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    batch_reference: str = mapped_column(String(100), nullable=False, index=True)
    created_at: datetime = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: datetime = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "batch_id": self.batch_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "available": self.quantity_available,
            "reserved": self.quantity_reserved,
            "total": self.quantity_available + self.quantity_reserved,
            "cell_location": self.cell_location,
            "expiry_date": self.expiry_date,
        }


class Reservation(Base):
    """Stock reservation database model (FEFO tracking)."""

    __tablename__ = "reservations"

    id: int = mapped_column(Integer, primary_key=True)
    stock_id: int = mapped_column(
        Integer,
        ForeignKey("stock.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_id: int = mapped_column(Integer, nullable=False, index=True)
    product_id: int = mapped_column(Integer, nullable=False, index=True)
    quantity: float = mapped_column(Float, nullable=False)
    status: str = mapped_column(
        String(50), default="active", nullable=False, index=True
    )  # active, released, fulfilled
    created_at: datetime = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: datetime = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "stock_id": self.stock_id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "status": self.status,
            "created_at": self.created_at,
        }
