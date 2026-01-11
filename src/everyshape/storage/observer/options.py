"""Subscription options.

Implements SubscriptionOptions class.
Filter types are imported from the shared filter module.
"""

from __future__ import annotations

from dataclasses import dataclass

from everyshape.storage.filter import (
    WILDCARD,
    And,
    Filter,
    LengthFilter,
    PrefixFilter,
    SuffixFilter,
    WildcardFilter,
)


__all__ = [
    "WILDCARD",
    "CompositeFilter",
    "LengthFilter",
    "PrefixFilter",
    "SubscriptionFilter",
    "SubscriptionOptions",
    "SuffixFilter",
    "WildcardFilter",
]


# Aliases for backward compatibility
SubscriptionFilter = Filter
"""Alias for Filter. Use Filter directly for new code."""

CompositeFilter = And
"""Alias for And. Use And directly for new code."""


@dataclass(frozen=True, slots=True)
class SubscriptionOptions:
    """Options for creating a subscription.

    Attributes:
        filter: Filter that determines which keys trigger notifications.

    Examples:
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
