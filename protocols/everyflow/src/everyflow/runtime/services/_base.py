"""Infrastructure services for EveryFlow."""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

import attrs


if TYPE_CHECKING:
    from ..storage import StorageProvider


__all__ = [
    "ServiceBase",
]


@attrs.frozen
class ServiceBase(ABC):
    """Base class for all services."""

    storage: StorageProvider
