"""Observer module.

Provides subscription capabilities for storage changes with:
- Flexible filtering (prefix, suffix, wildcard, length, composite)
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
from .options import (
    WILDCARD,
    CompositeFilter,
    LengthFilter,
    PrefixFilter,
    SubscriptionFilter,
    SubscriptionOptions,
    SuffixFilter,
    WildcardFilter,
)
from .registry import SubscriptionRegistry
from .subscription import (
    Subscription,
)
from .types import (
    SubscriptionCallback,
    SubscriptionReceiver,
)


__all__ = [  # noqa: RUF022
    # Protocols
    "ObserverProtocol",
    # Subscription types
    "Subscription",
    "SubscriptionOptions",
    "SubscriptionCallback",
    "SubscriptionReceiver",
    "SubscriptionRegistry",
    # Filter types
    "SubscriptionFilter",
    "PrefixFilter",
    "SuffixFilter",
    "WildcardFilter",
    "LengthFilter",
    "CompositeFilter",
    "WILDCARD",
    # Errors
    "ObserverError",
    "ObserverConnectionError",
    "ObserverSubscriptionError",
    "ObserverValidationError",
]
