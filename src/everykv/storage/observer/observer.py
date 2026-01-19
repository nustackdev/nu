"""Protocol definitions for observer system.

Defines the abstract interfaces for observers and subscriptions.
The new subscription system provides:
- Flexible filtering (prefix, suffix, wildcard, length, composite)
- Decoupled subscription from callbacks (subscribe once, bind/unbind callbacks)
- Efficient pattern matching with hash-based indexing
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable


if TYPE_CHECKING:
    from everykv.loc import key
    from everykv.storage import CodecProtocol

    from .subscription import (
        Subscription,
    )
    from .types import SubscriptionOptions


__all__ = [
    "ObserverProtocol",
]


@runtime_checkable
class ObserverProtocol[EncodedKeyT](Protocol):
    """Protocol for observable adapters.

    Observers provide subscription capabilities for storage changes, such as:
    - Flexible filtering (prefix, suffix, wildcard, length, composite)
    - Decoupled subscriptions from callbacks
    - Efficient pattern matching

    Examples:
        >>> # Subscribe with options
        >>> sub = observer.subscribe(
        ...     SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        ... )
        >>> sub.bind(lambda key: print(f"Changed: {key}"))
    """

    @property
    def codec(self) -> CodecProtocol[EncodedKeyT, Any]:
        """Get key codec for encoding topics."""
        ...

    def subscribe(self, options: SubscriptionOptions) -> Subscription:
        """Subscribe to key changes with flexible filtering.

        Args:
            options: Subscription options including filter specification.

        Returns:
            Subscription object for binding callbacks and managing lifecycle.

        Raises:
            ObserverError: If subscription fails.

        Examples:
            >>> # Subscribe to all keys under "users"
            >>> sub = observer.subscribe(
            ...     SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
            ... )

            >>> # Subscribe with wildcard pattern
            >>> sub = observer.subscribe(
            ...     SubscriptionOptions(
            ...         filter=WildcardFilter(pattern=("users", "*", "profile"))
            ...     )
            ... )

            >>> # Subscribe to keys with specific prefix AND length
            >>> sub = observer.subscribe(
            ...     SubscriptionOptions(
            ...         filter=PrefixFilter(prefix=("users",)) & LengthFilter(length=3)
            ...     )
            ... )
        """
        ...

    def notify(self, topic: key.Key) -> None:
        """Notify observers of a change at the specified topic.

        Args:
            topic: Topic identifying changed state.

        Raises:
            ObserverError: If notification fails.
        """
        ...

    def _close_subscription(self, subscription: Subscription) -> None:
        """Internal method to close a subscription.

        Called by Subscription.close() to remove subscription from observer.

        Args:
            subscription: Subscription to close.
        """
        ...
