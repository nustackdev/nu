"""Set mutation command classes for LValue references.

This module provides set mutation commands:

Commands (impure mutations):
    - AddCmd: Add item to set
    - RemoveCmd: Remove item from set
    - DiscardCmd: Discard item from set (no error if absent)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from everyshape.loc import path
from everyshape.types import SpecialValue, Value
from everyshape.view import (
    Addable,
    Discardable,
    Removable,
)

from ...term import Command, RValue, ViewRef


if TYPE_CHECKING:
    from ...context import Context
    from ...refs import UnionRefBases


__all__ = [
    "AddCmd",
    "DiscardCmd",
    "RemoveCmd",
]


class AddCmd[T: Value](Command[None]):
    """Add command for sets.

    Impure command that adds an item to a set.
    Returns None.

    Type Parameters:
        T: Type of item to add
        ContextT: Execution context type

    Example:
        >>> add_cmd = AddCmd(set_ref, literal("item"))
        >>> add_cmd.execute(ctx)  # Returns None
    """

    def __init__(
        self,
        ref: ViewRef | UnionRefBases,
        value: RValue[T | SpecialValue],
    ) -> None:
        """Initialize add command.

        Args:
            ref: Set reference to add to
            value: Value to add (wrapped in RValue)
        """
        self.ref = cast("ViewRef", ref)
        self.value_expr = value
        self.children = (cast("ViewRef", ref), value)

    def execute(self, context: Context) -> None:
        """Execute add command.

        Args:
            context: Execution context with transaction

        Returns:
            None
        """
        # Resolve ref to Path
        view_path = self.ref.resolve(context)

        # Evaluate value expression
        value = self.value_expr.execute(context)

        if isinstance(value, SpecialValue):
            raise ValueError(f"Cannot add special values (Empty, NaN, etc): {value}")

        # Get root view from context
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        # Navigate to the view
        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        # Add through view
        if not isinstance(view, Addable):
            raise TypeError(f"View {view.__class__.__name__} does not implement Addable protocol.")

        view.add(value)
        return None

    def __repr__(self) -> str:
        return f"AddCmd({self.ref!r}, {self.value_expr!r})"


class RemoveCmd[T: Value](Command[None]):
    """Remove command for sets.

    Impure command that removes an item from a set.
    Raises KeyError if item not found.
    Returns None.

    Type Parameters:
        T: Type of item to remove
        ContextT: Execution context type

    Example:
        >>> remove_cmd = RemoveCmd(set_ref, literal("item"))
        >>> remove_cmd.execute(ctx)  # Returns None
    """

    def __init__(
        self,
        ref: ViewRef | UnionRefBases,
        value: RValue[T | SpecialValue],
    ) -> None:
        """Initialize remove command.

        Args:
            ref: Set reference to remove from
            value: Value to remove (wrapped in RValue)
        """
        self.ref = cast("ViewRef", ref)
        self.value_expr = value
        self.children = (cast("ViewRef", ref), value)

    def execute(self, context: Context) -> None:
        """Execute remove command.

        Args:
            context: Execution context with transaction

        Returns:
            None

        Raises:
            KeyError: If item not in set
        """
        # Resolve ref to Path
        view_path = self.ref.resolve(context)

        # Evaluate value expression
        value = self.value_expr.execute(context)

        if isinstance(value, SpecialValue):
            raise ValueError(f"Cannot remove special values (Empty, NaN, etc): {value}")

        # Get root view from context
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        # Navigate to the view
        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        # Remove through view
        if not isinstance(view, Removable):
            raise TypeError(
                f"View {view.__class__.__name__} does not implement Removable protocol."
            )

        view.remove(value)
        return None

    def __repr__(self) -> str:
        return f"RemoveCmd({self.ref!r}, {self.value_expr!r})"


class DiscardCmd[T: Value](Command[None]):
    """Discard command for sets.

    Impure command that discards an item from a set.
    No error if item not found (unlike RemoveCmd).
    Returns None.

    Type Parameters:
        T: Type of item to discard
        ContextT: Execution context type

    Example:
        >>> discard_cmd = DiscardCmd(set_ref, literal("item"))
        >>> discard_cmd.execute(ctx)  # Returns None (no error if missing)
    """

    def __init__(
        self,
        ref: ViewRef | UnionRefBases,
        value: RValue[T | SpecialValue],
    ) -> None:
        """Initialize discard command.

        Args:
            ref: Set reference to discard from
            value: Value to discard (wrapped in RValue)
        """
        self.ref = cast("ViewRef", ref)
        self.value_expr = value
        self.children = (cast("ViewRef", ref), value)

    def execute(self, context: Context) -> None:
        """Execute discard command.

        Args:
            context: Execution context with transaction

        Returns:
            None
        """
        # Resolve ref to Path
        view_path = self.ref.resolve(context)

        # Evaluate value expression
        value = self.value_expr.execute(context)

        if isinstance(value, SpecialValue):
            raise ValueError(f"Cannot discard special values (Empty, NaN, etc): {value}")

        # Get root view from context
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        # Navigate to the view
        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        # Discard through view
        if not isinstance(view, Discardable):
            raise TypeError(
                f"View {view.__class__.__name__} does not implement Discardable protocol."
            )

        view.discard(value)
        return None

    def __repr__(self) -> str:
        return f"DiscardCmd({self.ref!r}, {self.value_expr!r})"
