"""Efficient subscription registry with hash-based indexing.

The registry provides O(key_length) lookup instead of O(n) iteration
over all subscriptions. It maintains separate indexes for different
filter types and uses hash-based lookups.
"""

from __future__ import annotations

import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .options import (
    WILDCARD,
    CompositeFilter,
    LengthFilter,
    PrefixFilter,
    SubscriptionFilter,
    SuffixFilter,
    WildcardFilter,
)


if TYPE_CHECKING:
    from everyshape.loc import key

    from .subscription import Subscription


__all__ = [
    "SubscriptionRegistry",
]


@dataclass
class SubscriptionRegistry:
    """Thread-safe registry for efficient subscription matching.

    Maintains multiple indexes for O(1) hash-based lookups:
    - Prefix index: prefix tuple -> list of subscriptions
    - Suffix index: suffix tuple -> list of subscriptions
    - Length index: length -> list of subscriptions
    - Wildcard index: (length, fixed_positions) -> list of subscriptions
    - All subscriptions set for cleanup

    When a key is modified, the registry efficiently finds matching
    subscriptions without iterating over all subscriptions.
    """

    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    # Index by prefix (for PrefixFilter)
    # Maps prefix tuple -> set of subscriptions
    _prefix_index: dict[key.Key, set[Subscription]] = field(
        default_factory=lambda: defaultdict(set), init=False
    )

    # Index by suffix (for SuffixFilter)
    # Maps suffix tuple -> set of subscriptions
    _suffix_index: dict[key.Key, set[Subscription]] = field(
        default_factory=lambda: defaultdict(set), init=False
    )

    # Index by length (for LengthFilter)
    # Maps length -> set of subscriptions
    _length_index: dict[int, set[Subscription]] = field(
        default_factory=lambda: defaultdict(set), init=False
    )

    # Index for wildcard patterns (for WildcardFilter)
    # Maps (length, signature_hash) -> set of subscriptions
    # Signature is a frozenset of (position, value) for non-wildcard positions
    _wildcard_index: dict[tuple[int, frozenset], set[Subscription]] = field(
        default_factory=lambda: defaultdict(set), init=False
    )

    # Index for composite filters (subscriptions with multiple filters)
    # These are indexed by their "primary" filter and verified on match
    _composite_subscriptions: set[Subscription] = field(default_factory=set, init=False)

    # All subscriptions for cleanup and iteration
    _all_subscriptions: set[Subscription] = field(default_factory=set, init=False)

    def add(self, subscription: Subscription) -> None:
        """Add a subscription to the registry.

        The subscription is indexed based on its filter type for
        efficient matching.

        Args:
            subscription: Subscription to add.
        """
        with self._lock:
            if subscription in self._all_subscriptions:
                return

            self._all_subscriptions.add(subscription)
            self._index_filter(subscription, subscription.filter)

    def _index_filter(self, subscription: Subscription, filt: SubscriptionFilter) -> None:
        """Index a subscription by its filter type.

        Args:
            subscription: Subscription to index.
            filt: Filter to index by.
        """
        if isinstance(filt, PrefixFilter):
            self._prefix_index[filt.prefix].add(subscription)

        elif isinstance(filt, SuffixFilter):
            self._suffix_index[filt.suffix].add(subscription)

        elif isinstance(filt, LengthFilter):
            self._length_index[filt.length].add(subscription)

        elif isinstance(filt, WildcardFilter):
            signature = self._wildcard_signature(filt.pattern)
            self._wildcard_index[(len(filt.pattern), signature)].add(subscription)

        elif isinstance(filt, CompositeFilter):
            self._composite_subscriptions.add(subscription)
            # Also index by the first filter for faster narrowing
            if filt.filters:
                self._index_filter(subscription, filt.filters[0])

    def remove(self, subscription: Subscription) -> None:
        """Remove a subscription from the registry.

        Args:
            subscription: Subscription to remove.
        """
        with self._lock:
            if subscription not in self._all_subscriptions:
                return

            self._all_subscriptions.discard(subscription)
            self._unindex_filter(subscription, subscription.filter)

    def _unindex_filter(self, subscription: Subscription, filt: SubscriptionFilter) -> None:
        """Remove subscription from filter index.

        Args:
            subscription: Subscription to remove.
            filt: Filter to unindex from.
        """
        if isinstance(filt, PrefixFilter):
            self._prefix_index[filt.prefix].discard(subscription)
            if not self._prefix_index[filt.prefix]:
                del self._prefix_index[filt.prefix]

        elif isinstance(filt, SuffixFilter):
            self._suffix_index[filt.suffix].discard(subscription)
            if not self._suffix_index[filt.suffix]:
                del self._suffix_index[filt.suffix]

        elif isinstance(filt, LengthFilter):
            self._length_index[filt.length].discard(subscription)
            if not self._length_index[filt.length]:
                del self._length_index[filt.length]

        elif isinstance(filt, WildcardFilter):
            signature = self._wildcard_signature(filt.pattern)
            idx_key = (len(filt.pattern), signature)
            self._wildcard_index[idx_key].discard(subscription)
            if not self._wildcard_index[idx_key]:
                del self._wildcard_index[idx_key]

        elif isinstance(filt, CompositeFilter):
            self._composite_subscriptions.discard(subscription)
            if filt.filters:
                self._unindex_filter(subscription, filt.filters[0])

    def match(self, key: key.Key) -> list[Subscription]:
        """Find all subscriptions matching a key.

        Uses hash-based lookups for efficient matching.

        Args:
            key: Key to match against subscriptions.

        Returns:
            List of matching subscriptions (no duplicates).
        """
        with self._lock:
            matches: set[Subscription] = set()

            # Match prefix filters: check all prefixes of the key
            for i in range(1, len(key) + 1):
                prefix = key[:i]
                if prefix in self._prefix_index:
                    matches.update(self._prefix_index[prefix])

            # Match suffix filters: check all suffixes of the key
            for i in range(len(key)):
                suffix = key[i:]
                if suffix in self._suffix_index:
                    matches.update(self._suffix_index[suffix])

            # Match length filters
            if len(key) in self._length_index:
                matches.update(self._length_index[len(key)])

            # Match wildcard filters of same length
            key_len = len(key)
            for idx_key, subs in self._wildcard_index.items():
                pattern_len, _ = idx_key
                if pattern_len == key_len:
                    # Verify each subscription's wildcard pattern matches
                    for sub in subs:
                        if sub.filter.matches(key):
                            matches.add(sub)

            # For composite filters, verify the full match
            verified_matches: list[Subscription] = []
            for sub in matches:
                if sub.filter.matches(key):
                    verified_matches.append(sub)

            return verified_matches

    def clear(self) -> None:
        """Remove all subscriptions from the registry."""
        with self._lock:
            self._prefix_index.clear()
            self._suffix_index.clear()
            self._length_index.clear()
            self._wildcard_index.clear()
            self._composite_subscriptions.clear()
            self._all_subscriptions.clear()

    @staticmethod
    def _wildcard_signature(pattern: key.Key) -> frozenset[tuple[int, key.KeySegment]]:
        """Compute signature for a wildcard pattern.

        The signature is a frozenset of (position, value) pairs for
        all non-wildcard positions. This allows efficient grouping
        of patterns with the same fixed positions.

        Args:
            pattern: Wildcard pattern.

        Returns:
            Frozenset of (position, value) for non-wildcard segments.
        """
        return frozenset((i, seg) for i, seg in enumerate(pattern) if seg != WILDCARD)

    def __len__(self) -> int:
        """Return number of subscriptions in the registry."""
        with self._lock:
            return len(self._all_subscriptions)

    def __contains__(self, subscription: Subscription) -> bool:
        """Check if subscription is in the registry."""
        with self._lock:
            return subscription in self._all_subscriptions
