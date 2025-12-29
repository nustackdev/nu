"""Concrete command classes for LValue references.

This module provides concrete commands for refs that work uniformly
across all ref types. Commands are impure mutations that modify data.

Commands (impure mutations):
    - SetCmd: Write primitive value
    - DeleteCmd: Delete value/item
    - StoreCmd: Store entire container structure
    - ClearCmd: Clear all items from container
    - AppendCmd: Append item to sequence
    - InsertCmd: Insert item at index in sequence
    - PopCmd: Pop item from sequence
    - AddCmd: Add item to set
    - RemoveCmd: Remove item from set
    - DiscardCmd: Discard item from set (no error if absent)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyshape.loc import path
from everyshape.shape.term import Command, PrimitiveRef, RValue, ViewRef
from everyshape.types import SpecialValue, Value
from everyshape.view import Appendable, Assignable, Clearable, Deletable, Initializable


if TYPE_CHECKING:
    from everyshape.shape.context import Context


__all__ = [  # noqa: RUF022
    # Core commands
    "SetCmd",
    "DeleteCmd",
    "StoreCmd",
    "ClearCmd",
    # Sequence commands
    "AppendCmd",
    "InsertCmd",
    "PopCmd",
    # Set commands
    "AddCmd",
    "RemoveCmd",
    "DiscardCmd",
]


# =============================================================================
# CORE COMMANDS
# =============================================================================


class SetCmd[T: Value](Command[T]):
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
        ref: PrimitiveRef[T],
        value: RValue[T | SpecialValue],
    ) -> None:
        """Initialize set command.

        Args:
            ref: Reference to write to
            value: Value to write (wrapped in RValue)
        """
        self.ref = ref
        self.value_expr = value
        self.children = (ref, value)

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

        if isinstance(value, SpecialValue):
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

    def __init__(self, ref: PrimitiveRef) -> None:
        """Initialize delete command.

        Args:
            ref: Reference to delete
        """
        self.ref = ref
        self.children = (ref,)

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


class StoreCmd[T: Value](Command[T]):
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
        ref: ViewRef[Initializable],
        data: RValue[T | SpecialValue],
    ) -> None:
        """Initialize store command.

        Args:
            ref: View reference to store to
            data: Data to store (wrapped in RValue)
        """
        self.ref = ref
        self.data_expr = data
        self.children = (ref, data)

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

        if isinstance(data, SpecialValue):
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

    def __init__(self, ref: ViewRef[Clearable]) -> None:
        """Initialize clear command.

        Args:
            ref: View reference to clear
        """
        self.ref = ref
        self.children = (ref,)

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


# =============================================================================
# SEQUENCE COMMANDS
# =============================================================================


class AppendCmd[T: Value](Command[T]):
    """Append command for sequences.

    Impure command that appends an item to a sequence.
    Returns the appended value.

    Type Parameters:
        T: Type of item to append
        ContextT: Execution context type

    Example:
        >>> append_cmd = AppendCmd(list_ref, literal(42))
        >>> appended = append_cmd.execute(ctx)  # Returns 42
    """

    def __init__(
        self,
        ref: ViewRef[Appendable],
        value: RValue[T | SpecialValue],
    ) -> None:
        """Initialize append command.

        Args:
            ref: Sequence reference to append to
            value: Value to append (wrapped in RValue)
        """
        self.ref = ref
        self.value_expr = value
        self.children = (ref, value)

    def execute(self, context: Context) -> T:
        """Execute append command.

        Args:
            context: Execution context with transaction

        Returns:
            The appended value
        """
        # Resolve ref to Path
        view_path = self.ref.resolve(context)

        # Evaluate value expression
        value = self.value_expr.execute(context)

        if isinstance(value, SpecialValue):
            raise ValueError(f"Cannot append special values (Empty, NaN, etc): {value}")

        # Get root view from context
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        # Navigate to the view
        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        # Append through view
        if not isinstance(view, Appendable):
            raise TypeError(
                f"View {view.__class__.__name__} does not implement Appendable protocol."
            )

        view.append(value)
        return value

    def __repr__(self) -> str:
        return f"AppendCmd({self.ref!r}, {self.value_expr!r})"


class InsertCmd[T: Value](Command[T]):
    """Insert command for sequences.

    Impure command that inserts an item at a specific index.
    Returns the inserted value.

    Type Parameters:
        T: Type of item to insert
        ContextT: Execution context type

    Example:
        >>> insert_cmd = InsertCmd(list_ref, literal(0), literal(42))
        >>> inserted = insert_cmd.execute(ctx)  # Returns 42
    """

    def __init__(
        self,
        ref: ViewRef,
        index: RValue[int | SpecialValue],
        value: RValue[T | SpecialValue],
    ) -> None:
        """Initialize insert command.

        Args:
            ref: Sequence reference to insert into
            index: Index to insert at (wrapped in RValue)
            value: Value to insert (wrapped in RValue)
        """
        self.ref = ref
        self.index_expr = index
        self.value_expr = value
        self.children = (ref, index, value)

    def execute(self, context: Context) -> T:
        """Execute insert command.

        Args:
            context: Execution context with transaction

        Returns:
            The inserted value
        """
        raise NotImplementedError
        # # Resolve ref to Path
        # view_path = self.ref.resolve(context)

        # # Evaluate expressions
        # index = self.index_expr.execute(context)
        # value = self.value_expr.execute(context)

        # if isinstance(index, SpecialValue):
        #     raise ValueError(f"Cannot use special value as index: {index}")
        # if isinstance(value, SpecialValue):
        #     raise ValueError(f"Cannot insert special values (Empty, NaN, etc): {value}")

        # # Get root view from context
        # root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        # # Navigate to the view
        # if not view_path:
        #     view = root_view
        # else:
        #     view = path.navigate_view(root_view, view_path)

        # # Insert through view
        # if not isinstance(view, Insertable):
        #     raise TypeError(
        #         f"View {view.__class__.__name__} does not implement Insertable protocol."
        #     )

        # view.insert(index, value)
        # return value

    def __repr__(self) -> str:
        return f"InsertCmd({self.ref!r}, {self.index_expr!r}, {self.value_expr!r})"


class PopCmd[T: Value](Command[T]):
    """Pop command for sequences.

    Impure command that removes and returns an item from a sequence.
    Returns the popped value.

    Type Parameters:
        T: Type of item to pop
        ContextT: Execution context type

    Example:
        >>> pop_cmd = PopCmd(list_ref)
        >>> popped = pop_cmd.execute(ctx)  # Returns last item
    """

    def __init__(
        self,
        ref: ViewRef,
        index: RValue[int | SpecialValue] | None = None,
    ) -> None:
        """Initialize pop command.

        Args:
            ref: Sequence reference to pop from
            index: Index to pop from (default: -1, last item)
        """
        self.ref = ref
        self.index_expr = index
        self.children = (ref, index) if index is not None else (ref,)

    def execute(self, context: Context) -> T:
        """Execute pop command.

        Args:
            context: Execution context with transaction

        Returns:
            The popped value
        """
        # Resolve ref to Path
        view_path = self.ref.resolve(context)

        # Evaluate index if provided
        if self.index_expr is not None:
            index = self.index_expr.execute(context)
            if isinstance(index, SpecialValue):
                raise ValueError(f"Cannot use special value as index: {index}")
        else:
            index = -1

        # Get root view from context
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        # Navigate to the view
        if not view_path:
            view = root_view
        else:
            view = path.navigate_view(root_view, view_path)

        # Pop through view - views should have pop method
        if hasattr(view, "pop"):
            return view.pop(index)

        raise TypeError(f"View {view.__class__.__name__} does not support pop operation.")

    def __repr__(self) -> str:
        return f"PopCmd({self.ref!r}, {self.index_expr!r})"


# =============================================================================
# SET COMMANDS
# =============================================================================


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
        ref: ViewRef,
        value: RValue[T | SpecialValue],
    ) -> None:
        """Initialize add command.

        Args:
            ref: Set reference to add to
            value: Value to add (wrapped in RValue)
        """
        self.ref = ref
        self.value_expr = value
        self.children = (ref, value)

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
        if hasattr(view, "add"):
            view.add(value)
            return None

        raise TypeError(f"View {view.__class__.__name__} does not support add operation.")

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
        ref: ViewRef,
        value: RValue[T | SpecialValue],
    ) -> None:
        """Initialize remove command.

        Args:
            ref: Set reference to remove from
            value: Value to remove (wrapped in RValue)
        """
        self.ref = ref
        self.value_expr = value
        self.children = (ref, value)

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
        if hasattr(view, "remove"):
            view.remove(value)
            return None

        raise TypeError(f"View {view.__class__.__name__} does not support remove operation.")

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
        ref: ViewRef,
        value: RValue[T | SpecialValue],
    ) -> None:
        """Initialize discard command.

        Args:
            ref: Set reference to discard from
            value: Value to discard (wrapped in RValue)
        """
        self.ref = ref
        self.value_expr = value
        self.children = (ref, value)

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
        if hasattr(view, "discard"):
            view.discard(value)
            return None

        raise TypeError(f"View {view.__class__.__name__} does not support discard operation.")

    def __repr__(self) -> str:
        return f"DiscardCmd({self.ref!r}, {self.value_expr!r})"
