import unittest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from src.routers.v1.warehouse.actions import _receive_batch, _reserve_stock
from src.routers.v1.warehouse.schemas import ReceiveRequest, ReserveRequest
from src.config import redis_cfg
from src.services import redis as redis_service


class WarehouseRedisIntegrationTests(unittest.IsolatedAsyncioTestCase):
    def test_redis_cfg_hardening_fields_present(self) -> None:
        self.assertGreater(redis_cfg.socket_timeout_seconds, 0)
        self.assertGreater(redis_cfg.socket_connect_timeout_seconds, 0)
        self.assertGreater(redis_cfg.health_check_interval_seconds, 0)
        self.assertGreater(redis_cfg.max_connections, 0)

    async def test_get_redis_uses_from_url_with_hardening_kwargs(self) -> None:
        redis_service._pool = None
        fake_client = AsyncMock()
        with patch(
            "src.services.redis.aioredis.from_url",
            return_value=fake_client,
        ) as from_url_mock:
            client = await redis_service.get_redis()
        self.assertIs(client, fake_client)
        from_url_mock.assert_called_once_with(
            redis_cfg.url,
            decode_responses=redis_cfg.decode_responses,
            socket_timeout=redis_cfg.socket_timeout_seconds,
            socket_connect_timeout=redis_cfg.socket_connect_timeout_seconds,
            health_check_interval=redis_cfg.health_check_interval_seconds,
            max_connections=redis_cfg.max_connections,
        )
        redis_service._pool = None

    async def test_reserve_stock_lock_conflict_returns_409(self) -> None:
        dal = AsyncMock()
        reserve_req = ReserveRequest(product_id=1, quantity=5, order_id=2, unit_type="unit")
        with patch(
            "src.routers.v1.warehouse.actions.acquire_lock",
            new=AsyncMock(return_value=None),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await _reserve_stock(reserve_req, dal)
        self.assertEqual(ctx.exception.status_code, 409)

    async def test_receive_batch_fallbacks_to_set_hot_stock(self) -> None:
        dal = AsyncMock()
        dal.receive.return_value = {
            "batch_id": 1,
            "product_id": 10,
            "quantity_received": 7,
            "status": "in_stock",
        }
        req = ReceiveRequest(
            product_id=10,
            quantity=7,
            unit_type="unit",
            expiry_date=datetime(2030, 1, 1),
            cell_location="A-1",
            batch_reference="B-1",
        )
        with (
            patch(
                "src.routers.v1.warehouse.actions.acquire_lock",
                new=AsyncMock(return_value="token-1"),
            ),
            patch(
                "src.routers.v1.warehouse.actions.release_lock",
                new=AsyncMock(return_value=True),
            ),
            patch(
                "src.routers.v1.warehouse.actions.increment_hot_stock",
                new=AsyncMock(side_effect=RuntimeError("redis err")),
            ),
            patch(
                "src.routers.v1.warehouse.actions.set_hot_stock",
                new=AsyncMock(),
            ) as set_mock,
        ):
            result = await _receive_batch(req, dal)
        self.assertEqual(result.product_id, 10)
        set_mock.assert_awaited_once()
