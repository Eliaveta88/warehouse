"""Business logic actions for warehouse endpoints."""

import logging

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
from src.services.redis import (
    acquire_lock,
    decrement_hot_stock,
    get_hot_stock,
    increment_hot_stock,
    release_lock,
    set_hot_stock,
)

logger = logging.getLogger(__name__)


async def _list_stock(
    dal: StockDAL,
    skip: int = 0,
    limit: int = 50,
) -> StockListResponse:
    """Get inventory overview."""
    stocks = await dal.list_stock(skip=skip, limit=limit)
    total = await dal.count_stock()
    items = [StockResponse(**s) for s in stocks]

    # Best-effort hot cache warm-up. Inventory API should remain available if Redis fails.
    for item in items:
        try:
            await set_hot_stock(item.product_id, item.available)
        except Exception:
            logger.exception(
                "redis_error while warming hot stock cache",
                extra={"event": "redis_error", "product_id": item.product_id},
            )

    return StockListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


async def _reserve_stock(
    reserve_req: ReserveRequest,
    dal: StockDAL,
) -> ReserveResponse:
    """Reserve stock using FEFO algorithm."""
    resource = f"product:{reserve_req.product_id}"
    lock_token: str | None = None

    try:
        lock_token = await acquire_lock(resource)
        if not lock_token:
            logger.warning(
                "lock_failed for stock reservation",
                extra={"event": "lock_failed", "resource": resource},
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Stock is being updated, retry later",
            )
        logger.info(
            "lock_acquired for stock reservation",
            extra={"event": "lock_acquired", "resource": resource},
        )
    except HTTPException:
        raise
    except Exception:
        # Keep API functional even when Redis is unavailable (reserve without lock).
        logger.exception(
            "redis_error while acquiring reservation lock",
            extra={"event": "redis_error", "resource": resource},
        )

    try:
        hot_stock: int | None = None
        try:
            hot_stock = await get_hot_stock(reserve_req.product_id)
        except Exception:
            logger.exception(
                "redis_error while reading hot stock",
                extra={
                    "event": "redis_error",
                    "product_id": reserve_req.product_id,
                },
            )

        if hot_stock is not None and hot_stock < reserve_req.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient stock to reserve",
            )

        reservation = await dal.reserve(reserve_req)
        if not reservation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient stock to reserve",
            )

        if hot_stock is not None:
            try:
                await decrement_hot_stock(reserve_req.product_id, reserve_req.quantity)
            except Exception:
                logger.exception(
                    "redis_error while decrementing hot stock",
                    extra={
                        "event": "redis_error",
                        "product_id": reserve_req.product_id,
                    },
                )

        return ReserveResponse(**reservation)
    finally:
        if lock_token:
            try:
                await release_lock(resource, lock_token)
            except Exception:
                logger.exception(
                    "redis_error while releasing reservation lock",
                    extra={"event": "redis_error", "resource": resource},
                )


async def _release_stock(
    release_req: ReleaseRequest,
    dal: StockDAL,
) -> dict:
    """Release previously made reservation."""
    resource = f"reservation:{release_req.reservation_id}"
    lock_token: str | None = None

    try:
        lock_token = await acquire_lock(resource)
        if not lock_token:
            logger.warning(
                "lock_failed for release",
                extra={"event": "lock_failed", "resource": resource},
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Stock is being updated, retry later",
            )
        logger.info(
            "lock_acquired for release",
            extra={"event": "lock_acquired", "resource": resource},
        )
    except HTTPException:
        raise
    except Exception:
        # Keep release API available if Redis is down.
        logger.exception(
            "redis_error while acquiring release lock",
            extra={"event": "redis_error", "resource": resource},
        )

    try:
        released = await dal.release(release_req.reservation_id)
        if not released:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reservation not found",
            )
        # No safe quantity/product context here; avoid incorrect hot-stock increments.
        return {"status": "released"}
    finally:
        if lock_token:
            try:
                await release_lock(resource, lock_token)
            except Exception:
                logger.exception(
                    "redis_error while releasing release lock",
                    extra={"event": "redis_error", "resource": resource},
                )


async def _receive_batch(
    receive_req: ReceiveRequest,
    dal: StockDAL,
) -> ReceiveBatchResponse:
    """Receive new batch with expiry tracking."""
    resource = f"product:{receive_req.product_id}"
    lock_token: str | None = None

    try:
        lock_token = await acquire_lock(resource)
        if not lock_token:
            logger.warning(
                "lock_failed for receive batch",
                extra={"event": "lock_failed", "resource": resource},
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Stock is being updated, retry later",
            )
        logger.info(
            "lock_acquired for receive batch",
            extra={"event": "lock_acquired", "resource": resource},
        )
    except HTTPException:
        raise
    except Exception:
        # Degraded: Redis down — receive without lock (same idea as list_stock warm-up).
        logger.exception(
            "redis_error while acquiring receive lock",
            extra={"event": "redis_error", "resource": resource},
        )

    try:
        batch = await dal.receive(receive_req)

        try:
            await increment_hot_stock(receive_req.product_id, receive_req.quantity)
        except Exception:
            logger.exception(
                "redis_error while incrementing hot stock; falling back to warm-up set",
                extra={
                    "event": "redis_error",
                    "product_id": receive_req.product_id,
                },
            )
            try:
                await set_hot_stock(receive_req.product_id, receive_req.quantity)
            except Exception:
                logger.exception(
                    "redis_error while fallback warming hot stock",
                    extra={
                        "event": "redis_error",
                        "product_id": receive_req.product_id,
                    },
                )

        return ReceiveBatchResponse(**batch)
    finally:
        if lock_token:
            try:
                await release_lock(resource, lock_token)
            except Exception:
                logger.exception(
                    "redis_error while releasing receive lock",
                    extra={"event": "redis_error", "resource": resource},
                )
