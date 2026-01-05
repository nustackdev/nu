"""Sequence mutation command classes for LValue references.

This module provides sequence mutation commands:

Commands (impure mutations):
    - AppendCmd: Append item to sequence
    - InsertCmd: Insert item at index in sequence
    - PopCmd: Pop item from sequence
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from everyshape.loc import path
from everyshape.types import SpecialValue, Value
from everyshape.view import (
    Appendable,
    Poppable,
)

from ...term import Command, RValue, ViewRef


if TYPE_CHECKING:
    from ...context import Context
    from ...refs import UnionRefBases


__all__ = [
    "AppendCmd",
    "InsertCmd",
    "PopCmd",
]


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
        ref: ViewRef[Appendable] | UnionRefBases,
        value: RValue[T | SpecialValue],
    ) -> None:
        """Initialize append command.

        Args:
            ref: Sequence reference to append to
            value: Value to append (wrapped in RValue)
        """
        self.ref = cast("ViewRef[Appendable]", ref)
        self.value_expr = value
        self.children = (cast("ViewRef[Appendable]", ref), value)

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
        ref: ViewRef | UnionRefBases,
        index: RValue[int | SpecialValue],
        value: RValue[T | SpecialValue],
    ) -> None:
        """Initialize insert command.

        Args:
            ref: Sequence reference to insert into
            index: Index to insert at (wrapped in RValue)
            value: Value to insert (wrapped in RValue)
        """
        self.ref = cast("ViewRef", ref)
        self.index_expr = index
        self.value_expr = value
        self.children = (cast("ViewRef", ref), index, value)

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
        ref: ViewRef | UnionRefBases,
        index: RValue[int | SpecialValue] | None = None,
    ) -> None:
        """Initialize pop command.

        Args:
            ref: Sequence reference to pop from
            index: Index to pop from (default: -1, last item)
        """
        self.ref = cast("ViewRef", ref)
        self.index_expr = index
        self.children = (
            (cast("ViewRef", ref), index) if index is not None else (cast("ViewRef", ref),)
        )

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

        # Pop through view
        if not isinstance(view, Poppable):
            raise TypeError(f"View {view.__class__.__name__} does not implement Poppable protocol.")

        return view.pop(index)

    def __repr__(self) -> str:
        return f"PopCmd({self.ref!r}, {self.index_expr!r})"
