"""Reactive operations."""

from __future__ import annotations

from abc import abstractmethod
from logging import getLogger
from typing import TYPE_CHECKING, cast

from everyshape.loc import path
from everyshape.shape import Operation, PrimitiveRef, ViewRef
from everyshape.storage import Subscription
from everyshape.view import ChildObservable, DescendantsObservable, Observable

from ..term import RValue


if TYPE_CHECKING:
    from everyshape.loc import key

    from ..context import Context


__all__ = [
    "ChangeOp",
    "OnChangeOp",
    "OnChildChangeOp",
    "OnChildrenChangeOp",
    "OnDescendantsChangeOp",
    "OnPrimitiveChangeOp",
]


logger = getLogger(__name__)


class ChangeOp(Operation[Subscription]):
    """Base class for all change subscription operations.

    All change operations return a Subscription that can be used to
    bind callbacks and receive notifications.

    Subclasses:
        - OnChangeOp: Watch entire view
        - OnPrimitiveChangeOp: Watch primitive value
        - OnChildChangeOp: Watch specific child
        - OnChildrenChangeOp: Watch all children
        - OnDescendantsChangeOp: Watch descendants matching pattern
    """

    @abstractmethod
    def execute(self, context: Context) -> Subscription:
        """Execute the change operation and return a subscription."""
        ...


class OnChangeOp(ChangeOp):
    """Subscribe to all changes on a view.

    Uses the Observable protocol to watch all changes within the view's scope.

    Example:
        >>> sub = User.tasks.on_change().execute(ctx)
        >>> sub.bind(my_callback)
        >>> sub.close()
    """

    def __init__(self, ref: ViewRef) -> None:
        """Initialize on_change operation.

        Args:
            ref: View reference to watch
        """
        self.ref = ref
        self.children = (ref,)

    def execute(self, context: Context) -> Subscription:
        """Execute on_change operation.

        Args:
            context: Execution context

        Returns:
            Subscription handle

        Raises:
            TypeError: If view doesn't support Observable protocol
        """
        view_path = self.ref.resolve(context)

        if not view_path:
            view = context.get_context_for_shape(self.ref.get_root_shape()).root_view
        else:
            view = path.navigate_view(
                context.get_context_for_shape(self.ref.get_root_shape()).root_view,
                view_path,
            )

        if not isinstance(view, Observable):
            raise TypeError(
                f"View {view.__class__.__name__} does not implement Observable protocol"
            )

        logger.debug(
            "OnChangeOp creating subscription",
            extra={"path": view_path},
        )
        return view.on_change()

    def __repr__(self) -> str:
        return f"OnChangeOp({self.ref!r})"


class OnPrimitiveChangeOp(ChangeOp):
    """Subscribe to changes on a primitive value.

    Uses the parent view's ChildObservable protocol to watch changes
    on a specific child (the primitive).

    Example:
        >>> sub = User.name.on_change().execute(ctx)
        >>> sub.bind(my_callback)
        >>> sub.close()
    """

    def __init__(self, ref: PrimitiveRef) -> None:
        """Initialize on_primitive_change operation.

        Args:
            ref: Primitive reference to watch
        """
        self.ref = ref
        self.children = (ref,)

    def execute(self, context: Context) -> Subscription:
        """Execute on_primitive_change operation.

        Args:
            context: Execution context

        Returns:
            Subscription handle

        Raises:
            TypeError: If parent view doesn't support ChildObservable protocol
        """
        value_path = cast("path.PathToValue", self.ref.resolve(context))

        parent_view, key = path.navigate_value(
            context.get_context_for_shape(self.ref.get_root_shape()).root_view,
            value_path,
        )

        if not isinstance(parent_view, ChildObservable):
            raise TypeError(
                f"View {parent_view.__class__.__name__} does not implement ChildObservable protocol"
            )

        logger.debug(
            "OnPrimitiveChangeOp creating subscription",
            extra={"path": value_path, "key": key},
        )
        return parent_view.on_child_change(key)

    def __repr__(self) -> str:
        return f"OnPrimitiveChangeOp({self.ref!r})"


class OnChildChangeOp[A](ChangeOp):
    """Subscribe to changes on a specific child of a view.

    Uses the ChildObservable protocol to watch changes on a specific child
    and its subtree.

    Example:
        >>> sub = User.tasks.on_child_change("task_1").execute(ctx)
        >>> sub.bind(my_callback)
        >>> sub.close()
    """

    def __init__(self, ref: ViewRef, address: A | RValue[A]) -> None:
        """Initialize on_child_change operation.

        Args:
            ref: View reference containing the child
            address: Child address to watch
        """
        self.ref = ref
        self.address = address
        self.children = (ref,)

    def execute(self, context: Context) -> Subscription:
        """Execute on_child_change operation.

        Args:
            context: Execution context

        Returns:
            Subscription handle

        Raises:
            TypeError: If view doesn't support ChildObservable protocol
        """
        if isinstance(self.address, RValue):
            address = self.address.execute(context)
        else:
            address = self.address

        view_path = self.ref.resolve(context)

        view = path.navigate_view(
            context.get_context_for_shape(self.ref.get_root_shape()).root_view,
            view_path,
        )

        if not isinstance(view, ChildObservable):
            raise TypeError(
                f"View {view.__class__.__name__} does not implement ChildObservable protocol"
            )

        logger.debug(
            "OnChildChangeOp creating subscription",
            extra={"path": view_path, "address": address},
        )
        return view.on_child_change(address)

    def __repr__(self) -> str:
        return f"OnChildChangeOp({self.ref!r}, {self.address!r})"


class OnChildrenChangeOp(ChangeOp):
    """Subscribe to changes on all children of a view.

    Uses the ChildObservable protocol to watch changes on all immediate
    children of the view.

    Example:
        >>> sub = User.tasks.on_children_change().execute(ctx)
        >>> sub.bind(my_callback)
        >>> sub.close()
    """

    def __init__(self, ref: ViewRef) -> None:
        """Initialize on_children_change operation.

        Args:
            ref: View reference to watch children of
        """
        self.ref = ref
        self.children = (ref,)

    def execute(self, context: Context) -> Subscription:
        """Execute on_children_change operation.

        Args:
            context: Execution context

        Returns:
            Subscription handle

        Raises:
            TypeError: If view doesn't support ChildObservable protocol
        """
        view_path = self.ref.resolve(context)

        if not view_path:
            view = context.get_context_for_shape(self.ref.get_root_shape()).root_view
        else:
            view = path.navigate_view(
                context.get_context_for_shape(self.ref.get_root_shape()).root_view,
                view_path,
            )

        if not isinstance(view, ChildObservable):
            raise TypeError(
                f"View {view.__class__.__name__} does not implement ChildObservable protocol"
            )

        logger.debug(
            "OnChildrenChangeOp creating subscription",
            extra={"path": view_path},
        )
        return view.on_children_change()

    def __repr__(self) -> str:
        return f"OnChildrenChangeOp({self.ref!r})"


class OnDescendantsChangeOp(ChangeOp):
    """Subscribe to changes on descendants matching a pattern.

    Uses the DescendantsObservable protocol to watch changes on descendants
    matching a wildcard pattern.

    Example:
        >>> sub = User.tasks.on_descendants_change("*", "status").execute(ctx)
        >>> sub.bind(my_callback)
        >>> sub.close()
    """

    def __init__(self, ref: ViewRef, *pattern: key.KeySegment) -> None:
        """Initialize on_descendants_change operation.

        Args:
            ref: View reference to watch descendants of
            *pattern: Key segments pattern (use "*" for wildcards)
        """
        self.ref = ref
        self.pattern = pattern
        self.children = (ref,)

    def execute(self, context: Context) -> Subscription:
        """Execute on_descendants_change operation.

        Args:
            context: Execution context

        Returns:
            Subscription handle

        Raises:
            TypeError: If view doesn't support DescendantsObservable protocol
            ValueError: If pattern is empty
        """
        if not self.pattern:
            raise ValueError("Pattern cannot be empty for on_descendants_change")

        view_path = self.ref.resolve(context)

        if not view_path:
            view = context.get_context_for_shape(self.ref.get_root_shape()).root_view
        else:
            view = path.navigate_view(
                context.get_context_for_shape(self.ref.get_root_shape()).root_view,
                view_path,
            )

        if not isinstance(view, DescendantsObservable):
            raise TypeError(
                f"View {view.__class__.__name__} does not implement DescendantsObservable protocol"
            )

        logger.debug(
            "OnDescendantsChangeOp creating subscription",
            extra={"path": view_path, "pattern": self.pattern},
        )
        return view.on_descendents_change(self.pattern[0], *self.pattern[1:])

    def __repr__(self) -> str:
        return f"OnDescendantsChangeOp({self.ref!r}, {self.pattern!r})"
