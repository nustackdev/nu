"""Comparison atoms: Python's ordering and identity operators.

Maps Python's comparison operators onto Nu ScalarQueries yielding a bool. Pure
compute over their operands; no Context effect of their own.

Operators to cover (Python -> Nu):
- ``==`` -> ``EqQuery``, ``!=`` -> ``NeQuery``
- ``<`` -> ``LtQuery``, ``>`` -> ``GtQuery``, ``<=`` -> ``LeQuery``, ``>=`` -> ``GeQuery``
- ``is`` / ``is not`` -> ``IsQuery`` (identity)

Sorts: all ScalarQuery (Q). ``EqQuery`` / ``NeQuery`` / ``IsQuery`` are commutative; the
orderings are not. Membership (``in``) lives in ``access`` as ``Contains``.

Each atom is binary and defines ``compile`` (sync hot path) and ``acompile``
(async hot path). Both return a thunk ``(rt) -> value`` (sync) or
``(rt) -> awaitable`` (async) that captures the precompiled child thunks, so
recursion skips the ``Runtime.eval`` / ``Runtime.aeval`` dispatch hop per
child. Sentinel propagation is inlined: an EMPTY or INVALID operand collapses
the result to INVALID without comparing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["EqQuery", "GeQuery", "GtQuery", "IsQuery", "LeQuery", "LtQuery", "NeQuery"]


class EqQuery(ScalarQuery):
    """Whether its two children are equal (``==``)."""

    commutative = Declared(value=True)

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = children

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a == b

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = children

        async def athunk(rt: Runtime) -> object:
            a = await left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a == b

        return athunk


class NeQuery(ScalarQuery):
    """Whether its two children are unequal (``!=``)."""

    commutative = Declared(value=True)

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = children

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a != b

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = children

        async def athunk(rt: Runtime) -> object:
            a = await left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a != b

        return athunk


class LtQuery(ScalarQuery):
    """Whether the first child is less than the second (``<``)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = children

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a < b

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = children

        async def athunk(rt: Runtime) -> object:
            a = await left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a < b

        return athunk


class GtQuery(ScalarQuery):
    """Whether the first child is greater than the second (``>``)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = children

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a > b

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = children

        async def athunk(rt: Runtime) -> object:
            a = await left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a > b

        return athunk


class LeQuery(ScalarQuery):
    """Whether the first child is less than or equal to the second (``<=``)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = children

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a <= b

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = children

        async def athunk(rt: Runtime) -> object:
            a = await left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a <= b

        return athunk


class GeQuery(ScalarQuery):
    """Whether the first child is greater than or equal to the second (``>=``)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = children

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a >= b

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = children

        async def athunk(rt: Runtime) -> object:
            a = await left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a >= b

        return athunk


class IsQuery(ScalarQuery):
    """Whether its two children are the same object (``is``)."""

    commutative = Declared(value=True)

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = children

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a is b

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = children

        async def athunk(rt: Runtime) -> object:
            a = await left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a is b

        return athunk
