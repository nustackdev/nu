"""Type conversion ops.

ToInt, ToFloat, ToBool, ToStr, ToBytes, ToList, ToSet, ToTuple
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.types import Mode


__all__ = [
    "ToBool",
    "ToBytes",
    "ToFloat",
    "ToInt",
    "ToList",
    "ToSet",
    "ToStr",
    "ToTuple",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class ToInt(ScalarQuery):
    """Convert value to integer."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> int:  # noqa: ANN401
        return int(ops[0])


class ToFloat(ScalarQuery):
    """Convert value to float."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> float:  # noqa: ANN401
        return float(ops[0])


class ToBool(ScalarQuery):
    """Convert value to boolean."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> bool:  # noqa: ANN401
        return bool(ops[0])


class ToStr(ScalarQuery):
    """Convert value to string."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> str:  # noqa: ANN401
        return str(ops[0])


class ToBytes(ScalarQuery):
    """Convert value to bytes."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any, encoding: str = "utf-8") -> None:  # noqa: ANN401
        super().__init__(operand)
        self._encoding = encoding

    def _apply(self, ctx: Any, ops: list[Any]) -> bytes:  # noqa: ANN401
        operand = ops[0]
        if isinstance(operand, bytes):
            return operand
        if isinstance(operand, str):
            return operand.encode(self._encoding)
        if isinstance(operand, bytearray):
            return bytes(operand)
        return bytes(operand)


class ToList(ScalarQuery):
    """Convert value to list."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> list[Any]:  # noqa: ANN401
        return list(ops[0])


class ToSet(ScalarQuery):
    """Convert value to set."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> set[Any]:  # noqa: ANN401
        return set(ops[0])


class ToTuple(ScalarQuery):
    """Convert value to tuple."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> tuple[Any, ...]:  # noqa: ANN401
        return tuple(ops[0])
