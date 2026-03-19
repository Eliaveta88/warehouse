"""Business logic actions for warehouse endpoints."""

from fastapi import HTTPException, status

from src.routers.v1.warehouse.dal import StockDAL
from src.routers.v1.warehouse.schemas import (
    ReserveRequest,
    ReserveResponse,
    ReleaseRequest,
    ReceiveRequest,
    ReceiveBatchResponse,
    StockListResponse,
    StockResponse,
)


async def _list_stock(
    dal: StockDAL,
    skip: int = 0,
    limit: int = 50,
) -> StockListResponse:
    """Get inventory overview."""
    stocks = await dal.list_stock(skip=skip, limit=limit)
    total = await dal.count_stock()
    return StockListResponse(
        items=[StockResponse(**s) for s in stocks],
        total=total,
        skip=skip,
        limit=limit,
    )


async def _reserve_stock(
    reserve_req: ReserveRequest,
    dal: StockDAL,
) -> ReserveResponse:
    """Reserve stock using FEFO algorithm."""
    reservation = await dal.reserve(reserve_req)
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient stock to reserve",
        )
    return ReserveResponse(**reservation)


async def _release_stock(
    release_req: ReleaseRequest,
    dal: StockDAL,
) -> dict:
    """Release previously made reservation."""
    released = await dal.release(release_req.reservation_id)
    if not released:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found",
        )
    return {"status": "released"}


async def _receive_batch(
    receive_req: ReceiveRequest,
    dal: StockDAL,
) -> ReceiveBatchResponse:
    """Receive new batch with expiry tracking."""
    batch = await dal.receive(receive_req)
    return ReceiveBatchResponse(**batch)
