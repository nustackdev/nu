"""Abstract compliance test suite for ObserverProtocol implementations.

This module provides a test framework for verifying that observer implementations
correctly implement the ObserverProtocol interface. These are compliance tests
that verify the subscription and notification system works correctly.

Usage:
    Inherit from compliance classes and override the required fixtures:

    ```python
    from tests.compliance.test_observer_protocol import (
        RegistryCompliance,
        ObserverCompliance,
    )


    class TestMyRegistry(RegistryCompliance):
        @pytest.fixture
        def registry(self):
            return MyRegistry()


    class TestMyObserver(ObserverCompliance):
        @pytest.fixture
        def observable_storage(self):
            return MyObservableStorage()
    ```

Test Coverage:
    RegistryCompliance:
        - Registry operations (add, remove, match, clear)
        - Filter types: Prefix, Suffix, Length, Wildcard, And, Or
        - Custom filter support
        - Multiple subscriptions matching

    ObserverCompliance:
        - Subscription creation and notification flow
        - Callback binding and unbinding
        - Notification delivery (matching and non-matching)
        - Subscription lifecycle (close)
        - Multiple subscriptions
        - Aborted transactions don't notify
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest

from everyshape.storage.filter import (
    WILDCARD,
    And,
    Filter,
    LengthFilter,
    Or,
    PrefixFilter,
    SuffixFilter,
    WildcardFilter,
)
from everyshape.storage.observer.options import SubscriptionOptions
from everyshape.storage.observer.registry import SubscriptionRegistry


if TYPE_CHECKING:
    from everyshape.loc import key


# =============================================================================
# Registry Compliance Tests
# =============================================================================


class RegistryCompliance:
    """Compliance tests for SubscriptionRegistry.

    Tests the registry's ability to correctly index and match subscriptions.
    """

    @pytest.fixture
    def registry(self) -> SubscriptionRegistry:
        """Provide a fresh registry for each test."""
        return SubscriptionRegistry()

    @staticmethod
    def make_subscription(filt: Filter) -> MockSubscription:
        """Create a mock subscription with the given filter."""
        return MockSubscription(filter=filt)

    # ========================================================================
    # Basic Registry Operations
    # ========================================================================

    def test_registry_add_subscription(self, registry: SubscriptionRegistry) -> None:
        """Test adding a subscription to the registry."""
        sub = self.make_subscription(PrefixFilter(prefix=("users",)))
        registry.add(sub)
        assert len(registry) == 1
        assert sub in registry

    def test_registry_add_duplicate_ignored(self, registry: SubscriptionRegistry) -> None:
        """Test adding the same subscription twice is idempotent."""
        sub = self.make_subscription(PrefixFilter(prefix=("users",)))
        registry.add(sub)
        registry.add(sub)
        assert len(registry) == 1

    def test_registry_remove_subscription(self, registry: SubscriptionRegistry) -> None:
        """Test removing a subscription from the registry."""
        sub = self.make_subscription(PrefixFilter(prefix=("users",)))
        registry.add(sub)
        registry.remove(sub)
        assert len(registry) == 0
        assert sub not in registry

    def test_registry_remove_nonexistent_ignored(self, registry: SubscriptionRegistry) -> None:
        """Test removing a non-existent subscription is ignored."""
        sub = self.make_subscription(PrefixFilter(prefix=("users",)))
        registry.remove(sub)  # Should not raise
        assert len(registry) == 0

    def test_registry_clear(self, registry: SubscriptionRegistry) -> None:
        """Test clearing all subscriptions."""
        for i in range(5):
            sub = self.make_subscription(PrefixFilter(prefix=(f"prefix{i}",)))
            registry.add(sub)
        assert len(registry) == 5
        registry.clear()
        assert len(registry) == 0

    # ========================================================================
    # Prefix Filter Matching
    # ========================================================================

    def test_match_prefix_filter_exact(self, registry: SubscriptionRegistry) -> None:
        """Test matching prefix filter with exact prefix."""
        sub = self.make_subscription(PrefixFilter(prefix=("users",)))
        registry.add(sub)
        matches = registry.match(("users",))
        assert len(matches) == 1
        assert sub in matches

    def test_match_prefix_filter_longer_key(self, registry: SubscriptionRegistry) -> None:
        """Test matching prefix filter with longer key."""
        sub = self.make_subscription(PrefixFilter(prefix=("users",)))
        registry.add(sub)
        matches = registry.match(("users", "alice", "profile"))
        assert len(matches) == 1
        assert sub in matches

    def test_match_prefix_filter_no_match(self, registry: SubscriptionRegistry) -> None:
        """Test prefix filter does not match different prefix."""
        sub = self.make_subscription(PrefixFilter(prefix=("users",)))
        registry.add(sub)
        matches = registry.match(("posts", "123"))
        assert len(matches) == 0

    def test_match_prefix_filter_shorter_key(self, registry: SubscriptionRegistry) -> None:
        """Test prefix filter does not match shorter key."""
        sub = self.make_subscription(PrefixFilter(prefix=("users", "alice")))
        registry.add(sub)
        matches = registry.match(("users",))
        assert len(matches) == 0

    def test_match_empty_prefix_matches_all(self, registry: SubscriptionRegistry) -> None:
        """Test empty prefix filter matches all keys."""
        sub = self.make_subscription(PrefixFilter(prefix=()))
        registry.add(sub)
        assert len(registry.match(())) == 1
        assert len(registry.match(("users",))) == 1
        assert len(registry.match(("users", "alice", "profile"))) == 1

    # ========================================================================
    # Suffix Filter Matching
    # ========================================================================

    def test_match_suffix_filter_exact(self, registry: SubscriptionRegistry) -> None:
        """Test matching suffix filter with exact suffix."""
        sub = self.make_subscription(SuffixFilter(suffix=("profile",)))
        registry.add(sub)
        matches = registry.match(("profile",))
        assert len(matches) == 1
        assert sub in matches

    def test_match_suffix_filter_longer_key(self, registry: SubscriptionRegistry) -> None:
        """Test matching suffix filter with longer key."""
        sub = self.make_subscription(SuffixFilter(suffix=("profile",)))
        registry.add(sub)
        matches = registry.match(("users", "alice", "profile"))
        assert len(matches) == 1
        assert sub in matches

    def test_match_suffix_filter_no_match(self, registry: SubscriptionRegistry) -> None:
        """Test suffix filter does not match different suffix."""
        sub = self.make_subscription(SuffixFilter(suffix=("profile",)))
        registry.add(sub)
        matches = registry.match(("users", "alice", "settings"))
        assert len(matches) == 0

    # ========================================================================
    # Length Filter Matching
    # ========================================================================

    def test_match_length_filter_exact(self, registry: SubscriptionRegistry) -> None:
        """Test matching length filter with exact length."""
        sub = self.make_subscription(LengthFilter(length=3))
        registry.add(sub)
        matches = registry.match(("a", "b", "c"))
        assert len(matches) == 1
        assert sub in matches

    def test_match_length_filter_no_match_short(self, registry: SubscriptionRegistry) -> None:
        """Test length filter does not match shorter key."""
        sub = self.make_subscription(LengthFilter(length=3))
        registry.add(sub)
        matches = registry.match(("a", "b"))
        assert len(matches) == 0

    def test_match_length_filter_no_match_long(self, registry: SubscriptionRegistry) -> None:
        """Test length filter does not match longer key."""
        sub = self.make_subscription(LengthFilter(length=3))
        registry.add(sub)
        matches = registry.match(("a", "b", "c", "d"))
        assert len(matches) == 0

    # ========================================================================
    # Wildcard Filter Matching
    # ========================================================================

    def test_match_wildcard_filter(self, registry: SubscriptionRegistry) -> None:
        """Test matching wildcard filter."""
        sub = self.make_subscription(WildcardFilter(pattern=("users", WILDCARD, "profile")))
        registry.add(sub)
        matches = registry.match(("users", "alice", "profile"))
        assert len(matches) == 1
        assert sub in matches

    def test_match_wildcard_filter_different_wildcard_value(
        self, registry: SubscriptionRegistry
    ) -> None:
        """Test wildcard matches any value in that position."""
        sub = self.make_subscription(WildcardFilter(pattern=("users", WILDCARD, "profile")))
        registry.add(sub)
        assert len(registry.match(("users", "alice", "profile"))) == 1
        assert len(registry.match(("users", "bob", "profile"))) == 1
        assert len(registry.match(("users", "123", "profile"))) == 1

    def test_match_wildcard_filter_no_match_wrong_fixed(
        self, registry: SubscriptionRegistry
    ) -> None:
        """Test wildcard filter does not match wrong fixed segments."""
        sub = self.make_subscription(WildcardFilter(pattern=("users", WILDCARD, "profile")))
        registry.add(sub)
        matches = registry.match(("users", "alice", "settings"))
        assert len(matches) == 0

    def test_match_wildcard_filter_no_match_length(self, registry: SubscriptionRegistry) -> None:
        """Test wildcard filter does not match wrong length."""
        sub = self.make_subscription(WildcardFilter(pattern=("users", WILDCARD, "profile")))
        registry.add(sub)
        assert len(registry.match(("users", "alice"))) == 0
        assert len(registry.match(("users", "alice", "profile", "extra"))) == 0

    # ========================================================================
    # And Filter Matching
    # ========================================================================

    def test_match_and_filter_both_match(self, registry: SubscriptionRegistry) -> None:
        """Test And filter matches when both filters match."""
        sub = self.make_subscription(
            And(filters=(PrefixFilter(prefix=("users",)), LengthFilter(length=3)))
        )
        registry.add(sub)
        matches = registry.match(("users", "alice", "profile"))
        assert len(matches) == 1
        assert sub in matches

    def test_match_and_filter_first_fails(self, registry: SubscriptionRegistry) -> None:
        """Test And filter does not match when first filter fails."""
        sub = self.make_subscription(
            And(filters=(PrefixFilter(prefix=("users",)), LengthFilter(length=3)))
        )
        registry.add(sub)
        matches = registry.match(("posts", "123", "title"))
        assert len(matches) == 0

    def test_match_and_filter_second_fails(self, registry: SubscriptionRegistry) -> None:
        """Test And filter does not match when second filter fails."""
        sub = self.make_subscription(
            And(filters=(PrefixFilter(prefix=("users",)), LengthFilter(length=3)))
        )
        registry.add(sub)
        matches = registry.match(("users", "alice"))
        assert len(matches) == 0

    # ========================================================================
    # Or Filter Matching
    # ========================================================================

    def test_match_or_filter_first_matches(self, registry: SubscriptionRegistry) -> None:
        """Test Or filter matches when first filter matches."""
        sub = self.make_subscription(
            Or(filters=(PrefixFilter(prefix=("users",)), PrefixFilter(prefix=("posts",))))
        )
        registry.add(sub)
        matches = registry.match(("users", "alice"))
        assert len(matches) == 1
        assert sub in matches

    def test_match_or_filter_second_matches(self, registry: SubscriptionRegistry) -> None:
        """Test Or filter matches when second filter matches."""
        sub = self.make_subscription(
            Or(filters=(PrefixFilter(prefix=("users",)), PrefixFilter(prefix=("posts",))))
        )
        registry.add(sub)
        matches = registry.match(("posts", "123"))
        assert len(matches) == 1
        assert sub in matches

    def test_match_or_filter_neither_matches(self, registry: SubscriptionRegistry) -> None:
        """Test Or filter does not match when neither filter matches."""
        sub = self.make_subscription(
            Or(filters=(PrefixFilter(prefix=("users",)), PrefixFilter(prefix=("posts",))))
        )
        registry.add(sub)
        matches = registry.match(("comments", "1"))
        assert len(matches) == 0

    def test_match_or_filter_first_not_matching_second_matches(
        self, registry: SubscriptionRegistry
    ) -> None:
        """Test Or filter matches via second when first doesn't match.

        This is the critical test for the Or indexing fix - the subscription
        should be found via the second filter's index.
        """
        # LengthFilter(2) | PrefixFilter("users") - indexed by BOTH
        sub = self.make_subscription(
            Or(filters=(LengthFilter(length=2), PrefixFilter(prefix=("users",))))
        )
        registry.add(sub)

        # Key ("users", "alice", "profile") has length 3, doesn't match LengthFilter(2)
        # But it DOES match PrefixFilter("users")
        matches = registry.match(("users", "alice", "profile"))
        assert len(matches) == 1
        assert sub in matches

    # ========================================================================
    # Custom Filter Matching
    # ========================================================================

    def test_match_custom_filter(self, registry: SubscriptionRegistry) -> None:
        """Test custom filter types are supported."""
        sub = self.make_subscription(ContainsSegmentFilter(segment="special"))
        registry.add(sub)

        matches = registry.match(("users", "special", "data"))
        assert len(matches) == 1
        assert sub in matches

    def test_match_custom_filter_no_match(self, registry: SubscriptionRegistry) -> None:
        """Test custom filter correctly rejects non-matching keys."""
        sub = self.make_subscription(ContainsSegmentFilter(segment="special"))
        registry.add(sub)

        matches = registry.match(("users", "normal", "data"))
        assert len(matches) == 0

    def test_custom_filter_in_unindexed_set(self, registry: SubscriptionRegistry) -> None:
        """Test custom filters are stored in unindexed set."""
        sub = self.make_subscription(ContainsSegmentFilter(segment="special"))
        registry.add(sub)
        assert sub in registry._unindexed_subscriptions

    # ========================================================================
    # Multiple Subscriptions
    # ========================================================================

    def test_match_multiple_subscriptions(self, registry: SubscriptionRegistry) -> None:
        """Test matching returns all matching subscriptions."""
        sub1 = self.make_subscription(PrefixFilter(prefix=("users",)))
        sub2 = self.make_subscription(LengthFilter(length=2))
        sub3 = self.make_subscription(PrefixFilter(prefix=("posts",)))
        registry.add(sub1)
        registry.add(sub2)
        registry.add(sub3)

        # ("users", "alice") matches sub1 (prefix) and sub2 (length)
        matches = registry.match(("users", "alice"))
        assert len(matches) == 2
        assert sub1 in matches
        assert sub2 in matches
        assert sub3 not in matches

    def test_match_no_duplicates(self, registry: SubscriptionRegistry) -> None:
        """Test matching does not return duplicates."""
        # This subscription matches via both prefix and length
        sub = self.make_subscription(
            And(filters=(PrefixFilter(prefix=("users",)), LengthFilter(length=2)))
        )
        registry.add(sub)

        matches = registry.match(("users", "alice"))
        assert len(matches) == 1


# =============================================================================
# Subscription Compliance Tests
# =============================================================================


class SubscriptionCompliance:
    """Compliance tests for Subscription objects."""

    # ========================================================================
    # Subscription Options
    # ========================================================================

    def test_subscription_options_hashable(self) -> None:
        """Test SubscriptionOptions is hashable."""
        opts = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        assert hash(opts) is not None

    def test_subscription_options_equality(self) -> None:
        """Test SubscriptionOptions equality."""
        opts1 = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        opts2 = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        opts3 = SubscriptionOptions(filter=PrefixFilter(prefix=("posts",)))
        assert opts1 == opts2
        assert opts1 != opts3

    def test_subscription_options_in_set(self) -> None:
        """Test SubscriptionOptions can be used in sets."""
        opts1 = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        opts2 = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        opts3 = SubscriptionOptions(filter=PrefixFilter(prefix=("posts",)))
        s = {opts1, opts2, opts3}
        assert len(s) == 2


# =============================================================================
# Test Helpers
# =============================================================================


@dataclass
class MockSubscription:
    """Mock subscription for testing registry."""

    filter: Filter

    def __hash__(self) -> int:
        return id(self)


@dataclass(frozen=True, slots=True)
class ContainsSegmentFilter(Filter):
    """Custom filter that matches keys containing a specific segment."""

    segment: str

    def matches(self, key: key.Key) -> bool:
        return self.segment in key

    def __hash__(self) -> int:
        return hash(("contains", self.segment))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ContainsSegmentFilter):
            return NotImplemented
        return self.segment == other.segment


# =============================================================================
# Observer Protocol Compliance Tests
# =============================================================================


class ObserverCompliance:
    """Compliance tests for ObserverProtocol implementations.

    Tests the full observer integration: subscribe, notify, bind, unbind, close.

    Usage:
        Inherit and provide an `observable_storage` fixture that returns a storage
        implementing both StorageProtocol and ObserverProtocol.

        ```python
        class TestMyObserver(ObserverCompliance):
            @pytest.fixture
            def observable_storage(self):
                return MyObservableStorage()
        ```
    """

    @pytest.fixture
    def observable_storage(self):
        """Override to provide storage with observer support."""
        raise NotImplementedError("Subclass must provide observable_storage fixture")

    def test_subscribe_and_notify(self, observable_storage) -> None:
        """Test basic subscription and notification flow."""
        notifications: list = []

        def callback(key):
            notifications.append(key)

        sub = observable_storage.subscribe(
            SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        )
        sub.bind(callback)

        with observable_storage.transaction() as tx:
            tx.put(("users", "alice"), b"data")

        assert len(notifications) == 1
        assert notifications[0] == ("users", "alice")

    def test_subscribe_filter_matching(self, observable_storage) -> None:
        """Test subscription only notifies for matching keys."""
        notifications: list = []

        def callback(key):
            notifications.append(key)

        sub = observable_storage.subscribe(
            SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        )
        sub.bind(callback)

        with observable_storage.transaction() as tx:
            tx.put(("users", "alice"), b"data")
            tx.put(("posts", "123"), b"post")  # Should NOT notify
            tx.put(("users", "bob"), b"data")

        assert len(notifications) == 2
        assert ("users", "alice") in notifications
        assert ("users", "bob") in notifications
        assert ("posts", "123") not in notifications

    def test_subscribe_delete_notifies(self, observable_storage) -> None:
        """Test deletion also triggers notification."""
        # First create a key
        with observable_storage.transaction() as tx:
            tx.put(("users", "alice"), b"data")

        notifications: list = []

        def callback(key):
            notifications.append(key)

        sub = observable_storage.subscribe(
            SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        )
        sub.bind(callback)

        # Delete the key
        with observable_storage.transaction() as tx:
            tx.delete(("users", "alice"))

        assert len(notifications) == 1
        assert notifications[0] == ("users", "alice")

    def test_subscription_close_stops_notifications(self, observable_storage) -> None:
        """Test closed subscription stops receiving notifications."""
        notifications: list = []

        def callback(key):
            notifications.append(key)

        sub = observable_storage.subscribe(
            SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        )
        sub.bind(callback)
        sub.close()

        with observable_storage.transaction() as tx:
            tx.put(("users", "alice"), b"data")

        assert len(notifications) == 0

    def test_multiple_subscriptions(self, observable_storage) -> None:
        """Test multiple subscriptions receive appropriate notifications."""
        user_notifications: list = []
        length_notifications: list = []

        def user_callback(key):
            user_notifications.append(key)

        def length_callback(key):
            length_notifications.append(key)

        sub1 = observable_storage.subscribe(
            SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        )
        sub1.bind(user_callback)

        sub2 = observable_storage.subscribe(SubscriptionOptions(filter=LengthFilter(length=2)))
        sub2.bind(length_callback)

        with observable_storage.transaction() as tx:
            tx.put(("users", "alice"), b"data")  # Matches both (prefix + length 2)
            tx.put(("users", "alice", "profile"), b"p")  # Matches only prefix
            tx.put(("posts", "123"), b"post")  # Matches only length

        assert len(user_notifications) == 2
        assert len(length_notifications) == 2
        assert ("users", "alice") in user_notifications
        assert ("users", "alice", "profile") in user_notifications
        assert ("users", "alice") in length_notifications
        assert ("posts", "123") in length_notifications

    def test_subscription_bind_unbind(self, observable_storage) -> None:
        """Test binding and unbinding callbacks."""
        notifications: list = []

        def callback(key):
            notifications.append(key)

        sub = observable_storage.subscribe(
            SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        )
        sub.bind(callback)

        with observable_storage.transaction() as tx:
            tx.put(("users", "alice"), b"data")

        assert len(notifications) == 1

        sub.unbind(callback)

        with observable_storage.transaction() as tx:
            tx.put(("users", "bob"), b"data")

        # Should still be 1 - callback was unbound
        assert len(notifications) == 1

    def test_subscription_multiple_callbacks(self, observable_storage) -> None:
        """Test subscription with multiple callbacks."""
        notifications1: list = []
        notifications2: list = []

        def callback1(key):
            notifications1.append(key)

        def callback2(key):
            notifications2.append(key)

        sub = observable_storage.subscribe(
            SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        )
        sub.bind(callback1)
        sub.bind(callback2)

        with observable_storage.transaction() as tx:
            tx.put(("users", "alice"), b"data")

        assert len(notifications1) == 1
        assert len(notifications2) == 1

    def test_or_filter_subscription(self, observable_storage) -> None:
        """Test Or filter subscription (verifies the Or indexing fix)."""
        notifications: list = []

        def callback(key):
            notifications.append(key)

        # LengthFilter(2) | PrefixFilter("users") - should match via second filter
        # even though first filter is indexed
        sub = observable_storage.subscribe(
            SubscriptionOptions(filter=LengthFilter(length=2) | PrefixFilter(prefix=("users",)))
        )
        sub.bind(callback)

        with observable_storage.transaction() as tx:
            # Length 3 but has "users" prefix - should match via Or's second filter
            tx.put(("users", "alice", "profile"), b"data")

        assert len(notifications) == 1
        assert notifications[0] == ("users", "alice", "profile")

    def test_aborted_transaction_no_notify(self, observable_storage) -> None:
        """Test aborted transaction does not trigger notifications."""
        notifications: list = []

        def callback(key):
            notifications.append(key)

        sub = observable_storage.subscribe(
            SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        )
        sub.bind(callback)

        tx = observable_storage.begin_transaction()
        tx.put(("users", "alice"), b"data")
        tx.abort()  # Abort instead of commit

        assert len(notifications) == 0


# =============================================================================
# Concrete Test Classes
# =============================================================================


class TestRegistryCompliance(RegistryCompliance):
    """Run registry compliance tests against SubscriptionRegistry."""

    pass


class TestSubscriptionCompliance(SubscriptionCompliance):
    """Run subscription compliance tests."""

    pass
