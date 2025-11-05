"""Observer module."""

from __future__ import annotations

from .exceptions import (
    ObserverConnectionError,
    ObserverError,
    ObserverSubscriptionError,
    ObserverValidationError,
)
from .observer import ObserverProtocol, SubscriptionProtocol


__all__ = [  # noqa: RUF022
    # Protocols
    "ObserverProtocol",
    "SubscriptionProtocol",
    # Errors
    "ObserverError",
    "ObserverConnectionError",
    "ObserverSubscriptionError",
    "ObserverValidationError",
]
