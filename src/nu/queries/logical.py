"""Logical ops.

Unary: Not, Bool
Binary: And, Or (with short-circuit evaluation)

And and Or override eval/aeval directly for short-circuit semantics.
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu.terms.query import ScalarQuery, _child_aeval, _child_eval
from nu.terms.sentinels import INVALID, is_sentinel
from nu.terms.types import Mode


__all__ = [
    "And",
    "Bool",
    "Not",
    "Or",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class Not(ScalarQuery):
    """Logical NOT: not operand."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        return not ops[0]


class Bool(ScalarQuery):
    """Boolean conversion: bool(operand)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> bool:  # noqa: ANN401
        return bool(ops[0])


class And(ScalarQuery):
    """Logical AND with short-circuit."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    commutative: ClassVar[bool] = True
    associative: ClassVar[bool] = True

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def eval(self, ctx: Any) -> Any:  # noqa: ANN401
        left = _child_eval(self._children[0], ctx)
        if is_sentinel(left):
            return INVALID
        if not left:
            return left
        right = _child_eval(self._children[1], ctx)
        if is_sentinel(right):
            return INVALID
        return left and right

    async def aeval(self, ctx: Any) -> Any:  # noqa: ANN401
        left = await _child_aeval(self._children[0], ctx)
        if is_sentinel(left):
            return INVALID
        if not left:
            return left
        right = await _child_aeval(self._children[1], ctx)
        if is_sentinel(right):
            return INVALID
        return left and right


class Or(ScalarQuery):
    """Logical OR with short-circuit."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    commutative: ClassVar[bool] = True
    associative: ClassVar[bool] = True

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def eval(self, ctx: Any) -> Any:  # noqa: ANN401
        left = _child_eval(self._children[0], ctx)
        if is_sentinel(left):
            return INVALID
        if left:
            return left
        right = _child_eval(self._children[1], ctx)
        if is_sentinel(right):
            return INVALID
        return left or right

    async def aeval(self, ctx: Any) -> Any:  # noqa: ANN401
        left = await _child_aeval(self._children[0], ctx)
        if is_sentinel(left):
            return INVALID
        if left:
            return left
        right = await _child_aeval(self._children[1], ctx)
        if is_sentinel(right):
            return INVALID
        return left or right
