from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from ..base import BaseService

ServiceT = TypeVar("ServiceT", bound="BaseService")


class ServiceState(Enum):
    """Service lifecycle states."""

    CREATED = auto()
    INITIALIZING = auto()
    INITIALIZED = auto()
    SHUTTING_DOWN = auto()
    SHUTDOWN = auto()
    ERROR = auto()
