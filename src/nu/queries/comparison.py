"""Comparison ops.

Binary: Eq, Ne, Gt, Lt, Ge, Le, IdComp
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.types import Mode


__all__ = [
    "Eq",
    "Ge",
    "Gt",
    "IdComp",
    "Le",
    "Lt",
    "Ne",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class Gt(ScalarQuery):
    """Greater than: left > right."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> bool:  # noqa: ANN401
        return ops[0] > ops[1]


class Lt(ScalarQuery):
    """Less than: left < right."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> bool:  # noqa: ANN401
        return ops[0] < ops[1]


class Eq(ScalarQuery):
    """Equality: left == right."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    commutative: ClassVar[bool] = True

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> bool:  # noqa: ANN401
        return ops[0] == ops[1]


class Ne(ScalarQuery):
    """Not equal: left != right."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    commutative: ClassVar[bool] = True

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> bool:  # noqa: ANN401
        return ops[0] != ops[1]


class Ge(ScalarQuery):
    """Greater than or equal: left >= right."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> bool:  # noqa: ANN401
        return ops[0] >= ops[1]


class Le(ScalarQuery):
    """Less than or equal: left <= right."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> bool:  # noqa: ANN401
        return ops[0] <= ops[1]


class IdComp(ScalarQuery):
    """Identity comparison: left is right."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    commutative: ClassVar[bool] = True

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> bool:  # noqa: ANN401
        return ops[0] is ops[1]
