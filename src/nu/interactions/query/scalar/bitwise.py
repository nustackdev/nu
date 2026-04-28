"""Bitwise ops.

Unary: BitwiseNot
Binary: BitwiseAnd, BitwiseOr, Xor, LShift, RShift
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.types import Mode


__all__ = [
    "BitwiseAnd",
    "BitwiseNot",
    "BitwiseOr",
    "LShift",
    "RShift",
    "Xor",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class BitwiseNot(ScalarQuery):
    """Bitwise NOT: ~operand."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        return ~ops[0]


class BitwiseAnd(ScalarQuery):
    """Bitwise AND: left & right."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    commutative: ClassVar[bool] = True
    associative: ClassVar[bool] = True

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        return ops[0] & ops[1]


class BitwiseOr(ScalarQuery):
    """Bitwise OR: left | right."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    commutative: ClassVar[bool] = True
    associative: ClassVar[bool] = True

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        return ops[0] | ops[1]


class Xor(ScalarQuery):
    """Bitwise XOR: left ^ right."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    commutative: ClassVar[bool] = True
    associative: ClassVar[bool] = True

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        return ops[0] ^ ops[1]


class LShift(ScalarQuery):
    """Left shift: left << right."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        return ops[0] << ops[1]


class RShift(ScalarQuery):
    """Right shift: left >> right."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        return ops[0] >> ops[1]
