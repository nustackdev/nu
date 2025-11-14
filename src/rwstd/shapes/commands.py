"""Command implementations for Shape system.

This module provides concrete commands that mutate state:
- SetCmd: write value to a reference
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from redwood.loc import path
from redwood.shape import Command
from redwood.types import Assignable, Initializable
from rwstd.collections import ListView


if TYPE_CHECKING:
    from redwood.shape import Context, PrimitiveRefBase, RValue, ViewRefBase
    from redwood.types import SpecialValue


__all__ = [
    "SetCmd",
]


# =============================================================================
# SET COMMAND
# =============================================================================


class SetCmd[T](Command[T]):
    """Write command for primitive values.

    Impure command that navigates to a location and writes a value.
    Returns the written value.

    Example:
        >>> User.name.set("Alice").execute(ctx)
        "Alice"
        >>> User.age.set(User.age.get() + 1).execute(ctx)
        31
    """

    def __init__(self, ref: PrimitiveRefBase, value: RValue[T]) -> None:
        """Initialize write command.

        Args:
            ref: Reference to write to
            value: Value to write (literal or RValue)
        """
        self.ref = ref
        self.value_expr = value
        self.children = (ref, self.value_expr)

    def execute(self, context: Context) -> T | SpecialValue:
        """Execute write command.

        Uses Path navigation to reach the target and write the value.

        Args:
            context: Execution context with transaction

        Returns:
            The written value
        """
        # Resolve ref to Path
        value_path = self.ref.resolve(context)

        # Evaluate value expression
        value = self.value_expr.execute(context)

        # Navigate using Path system
        parent_view, key = path.navigate_value(context.root_view, value_path)

        # Store structure through view
        if not isinstance(parent_view, Assignable):
            raise TypeError(
                f"View {parent_view.__class__.__name__} does not implelement Assignable protocol (e.g. ['item'] = 12)."
            )

        # Write value through View
        parent_view[key] = value

        return value

    def __repr__(self) -> str:
        return f"SetCmd({self.ref!r}, {self.value_expr!r})"


class AppendCmd[T](Command[T]):
    """Write command for primitive values.

    Impure command that navigates to a location and writes a value.
    Returns the written value.

    Example:
        >>> User.name.set("Alice").execute(ctx)
        "Alice"
        >>> User.age.set(User.age.get() + 1).execute(ctx)
        31
    """

    def __init__(self, ref: ViewRefBase, value: RValue[T]) -> None:
        """Initialize write command.

        Args:
            ref: Reference to write to
            value: Value to write (literal or RValue)
        """
        self.ref = ref
        self.value_expr = value
        self.children = (ref, self.value_expr)

    def execute(self, context: Context) -> T | SpecialValue:
        """Execute write command.

        Uses Path navigation to reach the target and write the value.

        Args:
            context: Execution context with transaction

        Returns:
            The written value
        """
        # Resolve ref to Path
        view_path = self.ref.resolve(context)

        # Evaluate value expression
        value = self.value_expr.execute(context)

        # Navigate to the shape's view
        if not view_path:
            # Root shape
            view = context.root_view
        else:
            view = path.navigate_view(context.root_view, view_path)

        # Store structure through view
        if not isinstance(view, ListView):
            raise TypeError(f"View at path {view} does not support append() operation.")

        # Write value through View
        view.append(value)

        return value

    def __repr__(self) -> str:
        return f"AppendCmd({self.ref!r}, {self.value_expr!r})"


class StoreCmd[T](Command[T]):
    """Store command for nested structures.

    Impure command that writes an entire shape structure from a dictionary.
    Recursively stores all nested values.

    Example:
        >>> User.profile.store({"email": "alice@example.com", "age": 30}).execute(ctx)
        {"email": "alice@example.com", "age": 30}
    """

    def __init__(self, ref: ViewRefBase, data: RValue[T]) -> None:
        """Initialize store command.

        Args:
            ref: Shape reference to store to
            data: Dictionary with data to store (or RValue producing dict)
        """
        self.ref = ref
        self.data_expr = data
        self.children = (ref, self.data_expr)

    def execute(self, context: Context) -> T | SpecialValue:
        """Execute store command.

        Navigates to shape location and stores entire structure.

        Args:
            context: Execution context with transaction

        Returns:
            The stored dictionary
        """
        # Resolve ref to Path
        view_path = self.ref.resolve(context)

        # Evaluate data expression
        data = self.data_expr.execute(context)

        # Navigate to the shape's view
        if not view_path:
            # Root shape
            shape_view = context.root_view
        else:
            shape_view = path.navigate_view(context.root_view, view_path)

        # Store structure through view
        if not isinstance(shape_view, Initializable):
            raise TypeError(
                f"View {shape_view.__class__.__name__} does not implelement Initializable protocol (store() method)."
            )

        shape_view.store(data)

        return data

    def __repr__(self) -> str:
        return f"StoreCmd({self.ref!r}, {self.data_expr!r})"
