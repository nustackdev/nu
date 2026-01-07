"""Core access operations for LValue references.

This module provides core operations for refs that read data:

Operations (pure computations):
    - GetOp: Read primitive value from ref
    - ExtractOp: Read entire container structure
    - ExistsOp: Check if location exists
    - MissingOp: Check if location is missing
    - LengthOp: Get container length
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from everyshape.loc import path
from everyshape.term.term import Operation, PrimitiveRef, ViewRef
from everyshape.types import Empty, SpecialValue, Value
from everyshape.view import capabilities as view_capabilities


if TYPE_CHECKING:
    from everyshape.view import View

    from ...context import Context
    from ...refs import UnionRefBases


__all__ = [
    "ExistsOp",
    "ExtractOp",
    "GetOp",
    "LengthOp",
    "MissingOp",
]


class GetOp[T](Operation[T | SpecialValue]):
    """Read operation for primitive values.

    Pure operation that navigates to a location and reads the value.
    Returns Empty if the value doesn't exist.

    Type Parameters:
        T: Type of value to read
        ContextT: Execution context type

    Example:
        >>> get_op = GetOp(value_ref)
        >>> value = get_op.execute(ctx)  # Returns T | SpecialValue
    """

    def __init__(self, ref: PrimitiveRef[T] | UnionRefBases) -> None:
        """Initialize get operation.

        Args:
            ref: Reference to read from
        """
        self.ref = cast("PrimitiveRef", ref)
        self.children = (cast("PrimitiveRef", ref),)

    def execute(self, context: Context) -> T | SpecialValue:
        """Execute read operation.

        Args:
            context: Execution context

        Returns:
            Value read from storage, or Empty if not found
        """
        # Resolve ref to path
        value_path = self.ref.resolve(context)

        # Get root view from context
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        # Navigate to parent and get key
        try:
            parent_view, key = path.navigate_value(root_view, value_path)
            if isinstance(parent_view, view_capabilities.Subscriptable):
                return parent_view[key]
            raise TypeError(f"View {parent_view.__class__.__name__} is not subscriptable")
        except (KeyError, IndexError):
            return Empty()

    def __repr__(self) -> str:
        return f"GetOp({self.ref!r})"


class ExtractOp[T](Operation[T | SpecialValue]):
    """Extract operation for container structures.

    Pure operation that reads an entire container structure.
    Returns the extracted data as dict/list/etc.

    Type Parameters:
        T: Type of extracted value (dict, list, etc.)
        ContextT: Execution context type

    Example:
        >>> extract_op = ExtractOp(view_ref)
        >>> data = extract_op.execute(ctx)  # Returns dict/list/etc
    """

    def __init__(self, ref: ViewRef[view_capabilities.Convertible[T]] | UnionRefBases) -> None:
        """Initialize extract operation.

        Args:
            ref: View reference to extract from
        """
        self.ref = cast("ViewRef[view_capabilities.Convertible[T]]", ref)
        self.children = (cast("ViewRef[view_capabilities.Convertible[T]]", ref),)

    def execute(self, context: Context) -> T | SpecialValue:
        """Execute extract operation.

        Args:
            context: Execution context

        Returns:
            Extracted data, or Empty if not found
        """
        # Resolve ref to path
        view_path = self.ref.resolve(context)

        # Get root view from context
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        # Navigate to view
        try:
            if not view_path:
                view = root_view
            else:
                view = path.navigate_view(root_view, view_path)

            if isinstance(view, view_capabilities.Convertible):
                return view.extract()

            raise TypeError(f"View {view.__class__.__name__} is not convertible")
        except (KeyError, IndexError):
            return Empty()

    def __repr__(self) -> str:
        return f"ExtractOp({self.ref!r})"


class ExistsOp(Operation[bool]):
    """Existence check operation.

    Pure operation that checks if a location exists in storage.

    Type Parameters:
        ContextT: Execution context type

    Example:
        >>> exists_op = ExistsOp(ref)
        >>> exists = exists_op.execute(ctx)  # Returns bool
    """

    def __init__(self, ref: PrimitiveRef[Value] | ViewRef[View] | UnionRefBases) -> None:
        """Initialize exists operation.

        Args:
            ref: Reference to check
        """
        self.ref = cast("PrimitiveRef[Value] | ViewRef[View]", ref)
        self.children = (cast("PrimitiveRef[Value] | ViewRef[View]", ref),)

    def execute(self, context: Context) -> bool:
        """Execute existence check.

        Args:
            context: Execution context

        Returns:
            True if location exists, False otherwise
        """
        # Get root view from context
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        try:
            ref_path = self.ref.resolve(context)

            if isinstance(self.ref, PrimitiveRef):
                parent_view, key = path.navigate_value(root_view, ref_path)
                # Check if key exists
                if isinstance(parent_view, view_capabilities.Containable):
                    return key in parent_view
                raise TypeError(f"View {parent_view.__class__.__name__} is not containable")
            else:
                # ViewRef - just try to navigate
                if not ref_path:
                    return True
                path.navigate_view(root_view, ref_path)
                return True
        except (KeyError, IndexError):
            return False

    def __repr__(self) -> str:
        return f"ExistsOp({self.ref!r})"


class MissingOp(Operation[bool]):
    """Missing check operation (inverse of exists).

    Pure operation that checks if a location is missing from storage.

    Type Parameters:
        ContextT: Execution context type

    Example:
        >>> missing_op = MissingOp(ref)
        >>> is_missing = missing_op.execute(ctx)  # Returns bool
    """

    def __init__(self, ref: PrimitiveRef[Value] | ViewRef[View] | UnionRefBases) -> None:
        """Initialize missing operation.

        Args:
            ref: Reference to check
        """
        self.ref = cast("PrimitiveRef[Value] | ViewRef[View]", ref)
        self.children = (cast("PrimitiveRef[Value] | ViewRef[View]", ref),)

    def execute(self, context: Context) -> bool:
        """Execute missing check.

        Args:
            context: Execution context

        Returns:
            True if location is missing, False otherwise
        """
        exists_op = ExistsOp(self.ref)
        return not exists_op.execute(context)

    def __repr__(self) -> str:
        return f"MissingOp({self.ref!r})"


class LengthOp(Operation[int | SpecialValue]):
    """Length query operation for containers.

    Pure operation that returns the length of a container.

    Type Parameters:
        ContextT: Execution context type

    Example:
        >>> len_op = LengthOp(list_ref)
        >>> length = len_op.execute(ctx)  # Returns int
    """

    def __init__(self, ref: ViewRef[view_capabilities.Sizeable] | UnionRefBases) -> None:
        """Initialize length operation.

        Args:
            ref: View reference to query
        """
        self.ref = cast("ViewRef[view_capabilities.Sizeable]", ref)
        self.children = (cast("ViewRef[view_capabilities.Sizeable]", ref),)

    def execute(self, context: Context) -> int | SpecialValue:
        """Execute length query.

        Args:
            context: Execution context

        Returns:
            Length of container, or Empty if not found
        """
        view_path = self.ref.resolve(context)
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        try:
            if not view_path:
                view = root_view
            else:
                view = path.navigate_view(root_view, view_path)

            if isinstance(view, view_capabilities.Sizeable):
                return len(view)

            raise TypeError(f"View {view.__class__.__name__} is not sizeable")
        except (KeyError, IndexError):
            return Empty()

    def __repr__(self) -> str:
        return f"LengthOp({self.ref!r})"
