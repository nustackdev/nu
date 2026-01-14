"""Core command classes for LValue references.

This module provides core commands for refs that work uniformly
across all ref types. Commands are impure mutations that modify data.

Commands (impure mutations):
    - SetCmd: Write primitive value
    - DeleteCmd: Delete value/item
    - StoreCmd: Store entire container structure
    - ClearCmd: Clear all items from container
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from everyshape.loc import path
from everyshape.typing import Sentinel
from everyshape.view import (
    Assignable,
    Clearable,
    Deletable,
    Initializable,
)

from ...term import Command, PrimitiveRef, RValue, ViewRef


if TYPE_CHECKING:
    from ...context import Context
    from ...refs import UnionRefBases


__all__ = [
    "ClearCmd",
    "DeleteCmd",
    "SetCmd",
    "StoreCmd",
]


class SetCmd[T](Command[T]):
    """Write command for primitive values.

    Impure command that writes a value to a storage location.
    Returns the written value.

    Type Parameters:
        T: Type of value to write
        ContextT: Execution context type

    Example:
        >>> set_cmd = SetCmd(value_ref, literal(42))
        >>> written = set_cmd.execute(ctx)  # Returns 42
    """

    def __init__(
        self,
        ref: PrimitiveRef[T] | UnionRefBases,
        value: RValue[T | Sentinel],
    ) -> None:
        """Initialize set command.

        Args:
            ref: Reference to write to
            value: Value to write (wrapped in RValue)
        """
        self.ref = cast("PrimitiveRef[T]", ref)
        self.value_expr = value
        self.children = (cast("PrimitiveRef[T]", ref), value)

    def execute(self, context: Context) -> T:
        """Execute write command.

        Args:
            context: Execution context with transaction

        Returns:
            The written value
        """
        # Resolve ref to Path
        value_path = self.ref.resolve(context)

        # Evaluate value expression
        value = self.value_expr.execute(context)

        if isinstance(value, Sentinel):
            raise ValueError(f"Cannot store special values (Empty, NaN, etc): {value}")

        # Get root view from context
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        # Navigate using Path system
        parent_view, key = path.navigate_value(root_view, value_path)

        # Store through view
        if not isinstance(parent_view, Assignable):
            raise TypeError(
                f"View {parent_view.__class__.__name__} does not implement Assignable protocol."
            )

        # Write value
        parent_view[key] = value
        return value

    def __repr__(self) -> str:
        return f"SetCmd({self.ref!r}, {self.value_expr!r})"


class DeleteCmd(Command[None]):
    """Delete command for removing items.

    Impure command that deletes a value from storage.
    Returns None.

    Type Parameters:
        ContextT: Execution context type

    Example:
        >>> del_cmd = DeleteCmd(value_ref)
        >>> del_cmd.execute(ctx)  # Returns None
    """

    def __init__(self, ref: PrimitiveRef | UnionRefBases) -> None:
        """Initialize delete command.

        Args:
            ref: Reference to delete
        """
        self.ref = cast("PrimitiveRef", ref)
        self.children = (cast("PrimitiveRef", ref),)

    def execute(self, context: Context) -> None:
        """Execute delete command.

        Args:
            context: Execution context with transaction

        Returns:
            None
        """
        # Resolve ref to Path
        value_path = self.ref.resolve(context)

        # Get root view from context
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        # Navigate using Path system
        parent_view, key = path.navigate_value(root_view, value_path)

        # Delete through view
        if not isinstance(parent_view, Deletable):
            raise TypeError(
                f"View {parent_view.__class__.__name__} does not implement Deletable protocol."
            )

        del parent_view[key]
        return None

    def __repr__(self) -> str:
        return f"DeleteCmd({self.ref!r})"


class StoreCmd[T](Command[T]):
    """Store command for container structures.

    Impure command that writes an entire structure to a container.
    Returns the stored value.

    Type Parameters:
        T: Type of value to store (dict, list, etc.)
        ContextT: Execution context type

    Example:
        >>> store_cmd = StoreCmd(dict_ref, literal({"key": "value"}))
        >>> stored = store_cmd.execute(ctx)  # Returns {"key": "value"}
    """

    def __init__(
        self,
        ref: ViewRef[Initializable] | UnionRefBases,
        data: RValue[T | Sentinel],
    ) -> None:
        """Initialize store command.

        Args:
            ref: View reference to store to
            data: Data to store (wrapped in RValue)
        """
        self.ref = cast("ViewRef[Initializable]", ref)
        self.data_expr = data
        self.children = (cast("ViewRef[Initializable]", ref), data)

    def execute(self, context: Context) -> T:
        """Execute store command.

        Args:
            context: Execution context with transaction

        Returns:
            The stored value
        """
        # Resolve ref to Path
        view_path = self.ref.resolve(context)

        # Evaluate data expression
        data = self.data_expr.execute(context)

        if isinstance(data, Sentinel):
            raise ValueError(f"Cannot store special values (Empty, NaN, etc): {data}")

        # Get root view from context
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        # Navigate to the view
        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        # Store through view
        if not isinstance(view, Initializable):
            raise TypeError(
                f"View {view.__class__.__name__} does not implement Initializable protocol."
            )

        view.store(data)
        return data

    def __repr__(self) -> str:
        return f"StoreCmd({self.ref!r}, {self.data_expr!r})"


class ClearCmd(Command[None]):
    """Clear command for containers.

    Impure command that removes all items from a container.
    Returns None.

    Type Parameters:
        ContextT: Execution context type

    Example:
        >>> clear_cmd = ClearCmd(list_ref)
        >>> clear_cmd.execute(ctx)  # Returns None
    """

    def __init__(self, ref: ViewRef[Clearable] | UnionRefBases) -> None:
        """Initialize clear command.

        Args:
            ref: View reference to clear
        """
        self.ref = cast("ViewRef[Clearable]", ref)
        self.children = (cast("ViewRef[Clearable]", ref),)

    def execute(self, context: Context) -> None:
        """Execute clear command.

        Args:
            context: Execution context with transaction

        Returns:
            None
        """
        # Resolve ref to Path
        view_path = self.ref.resolve(context)

        # Get root view from context
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        # Navigate to the view
        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        # Clear through view
        if not isinstance(view, Clearable):
            raise TypeError(
                f"View {view.__class__.__name__} does not implement Clearable protocol."
            )

        view.clear()
        return None

    def __repr__(self) -> str:
        return f"ClearCmd({self.ref!r})"
