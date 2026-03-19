"""Warehouse enums."""

from enum import Enum


class StockStatus(str, Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
