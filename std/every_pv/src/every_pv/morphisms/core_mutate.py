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

from pv.loc import path
from pv.traits import (
    Assignable,
    Clearable,
    Deletable,
    Initializable,
)
from pv.view import View

from everyabc import Command, Context, Morphism, Sentinel, Term
from everybase import ensure_term


if TYPE_CHECKING:
    from every_pv.ref import PVPrimitiveRef, PVViewRef

type UnionRefBases = None


__all__ = [
    "ClearCmd",
    "DeleteCmd",
    "SetCmd",
    "StoreCmd",
    "TypedSetCmd",
]


class SetCmd[T](Command, Morphism[T]):
    """Write command for primitive values.

    Impure command that writes a value to a storage location.
    Returns the written value.

    Type Parameters:
        T: Type of value to write

    Example:
        >>> set_cmd = SetCmd(value_ref, ensure_term(42))
        >>> written = set_cmd.execute(ctx)  # Returns 42
    """

    def __init__(
        self,
        ref: PVPrimitiveRef[T] | UnionRefBases,
        value: Term[T | Sentinel],
    ) -> None:
        """Initialize set command.

        Args:
            ref: Reference to write to
            value: Value to write (wrapped in Term)
        """
        self.ref = cast("PVPrimitiveRef[T]", ref)
        self.value_expr = value
        self.children = (cast("PVPrimitiveRef[T]", ref), value)

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
            raise ValueError(f"Cannot store special values (Empty, Invalid, etc): {value}")

        # Get root view from context (shape-scoped)
        shape = self.ref.get_root_shape()
        root_view = context.get(View, shape=shape)

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


class DeleteCmd(Command, Morphism[None]):
    """Delete command for removing items.

    Impure command that deletes a value from storage.
    Returns None.

    Example:
        >>> del_cmd = DeleteCmd(value_ref)
        >>> del_cmd.execute(ctx)  # Returns None
    """

    def __init__(self, ref: PVPrimitiveRef | UnionRefBases) -> None:
        """Initialize delete command.

        Args:
            ref: Reference to delete
        """
        self.ref = cast("PVPrimitiveRef", ref)
        self.children = (cast("PVPrimitiveRef", ref),)

    def execute(self, context: Context) -> None:
        """Execute delete command.

        Args:
            context: Execution context with transaction

        Returns:
            None
        """
        # Resolve ref to Path
        value_path = self.ref.resolve(context)

        # Get root view from context (shape-scoped)
        shape = self.ref.get_root_shape()
        root_view = context.get(View, shape=shape)

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


class StoreCmd[T](Command, Morphism[T]):
    """Store command for container structures.

    Impure command that writes an entire structure to a container.
    Returns the stored value.

    Type Parameters:
        T: Type of value to store (dict, list, etc.)

    Example:
        >>> store_cmd = StoreCmd(dict_ref, ensure_term({"key": "value"}))
        >>> stored = store_cmd.execute(ctx)  # Returns {"key": "value"}
    """

    def __init__(
        self,
        ref: PVViewRef[Initializable] | UnionRefBases,
        data: Term[T | Sentinel],
    ) -> None:
        """Initialize store command.

        Args:
            ref: View reference to store to
            data: Data to store (wrapped in Term)
        """
        self.ref = cast("PVViewRef[Initializable]", ref)
        self.data_expr = data
        self.children = (cast("PVViewRef[Initializable]", ref), data)

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
            raise ValueError(f"Cannot store special values (Empty, Invalid, etc): {data}")

        # Get root view from context (shape-scoped)
        shape = self.ref.get_root_shape()
        root_view = context.get(View, shape=shape)

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


class ClearCmd(Command, Morphism[None]):
    """Clear command for containers.

    Impure command that removes all items from a container.
    Returns None.

    Example:
        >>> clear_cmd = ClearCmd(list_ref)
        >>> clear_cmd.execute(ctx)  # Returns None
    """

    def __init__(self, ref: PVViewRef[Clearable] | UnionRefBases) -> None:
        """Initialize clear command.

        Args:
            ref: View reference to clear
        """
        self.ref = cast("PVViewRef[Clearable]", ref)
        self.children = (cast("PVViewRef[Clearable]", ref),)

    def execute(self, context: Context) -> None:
        """Execute clear command.

        Args:
            context: Execution context with transaction

        Returns:
            None
        """
        # Resolve ref to Path
        view_path = self.ref.resolve(context)

        # Get root view from context (shape-scoped)
        shape = self.ref.get_root_shape()
        root_view = context.get(View, shape=shape)

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


# =============================================================================
# TYPED SET COMMAND
# =============================================================================


class TypedSetCmd[T](Command, Morphism[T]):
    """Set command for TypedValue that calls __to_storage__ before storing.

    Like SetCmd, but before writing to storage, it checks if the value
    has a __to_storage__ method and calls it to convert the typed value
    to a storable format.

    This enables custom types like DatetimeValue to define how they
    should be serialized to storage.

    Type Parameters:
        T: Type of value to write (the storage type)

    Example:
        >>> class DatetimeValue(TypedValue[datetime]):
        ...     def __to_storage__(self) -> float:
        ...         # Store as Unix timestamp
        ...         return self._value.timestamp()
        >>> typed_set = TypedSetCmd(ref, datetime_value)
        >>> typed_set.execute(ctx)  # Stores the timestamp float
    """

    def __init__(
        self,
        ref: PVPrimitiveRef[T],
        value: Term[T | Sentinel],
    ) -> None:
        """Initialize typed set command.

        Args:
            ref: Reference to write to
            value: Value to write (can be TypedValue with __to_storage__)
        """
        self.ref = cast("PVPrimitiveRef[T]", ref)
        self.value_expr = ensure_term(value)
        self.children = (cast("PVPrimitiveRef[T]", ref), value)

    def execute(self, context: Context) -> T:
        """Execute typed write command.

        If the value has __to_storage__, calls it to get the storable value.
        Otherwise stores the value directly.

        Args:
            context: Execution context with transaction

        Returns:
            The written value (after __to_storage__ conversion if applicable)
        """
        # Resolve ref to Path
        value_path = self.ref.resolve(context)

        # Evaluate value expression
        value = self.value_expr.execute(context)

        if isinstance(value, Sentinel):
            raise ValueError(f"Cannot store special values (Empty, Invalid, etc): {value}")

        # Check for __to_storage__ method and call it if present
        if hasattr(value, "__to_storage__"):
            storage_value = value.__to_storage__()
        else:
            storage_value = value

        # Get root view from context (shape-scoped)
        shape = self.ref.get_root_shape()
        root_view = context.get(View, shape=shape)

        # Navigate using Path system
        parent_view, key = path.navigate_value(root_view, value_path)

        # Store through view
        if not isinstance(parent_view, Assignable):
            raise TypeError(
                f"View {parent_view.__class__.__name__} does not implement Assignable protocol."
            )

        # Write value
        parent_view[key] = storage_value
        return storage_value

    def __repr__(self) -> str:
        return f"TypedSetCmd({self.ref!r}, {self.value_expr!r})"
