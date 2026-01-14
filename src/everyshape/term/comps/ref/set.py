"""Set operations for LValue references.

This module provides operations for set containers.

Commands (mutations):
    - AddValueCmd: Add value to set (no-op if exists)
    - RemoveValueCmd: Remove value from set (error if missing)
    - DiscardValueCmd: Remove value from set (no error if missing)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from everyshape.loc import path
from everyshape.typing import Sentinel
from everyshape.typing.view import Addable, Discardable, Removable

from ...term import Command, Term, ViewRef


if TYPE_CHECKING:
    from ...context import Context
    from ...refs import UnionRefBases


__all__ = [
    "AddValueCmd",
    "DiscardValueCmd",
    "RemoveValueCmd",
]


class AddValueCmd[T](Command[None]):
    """Add a value to a set.

    Impure command that adds an item to a set.
    Returns None. Adding an existing value is a no-op.

    Type Parameters:
        T: Type of item to add

    Example:
        >>> add_cmd = AddValueCmd(set_ref, literal("item"))
        >>> add_cmd.execute(ctx)  # Returns None
    """

    def __init__(
        self,
        ref: ViewRef | UnionRefBases,
        value: Term[T | Sentinel],
    ) -> None:
        """Initialize add value command.

        Args:
            ref: Set reference to add to
            value: Value to add (wrapped in Term)
        """
        self.ref = cast("ViewRef", ref)
        self.value_expr = value
        self.children = (cast("ViewRef", ref), value)

    def execute(self, context: Context) -> None:
        """Execute add value command.

        Args:
            context: Execution context with transaction

        Returns:
            None
        """
        view_path = self.ref.resolve(context)
        value = self.value_expr.execute(context)

        if isinstance(value, Sentinel):
            raise ValueError(f"Cannot add special values (Empty, NaN, etc): {value}")

        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        if not isinstance(view, Addable):
            raise TypeError(f"View {view.__class__.__name__} does not implement Addable protocol.")

        view.add(value)
        return None

    def __repr__(self) -> str:
        return f"AddValueCmd({self.ref!r}, {self.value_expr!r})"


class RemoveValueCmd[T](Command[None]):
    """Remove a value from a set.

    Impure command that removes an item by value from a set.
    Raises KeyError if item not found.
    Returns None.

    Type Parameters:
        T: Type of item to remove

    Example:
        >>> remove_cmd = RemoveValueCmd(set_ref, literal("item"))
        >>> remove_cmd.execute(ctx)  # Returns None, raises KeyError if missing
    """

    def __init__(
        self,
        ref: ViewRef | UnionRefBases,
        value: Term[T | Sentinel],
    ) -> None:
        """Initialize remove value command.

        Args:
            ref: Set reference to remove from
            value: Value to remove (wrapped in Term)
        """
        self.ref = cast("ViewRef", ref)
        self.value_expr = value
        self.children = (cast("ViewRef", ref), value)

    def execute(self, context: Context) -> None:
        """Execute remove value command.

        Args:
            context: Execution context with transaction

        Returns:
            None

        Raises:
            KeyError: If value not in set
        """
        view_path = self.ref.resolve(context)
        value = self.value_expr.execute(context)

        if isinstance(value, Sentinel):
            raise ValueError(f"Cannot remove special values (Empty, NaN, etc): {value}")

        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        if not isinstance(view, Removable):
            raise TypeError(
                f"View {view.__class__.__name__} does not implement Removable protocol."
            )

        view.remove(value)
        return None

    def __repr__(self) -> str:
        return f"RemoveValueCmd({self.ref!r}, {self.value_expr!r})"


class DiscardValueCmd[T](Command[None]):
    """Discard a value from a set (no error if missing).

    Impure command that discards an item by value from a set.
    Unlike RemoveValueCmd, does not raise an error if item not found.
    Returns None.

    Type Parameters:
        T: Type of item to discard

    Example:
        >>> discard_cmd = DiscardValueCmd(set_ref, literal("item"))
        >>> discard_cmd.execute(ctx)  # Returns None (no error if missing)
    """

    def __init__(
        self,
        ref: ViewRef | UnionRefBases,
        value: Term[T | Sentinel],
    ) -> None:
        """Initialize discard value command.

        Args:
            ref: Set reference to discard from
            value: Value to discard (wrapped in Term)
        """
        self.ref = cast("ViewRef", ref)
        self.value_expr = value
        self.children = (cast("ViewRef", ref), value)

    def execute(self, context: Context) -> None:
        """Execute discard value command.

        Args:
            context: Execution context with transaction

        Returns:
            None
        """
        view_path = self.ref.resolve(context)
        value = self.value_expr.execute(context)

        if isinstance(value, Sentinel):
            raise ValueError(f"Cannot discard special values (Empty, NaN, etc): {value}")

        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        if not isinstance(view, Discardable):
            raise TypeError(
                f"View {view.__class__.__name__} does not implement Discardable protocol."
            )

        view.discard(value)
        return None

    def __repr__(self) -> str:
        return f"DiscardValueCmd({self.ref!r}, {self.value_expr!r})"
