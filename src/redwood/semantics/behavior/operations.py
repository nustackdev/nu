"""Pure operations - reads and computations without side effects.

Operations are RValues that produce values deterministically. They:
    - Have no side effects (is_pure = True)
    - Can be cached safely
    - Can be composed freely
    - Delegate to view protocols

Operation Types:
    - GetOp: Read value from ref location
    - LiteralValue: Constant value (42, "hello", True)
    - BinaryOp: Binary operations (>, <, ==, +, -, *, /, and, or)

Execution Flow (GetOp):
    1. resolve_ref(ref, ctx) → path segments
    2. navigate_to_parent(tree, parent_path, ctx) → tree node
    3. get_view(node, view_type, ctx) → view instance
    4. view.get(key) → value or None → Empty

Special Value Handling:
    - Operations propagate Empty/NaN automatically
    - BinaryOp: if any operand is special → NaN
    - Graceful degradation without exceptions

Design Philosophy:
    - Pure by contract (no hidden mutations)
    - Composable (operations return RValues)
    - Fail gracefully (Empty/NaN, not exceptions)
    - Delegate to protocols (operations don't know storage)

Usage Patterns:
    # Simple read
    value = price_ref.get().execute(ctx)

    # Comparison
    is_expensive = BinaryOp("gt", price.get(), LiteralValue(100))
    result = is_expensive.execute(ctx)  # → True/False/NaN

    # Composition
    condition = BinaryOp("and",
        BinaryOp("gt", price.get(), LiteralValue(100)),
        BinaryOp("lt", volume.get(), LiteralValue(1000))
    )

    # Operator overloading (future)
    price.get() > 100  # → constructs BinaryOp("gt", ...)

Why Operations Return RValues:
    - Enables composition: op1.and(op2)
    - Enables lazy evaluation: build expression, execute later
    - Enables optimization: constant folding, dead code elimination
    - Enables serialization: expressions as data
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from ..core import Operation, RValue
from ..types import Context, Empty


if TYPE_CHECKING:
    from ..core import Ref


# ============================================================================
# Get Operation - Pure Read
# ============================================================================


class GetOp(Operation):
    """Pure read operation.

    Reads a value from a ref location using view protocols.

    Flow:
    1. Resolve ref to path segments
    2. Navigate to parent container
    3. Get view from parent
    4. Call view.get() with final key

    Example:
        Market.signal.get().execute(ctx) → 42.0
        Market.orders["AAPL"].price.get().execute(ctx) → 150.0
    """

    def __init__(self, ref: Ref) -> None:
        """Initialize get operation.

        Args:
            ref: Reference to read from
        """
        self.ref = ref

    def execute(self, context: Context) -> object:
        """Execute read operation.

        Args:
            context: Execution context (tree + storage)

        Returns:
            Value at ref location, or Empty if not found
        """
        from ..executors.resolver import (
            get_view,
            navigate_to_parent,
            resolve_ref,
        )

        try:
            # 1. Resolve ref to path
            path = resolve_ref(self.ref, context)

            if not path:
                return Empty

            # 2. Navigate to parent
            if len(path) == 1:
                # Single segment - read from root
                parent = context.tree
                key = path[0]
            else:
                # Multiple segments - navigate to parent
                parent_path = path[:-1]
                key = path[-1]
                parent = navigate_to_parent(context.tree, parent_path, context)

            # 3. Get view from parent
            view = get_view(parent, self.ref.view_type, context)

            # 4. Call view protocol method
            result = view.get(key)

            return result if result is not None else Empty

        except (KeyError, AttributeError, IndexError):
            # Graceful failure
            return Empty


# ============================================================================
# Literal Value - Constants
# ============================================================================


class LiteralValue(Operation):
    """Constant literal value.

    Represents a compile-time constant (42, "hello", True, etc.)

    Example:
        LiteralValue(10).execute(ctx) → 10
    """

    def __init__(self, value: object) -> None:
        """Initialize literal.

        Args:
            value: The constant value
        """
        self.value = value

    def execute(self, context: Context) -> object:
        """Return the literal value.

        Args:
            context: Unused

        Returns:
            The constant value
        """
        return self.value


# ============================================================================
# Binary Operation - Comparisons and Arithmetic
# ============================================================================


class BinaryOp(Operation):
    """Binary operation between two RValues.

    Supports comparison, arithmetic, and logical operations.
    Handles special value propagation.

    Example:
        BinaryOp("gt", price.get(), LiteralValue(100))
        → Evaluates to: price > 100
    """

    # Operator implementations
    _OPERATORS: ClassVar[dict[str, Any]] = {
        # Comparison
        "gt": lambda a, b: a > b,
        "lt": lambda a, b: a < b,
        "eq": lambda a, b: a == b,
        "ne": lambda a, b: a != b,
        "ge": lambda a, b: a >= b,
        "le": lambda a, b: a <= b,
        # Arithmetic
        "add": lambda a, b: a + b,
        "sub": lambda a, b: a - b,
        "mul": lambda a, b: a * b,
        "div": lambda a, b: a / b if b != 0 else None,
        # Logical
        "and": lambda a, b: a and b,
        "or": lambda a, b: a or b,
    }

    def __init__(self, op: str, left: RValue, right: RValue) -> None:
        """Initialize binary operation.

        Args:
            op: Operator name (gt, lt, add, sub, etc.)
            left: Left operand
            right: Right operand
        """
        self.op = op
        self.children = (left, right)

    def execute(self, context: Context) -> object:
        """Execute binary operation.

        Args:
            context: Execution context

        Returns:
            Operation result, or NaN if operands are special
        """
        from ..types import NaN, propagate_special

        # Evaluate operands
        left_val = self.children[0].execute(context)
        right_val = self.children[1].execute(context)

        # Handle special values
        special = propagate_special(left_val, right_val)
        if special is not None:
            return special

        # Apply operator
        operator = self._OPERATORS.get(self.op)
        if operator is None:
            raise ValueError(f"Unknown operator: {self.op}")

        try:
            result = operator(left_val, right_val)
            return result if result is not None else NaN
        except (TypeError, ValueError, ZeroDivisionError):
            return NaN


__all__ = [
    "BinaryOp",
    "GetOp",
    "LiteralValue",
]
