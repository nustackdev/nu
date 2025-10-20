"""Impure commands - mutations with side effects.

Commands are RValues that modify state. They:
    - Have side effects (is_pure = False)
    - Cannot be cached (different result each time tree changes)
    - Should be executed carefully (order matters)
    - Delegate to mutable view protocols

Command Types:
    - SetCmd: Write value to ref location
    - DeleteCmd: Remove value at ref location

Execution Flow (SetCmd):
    1. resolve_ref(ref, ctx) → path segments
    2. navigate_to_parent(tree, parent_path, ctx) → tree node
    3. get_view(node, view_type, ctx) → mutable view instance
    4. view.set(key, value) → writes to tree

Transaction Requirements:
    Commands MUST be executed within a transaction context:

    ✓ Correct:
        with tree.transaction() as storage_ctx:
            ctx = Context(tree, storage_ctx)
            cmd.execute(ctx)

    ✗ Wrong:
        with tree.snapshot() as storage_ctx:  # Read-only!
            ctx = Context(tree, storage_ctx)
            cmd.execute(ctx)  # → Will fail

Design Philosophy:
    - Explicit impurity (is_pure = False clearly marked)
    - Transactional safety (rely on tree transactions)
    - Fail fast (errors propagate, no silent failures)
    - Protocol delegation (commands don't know storage)

Usage Patterns:
    # Single write
    Market.signal.set(42.0).execute(ctx)

    # Conditional write
    if price.get().execute(ctx) > 100:
        Market.orders["AAPL"].remove().execute(ctx)

    # Batch writes (in transaction)
    with tree.transaction() as storage_ctx:
        ctx = Context(tree, storage_ctx)
        Market.signal.set(99.0).execute(ctx)
        Market.orders["AAPL"].price.set(150.0).execute(ctx)
        # Atomically committed

Why Commands Return None:
    - Side effects are the point (not return values)
    - Prevents confusion (don't use result in expressions)
    - Explicit separation (operations produce, commands mutate)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core import Command


if TYPE_CHECKING:
    from ..core import Ref
    from ..types import Context, PrimitiveNodeValue


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

    def __init__(self, ref: Ref, value: PrimitiveNodeValue) -> None:
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
        from ..executors.resolver import (
            get_view,
            navigate_to_parent,
            resolve_ref,
        )

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
        from ..executors.resolver import (
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
