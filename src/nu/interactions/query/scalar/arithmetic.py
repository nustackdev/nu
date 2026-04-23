"""Arithmetic ops.

Unary: Neg, Abs, Pos
Binary: Add, Sub, Mul, Div, FloorDiv, Mod, Pow
"""

from __future__ import annotations

from typing import ClassVar

from nu.terms import BinaryScalar, Mode, UnaryScalar


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


class Neg[ResultT](UnaryScalar[ResultT]):
    """Negation: -operand."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> ResultT:
        """Apply."""
        return -operand  # type: ignore


class Abs[ResultT](UnaryScalar[ResultT]):
    """Absolute value: abs(operand)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> ResultT:
        """Apply."""
        return abs(operand)  # type: ignore


class Pos[ResultT](UnaryScalar[ResultT]):
    """Unary plus: +operand."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: object) -> ResultT:
        """Apply."""
        return +operand  # type: ignore


# =============================================================================
# BINARY ARITHMETIC
# =============================================================================


class Add[ResultT](BinaryScalar[ResultT]):
    """Addition: left + right."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left + right  # type: ignore


class Sub[ResultT](BinaryScalar[ResultT]):
    """Subtraction: left - right."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left - right  # type: ignore


class Mul[ResultT](BinaryScalar[ResultT]):
    """Multiplication: left * right."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left * right  # type: ignore


class Div[ResultT](BinaryScalar[ResultT]):
    """Division: left / right."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left / right  # type: ignore


class FloorDiv[ResultT](BinaryScalar[ResultT]):
    """Floor division: left // right."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left // right  # type: ignore


class Mod[ResultT](BinaryScalar[ResultT]):
    """Modulo: left % right."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left % right  # type: ignore


class Pow[ResultT](BinaryScalar[ResultT]):
    """Power: left ** right."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left**right  # type: ignore
