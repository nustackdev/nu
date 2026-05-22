"""Arithmetic atoms: literals and the numeric ScalarQueries.

Concrete ScalarQuery kinds on ``nu2.lang``. A Literal carries a constant in
its payload; Add and Mul are commutative and associative, Sub, Div and Neg
are neither. None touch the Context on their own - effects come from Ref
children.

Each atom defines ``compile`` (sync hot path) and ``acompile`` (async hot
path). Both return a thunk ``(rt) -> value`` (sync) or ``(rt) -> awaitable``
(async) that captures the precompiled child thunks, so recursion skips the
``Runtime.eval`` / ``Runtime.aeval`` dispatch hop per child. Sentinel
propagation is inlined: an EMPTY or INVALID operand collapses the result to
INVALID without further folding.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine.structure import Attribute
from nu2.lang import ScalarQuery
from nu2.lang.evaluation.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.evaluation.runtime import NuRuntime as Runtime

__all__ = ["Add", "Div", "Literal", "Mul", "Neg", "Sub"]


class Literal(ScalarQuery):
    """A ScalarQuery that yields a constant value carried in its payload."""

    def __init__(self, value: object) -> None:
        super().__init__()
        self.payload = {"value": value}

    def compile(self, nid: int, kids: tuple[Callable, ...]) -> Callable:  # noqa: D102
        value = self.payload["value"]

        def thunk(rt: Runtime) -> object:
            return value

        return thunk

    def acompile(self, nid: int, kids: tuple[Callable, ...]) -> Callable:  # noqa: D102
        value = self.payload["value"]

        async def athunk(rt: Runtime) -> object:
            return value

        return athunk


class Add(ScalarQuery):
    """The sum of its scalar children."""

    commutative = Attribute.declared(True)
    associative = Attribute.declared(True)

    def compile(self, nid: int, kids: tuple[Callable, ...]) -> Callable:  # noqa: D102
        def thunk(rt: Runtime) -> object:
            s: object = 0
            for kt in kids:
                v = kt(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                s = s + v
            return s

        return thunk

    def acompile(self, nid: int, kids: tuple[Callable, ...]) -> Callable:  # noqa: D102
        async def athunk(rt: Runtime) -> object:
            s: object = 0
            for kt in kids:
                v = await kt(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                s = s + v
            return s

        return athunk


class Mul(ScalarQuery):
    """The product of its scalar children."""

    commutative = Attribute.declared(True)
    associative = Attribute.declared(True)

    def compile(self, nid: int, kids: tuple[Callable, ...]) -> Callable:  # noqa: D102
        def thunk(rt: Runtime) -> object:
            out: object = 1
            for kt in kids:
                v = kt(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out * v
            return out

        return thunk

    def acompile(self, nid: int, kids: tuple[Callable, ...]) -> Callable:  # noqa: D102
        async def athunk(rt: Runtime) -> object:
            out: object = 1
            for kt in kids:
                v = await kt(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out * v
            return out

        return athunk


class Sub(ScalarQuery):
    """The first child minus the second."""

    def compile(self, nid: int, kids: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = kids

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a - b

        return thunk

    def acompile(self, nid: int, kids: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = kids

        async def athunk(rt: Runtime) -> object:
            a = await left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a - b

        return athunk


class Div(ScalarQuery):
    """The first child divided by the second."""

    def compile(self, nid: int, kids: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = kids

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a / b

        return thunk

    def acompile(self, nid: int, kids: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = kids

        async def athunk(rt: Runtime) -> object:
            a = await left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a / b

        return athunk


class Neg(ScalarQuery):
    """The arithmetic negation of its one child."""

    def compile(self, nid: int, kids: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = kids

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return -v

        return thunk

    def acompile(self, nid: int, kids: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = kids

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return -v

        return athunk
