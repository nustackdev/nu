"""Logic atoms: comparison and boolean ScalarQueries.

Concrete ScalarQuery kinds that yield a boolean. And and Or are commutative,
associative and idempotent; Eq is commutative; Lt and Not are neither. Eager
evaluation - And and Or fold every operand instead of short-circuiting, so
sentinel propagation has the chance to fire on any branch.

Each atom defines ``compile`` (sync hot path) and ``acompile`` (async hot path).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine.structure import Attribute
from nu2.lang import ScalarQuery
from nu2.lang.evaluation.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.evaluation.runtime import NuRuntime as Runtime

__all__ = ["And", "Eq", "Lt", "Not", "Or"]


class Eq(ScalarQuery):
    """Whether its two children are equal."""

    commutative = Attribute.declared(True)

    def compile(self, nid: int, kids: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = kids

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a == b

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
            return a == b

        return athunk


class Lt(ScalarQuery):
    """Whether the first child is less than the second."""

    def compile(self, nid: int, kids: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = kids

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a < b

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
            return a < b

        return athunk


class And(ScalarQuery):
    """The conjunction of its boolean children."""

    commutative = Attribute.declared(True)
    associative = Attribute.declared(True)
    idempotent = Attribute.declared(True)

    def compile(self, nid: int, kids: tuple[Callable, ...]) -> Callable:  # noqa: D102
        def thunk(rt: Runtime) -> object:
            out = True
            for kt in kids:
                v = kt(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out and bool(v)
            return out

        return thunk

    def acompile(self, nid: int, kids: tuple[Callable, ...]) -> Callable:  # noqa: D102
        async def athunk(rt: Runtime) -> object:
            out = True
            for kt in kids:
                v = await kt(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out and bool(v)
            return out

        return athunk


class Or(ScalarQuery):
    """The disjunction of its boolean children."""

    commutative = Attribute.declared(True)
    associative = Attribute.declared(True)
    idempotent = Attribute.declared(True)

    def compile(self, nid: int, kids: tuple[Callable, ...]) -> Callable:  # noqa: D102
        def thunk(rt: Runtime) -> object:
            out = False
            for kt in kids:
                v = kt(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out or bool(v)
            return out

        return thunk

    def acompile(self, nid: int, kids: tuple[Callable, ...]) -> Callable:  # noqa: D102
        async def athunk(rt: Runtime) -> object:
            out = False
            for kt in kids:
                v = await kt(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out or bool(v)
            return out

        return athunk


class Not(ScalarQuery):
    """The negation of its one boolean child."""

    def compile(self, nid: int, kids: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = kids

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return not v

        return thunk

    def acompile(self, nid: int, kids: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = kids

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return not v

        return athunk
