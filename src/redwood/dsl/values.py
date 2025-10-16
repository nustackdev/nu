"""Value term implementations.

ValueTerms represent pure computed values (R-values). They include:
- PathValue: Reading a path (bridge from PathTerm to ValueTerm)
- LiteralValue: Constants (42, "hello", True)
- BinaryOp: Binary operations (>, <, ==, +, -, *, /, &, |)
- UnaryOp: Unary operations (not)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from redwood.dsl.metadata import TermMetadata
from redwood.dsl.term import PathTerm, ValueTerm
from redwood.dsl.types import NaN, TermResult, is_special, propagate_special


if TYPE_CHECKING:
    from redwood.tree import ContextType, Tree

__all__ = ["BinaryOp", "LiteralValue", "PathValue", "UnaryOp"]


@dataclass(frozen=True)
class PathValue(ValueTerm):
    """Path value: reading a path location.

    This is the bridge from PathTerm (L-value) to ValueTerm (R-value).
    Created by PathTerm.get() or implicitly in value contexts.

    Attributes:
        path: PathTerm to read
    """

    path: PathTerm

    def __init__(self, path: PathTerm) -> None:
        """Initialize path value.

        Args:
            path: PathTerm to read
        """
        object.__setattr__(self, "path", path)

        super(ValueTerm, self).__init__()

        # Inherit metadata from path
        meta = TermMetadata(
            is_pure=True,
            value_type=path.meta.primitive_type or path.meta.value_type,
            primitive_type=path.meta.primitive_type,
            schema=path.meta.schema,
            dependencies=path.meta.dependencies | frozenset([str(path.meta.resolved_path)]),
        )
        object.__setattr__(self, "meta", meta)

    def evaluate(self, tree: Tree, ctx: ContextType) -> TermResult[Any]:
        """Evaluate by reading path value.

        Args:
            tree: Tree instance
            ctx: Context for data access

        Returns:
            Value at path, or Empty if doesn't exist
        """
        return self.path.evaluate(tree, ctx)


@dataclass(frozen=True)
class LiteralValue(ValueTerm):
    """Literal constant value: 42, "hello", True, 3.14.

    Represents a constant value in an expression.

    Attributes:
        value: The literal value
    """

    value: Any

    def __init__(self, value: Any) -> None:
        """Initialize literal value.

        Args:
            value: Literal value
        """
        object.__setattr__(self, "value", value)

        super(ValueTerm, self).__init__()

        meta = TermMetadata(
            is_pure=True,
            is_constant=True,
            value_type=type(value),
        )
        object.__setattr__(self, "meta", meta)

    def evaluate(self, tree: Tree, ctx: ContextType) -> TermResult[Any]:
        """Evaluate to literal value.

        Args:
            tree: Tree instance (not used)
            ctx: Context (not used)

        Returns:
            The literal value
        """
        return self.value


# Operation implementations with Empty/NaN propagation

_OPERATORS = {
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
    "div": lambda a, b: NaN if b == 0 else a / b,  # Handle division by zero
    "mod": lambda a, b: NaN if b == 0 else a % b,
    "pow": lambda a, b: a**b,
    # Logical
    "and": lambda a, b: a and b,
    "or": lambda a, b: a or b,
}


@dataclass(frozen=True)
class BinaryOp(ValueTerm):
    """Binary operation: a > b, a + b, a & b.

    Represents any binary operation between two value terms.
    Handles Empty/NaN propagation automatically.

    Attributes:
        op: Operation name (gt, lt, eq, add, sub, mul, div, and, or)
        left: Left operand
        right: Right operand
    """

    op: str
    left: ValueTerm
    right: ValueTerm

    def __init__(self, op: str, left: ValueTerm, right: ValueTerm) -> None:
        """Initialize binary operation.

        Args:
            op: Operation name
            left: Left operand
            right: Right operand
        """
        object.__setattr__(self, "op", op)
        object.__setattr__(self, "left", left)
        object.__setattr__(self, "right", right)

        super(ValueTerm, self).__init__()

        # Determine result type
        if op in ("gt", "lt", "eq", "ne", "ge", "le", "and", "or"):
            result_type = bool
        elif op in ("add", "sub", "mul", "div", "mod", "pow"):
            # Inherit from operands (simplified - could be more sophisticated)
            result_type = left.meta.value_type or right.meta.value_type
        else:
            result_type = None

        # Pure if both operands are pure
        is_pure = left.meta.is_pure and right.meta.is_pure

        # Merge dependencies
        dependencies = left.meta.dependencies | right.meta.dependencies

        meta = TermMetadata(
            is_pure=is_pure,
            value_type=result_type,
            dependencies=dependencies,
        )
        object.__setattr__(self, "meta", meta)

    def evaluate(self, tree: Tree, ctx: ContextType) -> TermResult[Any]:
        """Evaluate binary operation with Empty/NaN propagation.

        Args:
            tree: Tree instance
            ctx: Context

        Returns:
            Operation result, or NaN if operands are special values
        """
        # Evaluate operands
        left_val = self.left.evaluate(tree, ctx)
        right_val = self.right.evaluate(tree, ctx)

        # Propagate special values
        special = propagate_special(left_val, right_val)
        if special is not None:
            return special

        # Apply operation
        operator = _OPERATORS.get(self.op)
        if operator is None:
            msg = f"Unknown operator: {self.op}"
            raise ValueError(msg)

        try:
            return operator(left_val, right_val)
        except (TypeError, ValueError, ZeroDivisionError):
            # Type mismatches or invalid operations → NaN
            return NaN


_UNARY_OPERATORS = {
    "not": lambda a: not a,
    "neg": lambda a: -a,
    "pos": lambda a: +a,
}


@dataclass(frozen=True)
class UnaryOp(ValueTerm):
    """Unary operation: not a, -a, +a.

    Represents any unary operation on a value term.
    Handles Empty/NaN propagation automatically.

    Attributes:
        op: Operation name (not, neg, pos)
        operand: Operand term
    """

    op: str
    operand: ValueTerm

    def __init__(self, op: str, operand: ValueTerm) -> None:
        """Initialize unary operation.

        Args:
            op: Operation name
            operand: Operand term
        """
        object.__setattr__(self, "op", op)
        object.__setattr__(self, "operand", operand)

        super(ValueTerm, self).__init__()

        # Determine result type
        if op == "not":
            result_type = bool
        else:
            result_type = operand.meta.value_type

        meta = TermMetadata(
            is_pure=operand.meta.is_pure,
            value_type=result_type,
            dependencies=operand.meta.dependencies,
        )
        object.__setattr__(self, "meta", meta)

    def evaluate(self, tree: Tree, ctx: ContextType) -> TermResult[Any]:
        """Evaluate unary operation with Empty/NaN propagation.

        Args:
            tree: Tree instance
            ctx: Context

        Returns:
            Operation result, or NaN if operand is special value
        """
        # Evaluate operand
        operand_val = self.operand.evaluate(tree, ctx)

        # Propagate special values
        if is_special(operand_val):
            return NaN

        # Apply operation
        operator = _UNARY_OPERATORS.get(self.op)
        if operator is None:
            msg = f"Unknown unary operator: {self.op}"
            raise ValueError(msg)

        try:
            return operator(operand_val)
        except (TypeError, ValueError):
            return NaN
