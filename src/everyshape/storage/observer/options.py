"""Subscription options.

Implements:
- Filters for subscription filtering
- SubscriptionOptions class
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from everyshape.loc import key


__all__ = [
    "CompositeFilter",
    "LengthFilter",
    "PrefixFilter",
    "SubscriptionFilter",
    "SubscriptionOptions",
    "SuffixFilter",
    "WildcardFilter",
]


# =============================================================================
# Subscription Options
# =============================================================================


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
        ...     filter=WildcardFilter(pattern=("users", "*", "profile"))
        ... )

        >>> # Subscribe to keys with specific prefix AND length
        >>> opts = SubscriptionOptions(
        ...     filter=CompositeFilter(
        ...         filters=(
        ...             PrefixFilter(prefix=("users",)),
        ...             LengthFilter(length=3),
        ...         )
        ...     )
        ... )
    """

    filter: SubscriptionFilter
    """Filter that determines which keys trigger notifications."""

    def __hash__(self) -> int:
        """Return hash based on filter."""
        return hash(self.filter)

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, SubscriptionOptions):
            return NotImplemented
        return self.filter == other.filter


# =============================================================================
# Filter Types
# =============================================================================


class SubscriptionFilter(ABC):
    """Base class for subscription filters.

    Filters define matching criteria for keys. When a key is modified,
    the filter determines if the subscription should be notified.
    """

    @abstractmethod
    def matches(self, key: key.Key) -> bool:
        """Check if a key matches this filter.

        Args:
            key: Key to check against the filter.

        Returns:
            True if the key matches the filter criteria.
        """
        raise NotImplementedError

    @abstractmethod
    def __hash__(self) -> int:
        """Return hash for use in sets and dicts."""
        raise NotImplementedError

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """Check equality with another filter."""
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class PrefixFilter(SubscriptionFilter):
    """Match keys that start with a given prefix.

    Examples:
        >>> f = PrefixFilter(prefix=("users",))
        >>> f.matches(("users", "alice"))  # True
        >>> f.matches(("users", "alice", "profile"))  # True
        >>> f.matches(("posts",))  # False
    """

    prefix: key.Key
    """Prefix that keys must start with."""

    def matches(self, key: key.Key) -> bool:
        """Check if key starts with the prefix."""
        if len(key) < len(self.prefix):
            return False
        return key[: len(self.prefix)] == self.prefix

    def __hash__(self) -> int:
        """Return hash based on prefix."""
        return hash(("prefix", self.prefix))

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, PrefixFilter):
            return NotImplemented
        return self.prefix == other.prefix


@dataclass(frozen=True, slots=True)
class SuffixFilter(SubscriptionFilter):
    """Match keys that end with a given suffix.

    Examples:
        >>> f = SuffixFilter(suffix=("profile",))
        >>> f.matches(("users", "alice", "profile"))  # True
        >>> f.matches(("posts", "123", "profile"))  # True
        >>> f.matches(("users", "alice"))  # False
    """

    suffix: key.Key
    """Suffix that keys must end with."""

    def matches(self, key: key.Key) -> bool:
        """Check if key ends with the suffix."""
        if len(key) < len(self.suffix):
            return False
        return key[-len(self.suffix) :] == self.suffix

    def __hash__(self) -> int:
        """Return hash based on suffix."""
        return hash(("suffix", self.suffix))

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, SuffixFilter):
            return NotImplemented
        return self.suffix == other.suffix


# Sentinel for wildcard matching
WILDCARD = "*"
"""Wildcard segment that matches any single key segment."""


@dataclass(frozen=True, slots=True)
class WildcardFilter(SubscriptionFilter):
    """Match keys with wildcard patterns.

    Use '*' to match any single segment in the pattern.

    Examples:
        >>> f = WildcardFilter(pattern=("users", "*", "profile"))
        >>> f.matches(("users", "alice", "profile"))  # True
        >>> f.matches(("users", "bob", "profile"))  # True
        >>> f.matches(("users", "alice", "settings"))  # False
        >>> f.matches(("users", "alice"))  # False (length mismatch)
    """

    pattern: key.Key
    """Pattern with wildcards. '*' matches any single segment."""

    def matches(self, key: key.Key) -> bool:
        """Check if key matches the wildcard pattern."""
        if len(key) != len(self.pattern):
            return False
        return all(p == WILDCARD or k == p for k, p in zip(key, self.pattern, strict=True))

    def __hash__(self) -> int:
        """Return hash based on pattern."""
        return hash(("wildcard", self.pattern))

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, WildcardFilter):
            return NotImplemented
        return self.pattern == other.pattern


@dataclass(frozen=True, slots=True)
class LengthFilter(SubscriptionFilter):
    """Match keys with exact length.

    Examples:
        >>> f = LengthFilter(length=3)
        >>> f.matches(("a", "b", "c"))  # True
        >>> f.matches(("a", "b"))  # False
        >>> f.matches(("a", "b", "c", "d"))  # False
    """

    length: int
    """Exact length that keys must have."""

    def matches(self, key: key.Key) -> bool:
        """Check if key has the exact length."""
        return len(key) == self.length

    def __hash__(self) -> int:
        """Return hash based on length."""
        return hash(("length", self.length))

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, LengthFilter):
            return NotImplemented
        return self.length == other.length


@dataclass(frozen=True, slots=True)
class CompositeFilter(SubscriptionFilter):
    """Combine multiple filters with AND logic.

    All contained filters must match for the composite to match.

    Examples:
        >>> f = CompositeFilter(
        ...     filters=(
        ...         PrefixFilter(prefix=("users",)),
        ...         LengthFilter(length=3),
        ...     )
        ... )
        >>> f.matches(("users", "alice", "profile"))  # True
        >>> f.matches(("users", "alice"))  # False (length mismatch)
        >>> f.matches(("posts", "123", "title"))  # False (prefix mismatch)
    """

    filters: tuple[SubscriptionFilter, ...]
    """Tuple of filters to combine with AND logic."""

    def matches(self, key: key.Key) -> bool:
        """Check if key matches all filters."""
        return all(f.matches(key) for f in self.filters)

    def __hash__(self) -> int:
        """Return hash based on all filters."""
        return hash(("composite", self.filters))

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, CompositeFilter):
            return False
        return self.filters == other.filters
