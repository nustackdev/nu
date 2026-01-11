"""Subscription options."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from everyshape.storage.filter import Filter


__all__ = [
    "SubscriptionOptions",
]


@dataclass(frozen=True, slots=True)
class SubscriptionOptions:
    """Options for creating a subscription.

    Attributes:
        filter: Filter that determines which keys trigger notifications.

    Examples:
        >>> from everyshape.storage.filter import (
        ...     PrefixFilter,
        ...     LengthFilter,
        ...     WildcardFilter,
        ...     WILDCARD,
        ... )

        >>> # Subscribe to all keys under "users"
        >>> opts = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))

        >>> # Subscribe to keys matching a wildcard pattern
        >>> opts = SubscriptionOptions(
        ...     filter=WildcardFilter(pattern=("users", WILDCARD, "profile"))
        ... )

        >>> # Subscribe to keys with specific prefix AND length
        >>> opts = SubscriptionOptions(
        ...     filter=PrefixFilter(prefix=("users",)) & LengthFilter(length=3)
        ... )
    """

    filter: Filter
    """Filter that determines which keys trigger notifications."""

    def __hash__(self) -> int:
        """Return hash based on filter."""
        return hash(self.filter)

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, SubscriptionOptions):
            return NotImplemented
        return self.filter == other.filter
