"""Data Access Layer for warehouse operations."""

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.routers.v1.warehouse.models import Stock, Reservation, Batch
from src.routers.v1.warehouse.schemas import (
    ReserveRequest,
    ReleaseRequest,
    ReceiveRequest,
)


class StockDAL:
    """Data Access Layer for stock management."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_stock(self, skip: int = 0, limit: int = 100) -> list[dict]:
        """List all stock items with pagination (FEFO order)."""
        stmt = (
            select(Stock)
            .order_by(Stock.expiry_date.asc())  # Oldest first
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        stocks = result.scalars().all()
        return [s.to_dict() for s in stocks]

    async def count_stock(self) -> int:
        """Get total stock count."""
        stmt = select(func.count(Stock.id))
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def reserve(self, reserve_req: ReserveRequest) -> dict | None:
        """Reserve stock using FEFO algorithm (First-Expiry-First-Out)."""
        # 1. Find oldest batch with sufficient quantity
        stmt = (
            select(Stock)
            .where(
                Stock.product_id == reserve_req.product_id,
                Stock.quantity_available >= reserve_req.quantity,
            )
            .order_by(Stock.expiry_date.asc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        stock = result.scalar_one_or_none()

        if not stock:
            return None

        # 2. Create Reservation record
        reservation = Reservation(
            stock_id=stock.id,
            order_id=reserve_req.order_id,
            product_id=reserve_req.product_id,
            quantity=reserve_req.quantity,
            status="active",
        )
        self.session.add(reservation)

        # 3. Update Stock quantities
        await self.session.execute(
            update(Stock)
            .where(Stock.id == stock.id)
            .values(
                quantity_available=Stock.quantity_available - reserve_req.quantity,
                quantity_reserved=Stock.quantity_reserved + reserve_req.quantity,
            )
        )

        await self.session.flush()

        # 4. Return reservation details
        return {
            "id": reservation.id,
            "stock_id": stock.id,
            "product_id": reserve_req.product_id,
            "reserved_qty": reserve_req.quantity,
            "batch_id": stock.batch_id,
            "expiry_date": stock.expiry_date,
            "status": "active",
        }

    async def release(self, reservation_id: int) -> bool:
        """Release previously made reservation."""
        # 1. Find reservation by ID
        stmt = select(Reservation).where(Reservation.id == reservation_id)
        result = await self.session.execute(stmt)
        reservation = result.scalar_one_or_none()

        if not reservation:
            return False

        # 2. Update Stock (decrease reserved, increase available)
        await self.session.execute(
            update(Stock)
            .where(Stock.id == reservation.stock_id)
            .values(
                quantity_available=Stock.quantity_available + reservation.quantity,
                quantity_reserved=Stock.quantity_reserved - reservation.quantity,
            )
        )

        # 3. Mark reservation as cancelled
        await self.session.execute(
            update(Reservation)
            .where(Reservation.id == reservation_id)
            .values(status="released")
        )

        await self.session.flush()
        return True

    async def receive(self, receive_req: ReceiveRequest) -> dict:
        """Receive new batch."""
        # 1. Create Batch record
        batch = Batch(
            product_id=receive_req.product_id,
            quantity_received=receive_req.quantity,
            unit_type=receive_req.unit_type,
            expiry_date=receive_req.expiry_date,
            batch_reference=receive_req.batch_reference,
            status="in_stock",
        )
        self.session.add(batch)
        await self.session.flush()

        # 2. Create Stock record for this batch
        stock = Stock(
            batch_id=batch.id,
            product_id=receive_req.product_id,
            product_name="Unknown",  # TODO: Fetch from catalog
            quantity_available=receive_req.quantity,
            quantity_reserved=0,
            unit_type=receive_req.unit_type,
            cell_location=receive_req.cell_location,
            expiry_date=receive_req.expiry_date,
            batch_reference=receive_req.batch_reference,
        )
        self.session.add(stock)
        await self.session.flush()

        # 3. Return batch details
        return {
            "batch_id": batch.id,
            "product_id": receive_req.product_id,
            "quantity_received": receive_req.quantity,
            "status": "in_stock",
        }
