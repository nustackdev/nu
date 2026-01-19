"""Observer module.

Provides subscription capabilities for storage changes with:
- Flexible filtering (import from storage.filter)
- Decoupled subscriptions from callbacks (subscribe once, bind/unbind)
- Efficient pattern matching via SubscriptionRegistry
"""

from __future__ import annotations

from .exceptions import (
    ObserverConnectionError,
    ObserverError,
    ObserverSubscriptionError,
    ObserverValidationError,
)
from .observer import ObserverProtocol
from .registry import SubscriptionRegistry
from .subscription import (
    Subscription,
)
from .types import (
    SubscriptionCallback,
    SubscriptionOptions,
    SubscriptionReceiver,
)


__all__ = [
    "ObserverConnectionError",
    "ObserverError",
    "ObserverProtocol",
    "ObserverSubscriptionError",
    "ObserverValidationError",
    "Subscription",
    "SubscriptionCallback",
    "SubscriptionOptions",
    "SubscriptionReceiver",
    "SubscriptionRegistry",
]
