import os
from abc import ABC
from dataclasses import asdict, dataclass


class CfgBase(ABC):
    dict: callable = asdict


@dataclass
class RedisCfg(CfgBase):
    """Redis configuration for distributed locks (Redlock), hot stock levels, and inventory cache."""
    host: str = os.getenv("REDIS_HOST")
    port: int = os.getenv("REDIS_PORT")
    db: int = os.getenv("REDIS_DB")
    password: str = os.getenv("REDIS_PASSWORD")


redis_cfg = RedisCfg()
