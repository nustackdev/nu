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
    CompositeFilter,
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
            SubscriptionOptions(PrefixFilter(prefix=(self.container.path)))
        )


class ChildObservableBase[A](AddressMappingBase[A]):
    """Base providing subscription-based observability for view's children.

    This base enables views to observe changes on specific children
    or all children at once.

    Type Parameters:
        A: The type of address/key for children

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
        key = self.normalize_address(address)
        child_full_path = (*self.container.path, key)
        return self.container.subscribe(
            SubscriptionOptions(
                CompositeFilter(
                    filters=(
                        PrefixFilter(prefix=child_full_path),
                        LengthFilter(length=len(child_full_path)),
                    )
                )
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
        child_full_path = (*self.container.path, "*")
        return self.container.subscribe(
            SubscriptionOptions(
                WildcardFilter(pattern=child_full_path),
            )
        )


class DescendantsObservableBase:
    """Base providing subscription-based observability for view's descendants.

    This base enables views to observe changes on descendants matching
    a pattern, using wildcards to match any key at specific levels.

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
        key: key.KeySegment,
        *keys: key.KeySegment,
    ) -> Subscription:
        """Watch changes of descendants for a given pattern.

        Args:
            key: First key segment in the pattern
            *keys: Additional key segments (use "*" for wildcards)

        Returns:
            Subscription handle that can be bound to callbacks

        Example:
            >>> sub = view.on_descendents_change("users", "*", "age")
            >>> sub.bind(callback)
            >>> sub.close()
        """
        keys = (key, *keys)
        wildcard_path = (*self.container.path, *keys)
        return self.container.subscribe(SubscriptionOptions(WildcardFilter(pattern=wildcard_path)))
