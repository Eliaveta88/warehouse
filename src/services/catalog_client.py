"""HTTP client for catalog service."""

from __future__ import annotations

import logging

import httpx

from src.config import integration_cfg

logger = logging.getLogger(__name__)


async def fetch_product(product_id: int) -> dict | None:
    """GET /api/v1/catalog/products/{id}."""
    url = f"{integration_cfg.catalog_base_url}/api/v1/catalog/products/{product_id}"
    timeout = httpx.Timeout(integration_cfg.http_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(url)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
