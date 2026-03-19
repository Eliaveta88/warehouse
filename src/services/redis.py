"""Redis service for warehouse: distributed locks (Redlock) and hot stock balances."""

from __future__ import annotations

import uuid

import redis.asyncio as aioredis

from src.config import redis_cfg

_KEY_PREFIX = "warehouse"
_LOCK = f"{_KEY_PREFIX}:lock:"
_HOT_STOCK = f"{_KEY_PREFIX}:stock"

_LOCK_TTL_MS = 5_000  # 5 seconds auto-release

_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Return the shared async Redis connection (lazy-init)."""
    global _pool
    if _pool is None:
        _pool = aioredis.Redis(
            host=redis_cfg.host,
            port=redis_cfg.port,
            db=redis_cfg.db,
            password=redis_cfg.password or None,
            decode_responses=redis_cfg.decode_responses,
        )
    return _pool


async def close_redis() -> None:
    """Gracefully close the Redis connection pool."""
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


# ---------------------------------------------------------------------------
# Distributed Lock  (simplified Redlock for single-node)
# ---------------------------------------------------------------------------

_UNLOCK_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""


async def acquire_lock(
    resource: str,
    ttl_ms: int = _LOCK_TTL_MS,
) -> str | None:
    """Try to acquire a distributed lock on *resource* (e.g. ``sku:12345``).

    Returns a unique *lock_token* on success, ``None`` if the resource
    is already locked.  The lock auto-expires after *ttl_ms*.
    """
    r = await get_redis()
    token = uuid.uuid4().hex
    acquired = await r.set(
        f"{_LOCK}{resource}",
        token,
        nx=True,
        px=ttl_ms,
    )
    return token if acquired else None


async def release_lock(resource: str, token: str) -> bool:
    """Release a previously acquired lock.

    Only the owner (matching *token*) can release it — prevents
    accidental release by another process.
    """
    r = await get_redis()
    result = await r.eval(_UNLOCK_SCRIPT, 1, f"{_LOCK}{resource}", token)
    return result == 1


# ---------------------------------------------------------------------------
# Hot stock balances  (Hash: product_id -> available_qty)
# ---------------------------------------------------------------------------


async def set_hot_stock(product_id: int, available: int) -> None:
    """Update the hot (in-memory) available stock for a product."""
    r = await get_redis()
    await r.hset(_HOT_STOCK, str(product_id), str(available))


async def get_hot_stock(product_id: int) -> int | None:
    """Return hot available stock for *product_id*, or None if not cached."""
    r = await get_redis()
    val = await r.hget(_HOT_STOCK, str(product_id))
    return int(val) if val is not None else None


async def get_all_hot_stock() -> dict[int, int]:
    """Return all cached hot stock levels as ``{product_id: available}``."""
    r = await get_redis()
    raw = await r.hgetall(_HOT_STOCK)
    return {int(k): int(v) for k, v in raw.items()}


async def decrement_hot_stock(product_id: int, qty: int) -> int:
    """Atomically decrease hot stock and return new value."""
    r = await get_redis()
    return await r.hincrby(_HOT_STOCK, str(product_id), -qty)


async def increment_hot_stock(product_id: int, qty: int) -> int:
    """Atomically increase hot stock (release/receive) and return new value."""
    r = await get_redis()
    return await r.hincrby(_HOT_STOCK, str(product_id), qty)


async def delete_hot_stock(product_id: int) -> None:
    """Remove a product from the hot stock cache."""
    r = await get_redis()
    await r.hdel(_HOT_STOCK, str(product_id))
