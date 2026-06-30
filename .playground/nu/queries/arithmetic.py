"""Arithmetic ops.

Unary: Neg, Abs, Pos
Binary: Add, Sub, Mul, Div, FloorDiv, Mod, Pow
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.types import Mode


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


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


# =============================================================================
# UNARY ARITHMETIC
# =============================================================================


class Neg(ScalarQuery):
    """Negation: -operand."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        return -ops[0]


class Abs(ScalarQuery):
    """Absolute value: abs(operand)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        return abs(ops[0])


class Pos(ScalarQuery):
    """Unary plus: +operand."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        return +ops[0]


# =============================================================================
# BINARY ARITHMETIC
# =============================================================================


class Add(ScalarQuery):
    """Addition: left + right."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    commutative: ClassVar[bool] = True
    associative: ClassVar[bool] = True

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        return ops[0] + ops[1]


class Sub(ScalarQuery):
    """Subtraction: left - right."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        return ops[0] - ops[1]


class Mul(ScalarQuery):
    """Multiplication: left * right."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    commutative: ClassVar[bool] = True
    associative: ClassVar[bool] = True

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        return ops[0] * ops[1]


class Div(ScalarQuery):
    """Division: left / right."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        return ops[0] / ops[1]


class FloorDiv(ScalarQuery):
    """Floor division: left // right."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        return ops[0] // ops[1]


class Mod(ScalarQuery):
    """Modulo: left % right."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        return ops[0] % ops[1]


class Pow(ScalarQuery):
    """Power: left ** right."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        return ops[0] ** ops[1]
