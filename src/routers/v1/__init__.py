"""V1 API: health + warehouse."""

from fastapi import APIRouter

from src.routers.v1.warehouse.endpoints import warehouse_router

common_router = APIRouter(tags=["common"])


@common_router.get("/health", summary="Liveness probe")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "warehouse"}


@common_router.get("/ready", summary="Readiness probe")
async def ready() -> dict[str, str]:
    return {"status": "ready", "service": "warehouse"}


v1_router = APIRouter()
v1_router.include_router(common_router)
v1_router.include_router(warehouse_router)
