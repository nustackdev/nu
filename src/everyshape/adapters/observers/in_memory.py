"""In-memory observer implementation with thread-safe subscription management.

The InMemoryObserver provides efficient pattern matching using the
SubscriptionRegistry from the base class. All subscription logic is
handled by BaseObserver - this class only provides connection management.
"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from ._base import BaseObserver


if TYPE_CHECKING:
    from logging import Logger

    from everyshape.storage import (
        ObserverProtocol,
    )


logger: Logger = getLogger(__name__)


__all__ = [
    "InMemoryObserver",
]


class InMemoryObserver(BaseObserver[str]):
    """In-memory observer with thread-safe subscription management.

    Uses the SubscriptionRegistry from BaseObserver for efficient O(key_length)
    pattern matching instead of O(n) iteration over all subscriptions.

    Supports both the new API (subscribe with options + bind/unbind) and
    the legacy API (subscribe with prefix and callback).

    Examples:
        >>> from everyshape.storage.observer.subscription import (
        ...     PrefixFilter,
        ...     SubscriptionOptions,
        ... )

        >>> # New API
        >>> observer = InMemoryObserver(codec)
        >>> observer.connect()
        >>> sub = observer.subscribe(
        ...     SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        ... )
        >>> sub.bind(lambda key: print(f"Changed: {key}"))
        >>> observer.notify(("users", "alice"))  # Prints: Changed: ('users', 'alice')
        >>> sub.close()
        >>> observer.disconnect()

        >>> # Legacy API
        >>> with InMemoryObserver(codec) as observer:
        ...     sub = observer.subscribe_legacy(
        ...         prefix=("users",),
        ...         callback=lambda key: print(f"Changed: {key}"),
        ...         prefix_depth=-1,
        ...     )
        ...     observer.notify(("users", "alice"))
        ...     sub.close()
    """

    def _connect_impl(self) -> None:
        """Initialize connection state.

        The SubscriptionRegistry is created by the base class.
        """
        pass

    def _disconnect_impl(self) -> None:
        """Clean up connection state.

        The SubscriptionRegistry is cleared by the base class.
        """
        pass


if TYPE_CHECKING:
    _: type[ObserverProtocol[str]] = InMemoryObserver
