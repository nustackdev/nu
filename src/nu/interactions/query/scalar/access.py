"""Collection access ops.

At: Subscript access (seq[key], dict[key])
Slice: Slice access (seq[start:stop:step])
Len: Length (len(obj))
Contains: Containment check (item in container)
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.types import Mode


__all__ = [
    "At",
    "Contains",
    "Len",
    "Slice",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class Len(ScalarQuery):
    """Length: len(operand)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> int:  # noqa: ANN401
        return len(ops[0])


class At(ScalarQuery):
    """Subscript access: left[right]."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        return ops[0][ops[1]]


class Slice(ScalarQuery):
    """Slice access: operand[start:stop:step]."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any, start: Any, stop: Any, step: Any) -> None:  # noqa: ANN401
        super().__init__(operand, start, stop, step)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand, start, stop, step = ops
        return operand[slice(start, stop, step)]


class Contains(ScalarQuery):
    """Containment check: right in left."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> bool:  # noqa: ANN401
        return ops[1] in ops[0]
