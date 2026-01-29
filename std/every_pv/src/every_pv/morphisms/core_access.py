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

import pv.traits as view_traits
from pv.loc import path
from pv.view import View

from every_pv.ref import PVPrimitiveRef, PVViewRef
from everyabc import EMPTY, Context, Morphism, Operation, Sentinel


if TYPE_CHECKING:
    from pv.types import Value


__all__ = [
    "ExistsOp",
    "ExtractOp",
    "GetOp",
    "LengthOp",
    "MissingOp",
]

type UnionRefBases = None


class GetOp[T](Operation, Morphism[T | Sentinel]):
    """Read operation for primitive values.

    Pure operation that navigates to a location and reads the value.
    Returns Empty if the value doesn't exist.

    Type Parameters:
        T: Type of value to read

    Example:
        >>> get_op = GetOp(value_ref)
        >>> value = get_op.execute(ctx)  # Returns T | Sentinel
    """

    def __init__(self, ref: PVPrimitiveRef[T] | UnionRefBases) -> None:
        """Initialize get operation.

        Args:
            ref: Reference to read from
        """
        super().__init__(cast("PVPrimitiveRef", ref))
        self.ref = cast("PVPrimitiveRef", ref)

    async def execute(self, ctx: Context) -> T | Sentinel:
        """Execute read operation.

        Args:
            ctx: Execution context

        Returns:
            Value read from storage, or Empty if not found
        """
        # Resolve ref to path
        value_path = await self.ref.resolve(ctx)

        # Get root view from context (shape-scoped)
        shape = self.ref.get_root_shape()
        root_view = ctx.get(View, shape=shape)

        # Navigate to parent and get key
        try:
            parent_view, key = path.navigate_value(root_view, value_path)
            if isinstance(parent_view, view_traits.Subscriptable):
                return parent_view[key]
            raise TypeError(f"View {parent_view.__class__.__name__} is not subscriptable")
        except (KeyError, IndexError):
            return EMPTY

    def __repr__(self) -> str:
        return f"GetOp({self.ref!r})"


class ExtractOp[T](Operation, Morphism[T | Sentinel]):
    """Extract operation for container structures.

    Pure operation that reads an entire container structure.
    Returns the extracted data as dict/list/etc.

    Type Parameters:
        T: Type of extracted value (dict, list, etc.)

    Example:
        >>> extract_op = ExtractOp(view_ref)
        >>> data = extract_op.execute(ctx)  # Returns dict/list/etc
    """

    def __init__(self, ref: PVViewRef[view_traits.Convertible[T]] | UnionRefBases) -> None:
        """Initialize extract operation.

        Args:
            ref: View reference to extract from
        """
        super().__init__(cast("PVViewRef[view_traits.Convertible[T]]", ref))
        self.ref = cast("PVViewRef[view_traits.Convertible[T]]", ref)

    async def execute(self, ctx: Context) -> T | Sentinel:
        """Execute extract operation.

        Args:
            ctx: Execution context

        Returns:
            Extracted data, or Empty if not found
        """
        # Resolve ref to path
        view_path = await self.ref.resolve(ctx)

        # Get root view from context (shape-scoped)
        shape = self.ref.get_root_shape()
        root_view = ctx.get(View, shape=shape)

        # Navigate to view
        try:
            if not view_path:
                view = root_view
            else:
                view = path.navigate_view(root_view, view_path)

            if isinstance(view, view_traits.Convertible):
                return view.extract()

            raise TypeError(f"View {view.__class__.__name__} is not convertible")
        except (KeyError, IndexError):
            return EMPTY

    def __repr__(self) -> str:
        return f"ExtractOp({self.ref!r})"


class ExistsOp(Operation, Morphism[bool]):
    """Existence check operation.

    Pure operation that checks if a location exists in storage.

    Example:
        >>> exists_op = ExistsOp(ref)
        >>> exists = exists_op.execute(ctx)  # Returns bool
    """

    def __init__(self, ref: PVPrimitiveRef[Value] | PVViewRef[View] | UnionRefBases) -> None:
        """Initialize exists operation.

        Args:
            ref: Reference to check
        """
        super().__init__(cast("PVPrimitiveRef[Value] | PVViewRef[View]", ref))
        self.ref = cast("PVPrimitiveRef[Value] | PVViewRef[View]", ref)

    async def execute(self, ctx: Context) -> bool:
        """Execute existence check.

        Args:
            ctx: Execution context

        Returns:
            True if location exists, False otherwise
        """
        # Get root view from context (shape-scoped)
        shape = self.ref.get_root_shape()
        root_view = ctx.get(View, shape=shape)

        try:
            ref_path = await self.ref.resolve(ctx)

            if isinstance(self.ref, PVPrimitiveRef):
                parent_view, key = path.navigate_value(root_view, ref_path)
                # Check if key exists
                if isinstance(parent_view, view_traits.Containable):
                    return key in parent_view
                raise TypeError(f"View {parent_view.__class__.__name__} is not containable")
            else:
                # PVViewRef - just try to navigate
                if not ref_path:
                    return True
                path.navigate_view(root_view, ref_path)
                return True
        except (KeyError, IndexError):
            return False

    def __repr__(self) -> str:
        return f"ExistsOp({self.ref!r})"


class MissingOp(Operation, Morphism[bool]):
    """Missing check operation (inverse of exists).

    Pure operation that checks if a location is missing from storage.

    Example:
        >>> missing_op = MissingOp(ref)
        >>> is_missing = missing_op.execute(ctx)  # Returns bool
    """

    def __init__(self, ref: PVPrimitiveRef[Value] | PVViewRef[View] | UnionRefBases) -> None:
        """Initialize missing operation.

        Args:
            ref: Reference to check
        """
        super().__init__(cast("PVPrimitiveRef[Value] | PVViewRef[View]", ref))
        self.ref = cast("PVPrimitiveRef[Value] | PVViewRef[View]", ref)

    async def execute(self, ctx: Context) -> bool:
        """Execute missing check.

        Args:
            ctx: Execution context

        Returns:
            True if location is missing, False otherwise
        """
        exists_op = ExistsOp(self.ref)
        return not await exists_op.execute(ctx)

    def __repr__(self) -> str:
        return f"MissingOp({self.ref!r})"


class LengthOp(Operation, Morphism[int | Sentinel]):
    """Length query operation for containers.

    Pure operation that returns the length of a container.

    Example:
        >>> len_op = LengthOp(list_ref)
        >>> length = len_op.execute(ctx)  # Returns int
    """

    def __init__(self, ref: PVViewRef[view_traits.Sizeable] | UnionRefBases) -> None:
        """Initialize length operation.

        Args:
            ref: View reference to query
        """
        super().__init__(cast("PVViewRef[view_traits.Sizeable]", ref))
        self.ref = cast("PVViewRef[view_traits.Sizeable]", ref)

    async def execute(self, ctx: Context) -> int | Sentinel:
        """Execute length query.

        Args:
            ctx: Execution context

        Returns:
            Length of container, or Empty if not found
        """
        view_path = await self.ref.resolve(ctx)

        # Get root view from context (shape-scoped)
        shape = self.ref.get_root_shape()
        root_view = ctx.get(View, shape=shape)

        try:
            if not view_path:
                view = root_view
            else:
                view = path.navigate_view(root_view, view_path)

            if isinstance(view, view_traits.Sizeable):
                return len(view)

            raise TypeError(f"View {view.__class__.__name__} is not sizeable")
        except (KeyError, IndexError):
            return EMPTY

    def __repr__(self) -> str:
        return f"LengthOp({self.ref!r})"
