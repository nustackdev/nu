"""View bases for composing custom observable behaviors.

This module provides reusable bases for common patterns:
- ChildObservableBase
- DescendantsObservableBase
- ObservableBase
"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from everyshape.storage import (
    LengthFilter,
    PrefixFilter,
    SubscriptionOptions,
    WildcardFilter,
)

from .bases import AddressMappingBase


if TYPE_CHECKING:
    from everyshape.container import Container
    from everyshape.loc import key
    from everyshape.storage import (
        Subscription,
    )


__all__ = [
    "ChildObservableBase",
    "DescendantsObservableBase",
    "ObservableBase",
]

logger = getLogger(__name__)


class ObservableBase:
    """Base providing subscription-based observability for the whole view.

    This base enables views to observe any modifications within
    the view's scope.

    Example:
        >>> class MyView(ObservableBase, View): ...
        >>> sub = view.on_change()
        >>> sub.bind(my_callback)
        >>> # ... later
        >>> sub.close()
    """

    container: Container

    def on_change(self) -> Subscription:
        """Subscribe to all changes in this view.

        Returns:
            Subscription handle that can be bound to callbacks

        Example:
            >>> sub = view.on_change()
            >>> sub.bind(callback)
            >>> sub.close()
        """
        return self.container.subscribe(
            SubscriptionOptions(PrefixFilter(prefix=(self.container.site)))
        )


class ChildObservableBase[A](AddressMappingBase[A]):
    """Base providing subscription-based observability for view's children.

    This base enables views to observe changes on specific children
    or all children at once.

    Type Parameters:
        A: The type of address for children

    Example:
        >>> class MyView(ChildObservableBase[int], View): ...
        >>> sub = view.on_child_change(0)
        >>> sub.bind(my_callback)
        >>> # ... later
        >>> sub.close()
    """

    def on_child_change(self, address: A) -> Subscription:
        """Watch changes to a specific child and its subtree.

        Args:
            address: Child address to watch

        Returns:
            Subscription handle that can be bound to callbacks

        Example:
            >>> sub = view.on_child_change("users")
            >>> sub.bind(callback)
            >>> sub.close()
        """
        normalized = self.normalize_address(address)
        child_full_site = (*self.container.site, normalized)
        return self.container.subscribe(
            SubscriptionOptions(
                filter=PrefixFilter(prefix=child_full_site)
                & LengthFilter(length=len(child_full_site))
            )
        )

    def on_children_change(self) -> Subscription:
        """Watch changes of all children.

        Returns:
            Subscription handle that can be bound to callbacks

        Example:
            >>> sub = view.on_children_change()
            >>> sub.bind(callback)
            >>> sub.close()
        """
        child_full_site = (*self.container.site, "*")
        return self.container.subscribe(
            SubscriptionOptions(
                WildcardFilter(pattern=child_full_site),
            )
        )


class DescendantsObservableBase:
    """Base providing subscription-based observability for view's descendants.

    This base enables views to observe changes on descendants matching
    a pattern, using wildcards to match any address at specific levels.

    Example:
        >>> class MyView(DescendantsObservableBase, View): ...
        >>> sub = view.on_descendents_change("users", "*", "age")
        >>> sub.bind(my_callback)
        >>> # ... later
        >>> sub.close()
    """

    container: Container

    def on_descendents_change(
        self,
        address: key.KeySegment,
        *addresses: key.KeySegment,
    ) -> Subscription:
        """Watch changes of descendants for a given pattern.

        Args:
            address: First address segment in the pattern
            *addresses: Additional address segments (use "*" for wildcards)

        Returns:
            Subscription handle that can be bound to callbacks

        Example:
            >>> sub = view.on_descendents_change("users", "*", "age")
            >>> sub.bind(callback)
            >>> sub.close()
        """
        pattern = (address, *addresses)
        wildcard_site = (*self.container.site, *pattern)
        return self.container.subscribe(SubscriptionOptions(WildcardFilter(pattern=wildcard_site)))
