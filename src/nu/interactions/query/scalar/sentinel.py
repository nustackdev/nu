"""Sentinel check ops.

IsEmpty, IsInvalid, NotEmpty, NotInvalid

These accept sentinels (don't propagate them). They use `accepts_sentinels = True`
on ScalarQuery so the sentinel-propagation wrap doesn't short-circuit them.
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.sentinels import is_empty, is_invalid
from nu.terms.types import Mode


__all__ = [
    "IsEmpty",
    "IsInvalid",
    "NotEmpty",
    "NotInvalid",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class IsEmpty(ScalarQuery):
    """Check if operand is Empty sentinel."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = True

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> bool:  # noqa: ANN401
        return is_empty(ops[0])


class NotEmpty(ScalarQuery):
    """Check if operand is NOT Empty sentinel."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = True

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> bool:  # noqa: ANN401
        return not is_empty(ops[0])


class IsInvalid(ScalarQuery):
    """Check if operand is Invalid sentinel."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = True

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> bool:  # noqa: ANN401
        return is_invalid(ops[0])


class NotInvalid(ScalarQuery):
    """Check if operand is NOT Invalid sentinel."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = True

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> bool:  # noqa: ANN401
        return not is_invalid(ops[0])
