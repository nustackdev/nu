"""Logical ops.

Unary: Not, Bool
Binary: And, Or (with short-circuit evaluation)

And and Or override open() for short-circuit semantics.
"""

from __future__ import annotations

from contextlib import aclosing, closing
from typing import TYPE_CHECKING, Any

from nu.terms import BinaryScalar, Sentinel, UnaryScalar, propagate_special


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator

    from nu.context import Context
    from nu.terms import Nu


__all__ = [
    "And",
    "Bool",
    "Not",
    "Or",
]


# =============================================================================
# UNARY LOGICAL
# =============================================================================


class Not[ResultT](UnaryScalar[ResultT]):
    """Logical NOT: not operand.

    Python's 'not' keyword cannot be overloaded.
    Use .not_() method in trait classes instead.
    """

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        return not operand  # type: ignore


class Bool(UnaryScalar[bool]):
    """Boolean conversion: bool(operand)."""

    def apply(self, operand: object) -> bool:
        """Apply."""
        return bool(operand)


# =============================================================================
# BINARY LOGICAL (with short-circuit)
# =============================================================================


async def _drain_last(child: Nu, ctx: Context) -> Any:
    val: Any = None
    async with aclosing(child.aopen(ctx)) as gen:
        async for v in gen:
            val = v
    return val


def _drain_last_sync(child: Nu, ctx: Context) -> Any:
    val: Any = None
    with closing(child.open(ctx)) as gen:
        for v in gen:
            val = v
    return val


class And[ResultT](BinaryScalar[ResultT]):
    """Logical AND: left and right.

    Overrides open() for short-circuit evaluation:
    if left is falsy, yields left without evaluating right.
    """

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:  # type: ignore[override]
        left_val = await _drain_last(self._children[0], ctx)

        sp = propagate_special(left_val)
        if sp is not None:
            yield sp
            return

        if not left_val:
            yield left_val
            return

        right_val = await _drain_last(self._children[1], ctx)

        special = propagate_special(right_val)
        if special is not None:
            yield special
            return

        yield left_val and right_val

    def open(self, ctx: Context) -> Generator[Any, None, None]:  # type: ignore[override]
        left_val = _drain_last_sync(self._children[0], ctx)

        sp = propagate_special(left_val)
        if sp is not None:
            yield sp
            return

        if not left_val:
            yield left_val
            return

        right_val = _drain_last_sync(self._children[1], ctx)

        special = propagate_special(right_val)
        if special is not None:
            yield special
            return

        yield left_val and right_val

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        # Not used - open() handles everything
        raise NotImplementedError


class Or[ResultT](BinaryScalar[ResultT]):
    """Logical OR: left or right.

    Overrides open() for short-circuit evaluation:
    if left is truthy, yields left without evaluating right.
    """

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:  # type: ignore[override]
        left_val = await _drain_last(self._children[0], ctx)

        sp = propagate_special(left_val)
        if sp is not None:
            yield sp
            return

        if left_val:
            yield left_val
            return

        right_val = await _drain_last(self._children[1], ctx)

        special = propagate_special(right_val)
        if special is not None:
            yield special
            return

        yield left_val or right_val

    def open(self, ctx: Context) -> Generator[Any, None, None]:  # type: ignore[override]
        left_val = _drain_last_sync(self._children[0], ctx)

        sp = propagate_special(left_val)
        if sp is not None:
            yield sp
            return

        if left_val:
            yield left_val
            return

        right_val = _drain_last_sync(self._children[1], ctx)

        special = propagate_special(right_val)
        if special is not None:
            yield special
            return

        yield left_val or right_val

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        # Not used - open() handles everything
        raise NotImplementedError
