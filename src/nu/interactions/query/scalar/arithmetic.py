"""Arithmetic ops.

Unary: Neg, Abs, Pos
Binary: Add, Sub, Mul, Div, FloorDiv, Mod, Pow
"""

from __future__ import annotations

from typing import ClassVar

from nu.terms import BinaryQuery, Mode, UnaryQuery


__all__ = [
    "Abs",
    "Add",
    "Div",
    "FloorDiv",
    "Mod",
    "Mul",
    "Neg",
    "Pos",
    "Pow",
    "Sub",
]


# =============================================================================
# UNARY ARITHMETIC
# =============================================================================


class Neg[ResultT](UnaryQuery[ResultT]):
    """Negation: -operand."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, operand: object) -> ResultT:
        """Apply."""
        return -operand  # type: ignore


class Abs[ResultT](UnaryQuery[ResultT]):
    """Absolute value: abs(operand)."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, operand: object) -> ResultT:
        """Apply."""
        return abs(operand)  # type: ignore


class Pos[ResultT](UnaryQuery[ResultT]):
    """Unary plus: +operand."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, operand: object) -> ResultT:
        """Apply."""
        return +operand  # type: ignore


# =============================================================================
# BINARY ARITHMETIC
# =============================================================================


class Add[ResultT](BinaryQuery[ResultT]):
    """Addition: left + right."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left + right  # type: ignore


class Sub[ResultT](BinaryQuery[ResultT]):
    """Subtraction: left - right."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left - right  # type: ignore


class Mul[ResultT](BinaryQuery[ResultT]):
    """Multiplication: left * right."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left * right  # type: ignore


class Div[ResultT](BinaryQuery[ResultT]):
    """Division: left / right."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left / right  # type: ignore


class FloorDiv[ResultT](BinaryQuery[ResultT]):
    """Floor division: left // right."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left // right  # type: ignore


class Mod[ResultT](BinaryQuery[ResultT]):
    """Modulo: left % right."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left % right  # type: ignore


class Pow[ResultT](BinaryQuery[ResultT]):
    """Power: left ** right."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left**right  # type: ignore
