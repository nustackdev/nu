"""Operation implementations for Shape system.

This module provides concrete operations that read and compute values:
- GetOp: read value from a reference
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from everyshape.loc import path
from everyshape.shape import Operation
from everyshape.types import Convertible, Empty, Subscriptable


if TYPE_CHECKING:
    from everyshape.shape import Context, PrimitiveRefBase, ViewRefBase


__all__ = [
    "GetOp",
]


# =============================================================================
# GET OPERATION
# =============================================================================


class GetOp[T](Operation[T]):
    """Read operation for primitive values.

    Pure operation that navigates to a location and reads the value.
    Returns Empty if the value doesn't exist.

    Example:
        >>> name = User.name.get().execute(ctx)
        >>> age = User.age.get().execute(ctx)
    """

    def __init__(self, ref: PrimitiveRefBase) -> None:
        """Initialize read operation.

        Args:
            ref: Reference to read from
        """
        self.ref = ref
        self.children = (ref,)

    def execute(self, context: Context) -> T | Empty:
        """Execute read operation.

        Uses Path navigation to reach the target and read the value.

        Args:
            context: Execution context

        Returns:
            Value read from storage, or Empty if not found
        """
        # Resolve ref to Path
        value_path = cast("path.PathToValue", self.ref.resolve(context))

        # Navigate using Path system
        try:
            parent_view, key = path.navigate_value(context.root_view, value_path)

            if not isinstance(parent_view, Subscriptable):
                raise TypeError(
                    f"View {parent_view.__class__.__name__} does not implelement Subscriptible protocol (e.g. ['item'])."
                )

            value = parent_view[key]
            return value
        except KeyError:
            return Empty()

    def __repr__(self) -> str:
        return f"GetOp({self.ref!r})"


class ExtractOp[T](Operation[T]):
    """Extract operation for nested structures.

    Pure operation that reads an entire shape structure and returns
    it as a dictionary. Recursively extracts nested values.

    Example:
        >>> user_data = User.profile.extract().execute(ctx)
        >>> # Returns: {"email": "alice@example.com", "age": 30}
    """

    def __init__(self, ref: ViewRefBase) -> None:
        """Initialize extract operation.

        Args:
            ref: Shape reference to extract from
        """
        self.ref = ref
        self.children = (ref,)

    def execute(self, context: Context) -> T | Empty:
        """Execute extract operation.

        Navigates to shape location and extracts entire structure.

        Args:
            context: Execution context

        Returns:
            Dictionary with extracted data, or Empty if not found
        """
        # Resolve ref to Path
        view_path = self.ref.resolve(context)

        # Navigate to the shape's view
        try:
            if not view_path:
                # Root shape
                shape_view = context.root_view
            else:
                shape_view = path.navigate_view(context.root_view, view_path)

            # Extract structure from view
            if not isinstance(shape_view, Convertible):
                raise TypeError(
                    f"View {shape_view.__class__.__name__} does not implelement Convertible protocol (extract() method)."
                )
            data = shape_view.extract()
            return data
        except KeyError:
            return Empty()

    def __repr__(self) -> str:
        return f"ExtractOp({self.ref!r})"
