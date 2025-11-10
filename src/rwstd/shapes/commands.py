"""Impure commands - mutations with side effects."""

from __future__ import annotations

from typing import TYPE_CHECKING

from redwood.shape.evaluation import Command
from redwood.shape.utils.resolver import (
    get_view,
    navigate_to_parent,
    resolve_ref,
)


if TYPE_CHECKING:
    from redwood.abc import Value
    from redwood.shape.evaluation import Ref
    from redwood.shape.types import Context


# ============================================================================
# Set Command - Write Value
# ============================================================================


class SetCmd(Command):
    """Impure write operation.

    Writes a value to a ref location using mutable view protocols.

    Flow:
    1. Resolve ref to path segments
    2. Navigate to parent container
    3. Get mutable view from parent
    4. Call view.set() with key and value

    Example:
        Market.signal.set(42.0).execute(ctx)
        Market.orders["AAPL"].price.set(150.0).execute(ctx)
    """

    def __init__(self, ref: Ref, value: Value) -> None:
        """Initialize set command.

        Args:
            ref: Reference to write to
            value: Value to set
        """
        self.ref = ref
        self.value = value

    def execute(self, context: Context) -> None:
        """Execute write operation.

        Args:
            context: Execution context (tree + storage)

        Returns:
            None (side effect operation)
        """
        # 1. Resolve ref to path
        path = resolve_ref(self.ref, context)

        if not path:
            raise ValueError("Cannot set root path")

        # 2. Navigate to parent
        if len(path) == 1:
            # Single segment - write to root
            parent = context.tree
            key = path[0]
        else:
            # Multiple segments - navigate to parent
            parent_path = path[:-1]
            key = path[-1]
            parent = navigate_to_parent(context.tree, parent_path, context)

        # 3. Get mutable view from parent
        view = get_view(parent, self.ref.view_type, context)

        # 4. Call view protocol method
        view.set(key, self.value)


# ============================================================================
# Delete Command - Remove Value
# ============================================================================


class DeleteCmd(Command):
    """Impure delete operation.

    Removes a value at ref location using mutable view protocols.

    Example:
        Market.orders["AAPL"].remove().execute(ctx)
    """

    def __init__(self, ref: Ref) -> None:
        """Initialize delete command.

        Args:
            ref: Reference to delete
        """
        self.ref = ref

    def execute(self, context: Context) -> None:
        """Execute delete operation.

        Args:
            context: Execution context

        Returns:
            None (side effect operation)
        """
        from ..utils.resolver import (
            get_view,
            navigate_to_parent,
            resolve_ref,
        )

        # 1. Resolve ref to path
        path = resolve_ref(self.ref, context)

        if not path:
            raise ValueError("Cannot delete root path")

        # 2. Navigate to parent
        if len(path) == 1:
            parent = context.tree
            key = path[0]
        else:
            parent_path = path[:-1]
            key = path[-1]
            parent = navigate_to_parent(context.tree, parent_path, context)

        # 3. Get mutable view
        view = get_view(parent, self.ref.view_type, context)

        # 4. Call view protocol method
        view.remove(key)


__all__ = [
    "DeleteCmd",
    "SetCmd",
]
