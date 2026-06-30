"""Arithmetic atoms: Python's numeric builtins and operators.

Maps Python's native numeric functions and arithmetic operators onto Nu
ScalarQueries. None touch the Context on their own - effects only ride in
through Ref children.

Builtins / operators to cover (Python -> Nu):
- ``+`` -> ``AddQuery``, ``-`` -> ``SubQuery``, ``*`` -> ``MulQuery``, ``/`` -> ``DivQuery``
- ``//`` -> ``FloorDivQuery``, ``%`` -> ``ModQuery``, ``**`` / ``pow`` -> ``PowQuery``
- unary ``-`` -> ``NegQuery``, unary ``+`` -> ``PosQuery``, ``abs`` -> ``AbsQuery``
- ``divmod`` -> ``DivModQuery``, ``round`` -> ``RoundQuery``

Sorts: all ScalarQuery (Q). ``AddQuery`` and ``MulQuery`` are commutative + associative
and fold a variadic child list; the rest are neither. ``SubQuery``, ``DivQuery``,
``FloorDivQuery``, ``ModQuery``, ``PowQuery`` and ``DivModQuery`` are binary. ``NegQuery``, ``PosQuery`` and
``AbsQuery`` are unary. ``RoundQuery`` takes one child (value) or two (value, ndigits).
``DivModQuery`` yields the ``(quotient, remainder)`` pair as its single scalar.

Each atom defines ``compile`` (sync hot path) and ``acompile`` (async hot
path). Both return a thunk ``(rt) -> value`` (sync) or ``(rt) -> awaitable``
(async) that captures the precompiled child thunks, so recursion skips the
``Runtime.eval`` / ``Runtime.aeval`` dispatch hop per child. Sentinel
propagation is inlined: an EMPTY or INVALID operand collapses the result to
INVALID without further folding.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = [
    "AbsQuery",
    "AddQuery",
    "DivModQuery",
    "DivQuery",
    "FloorDivQuery",
    "ModQuery",
    "MulQuery",
    "NegQuery",
    "PosQuery",
    "PowQuery",
    "RoundQuery",
    "SubQuery",
]


class AddQuery(ScalarQuery):
    """The sum of its scalar children."""

    commutative = Declared(value=True)
    associative = Declared(value=True)

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        def thunk(rt: Runtime) -> object:
            s: object = 0  # additive identity for the no-children case
            for i, ct in enumerate(children):
                v = ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                # Fold from the first operand so `+` works for any type that
                # supports it (str / list / tuple concat), not just numbers.
                s = v if i == 0 else s + v
            return s

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        async def athunk(rt: Runtime) -> object:
            s: object = 0  # additive identity for the no-children case
            for i, ct in enumerate(children):
                v = await ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                s = v if i == 0 else s + v
            return s

        return athunk


class MulQuery(ScalarQuery):
    """The product of its scalar children."""

    commutative = Declared(value=True)
    associative = Declared(value=True)

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        def thunk(rt: Runtime) -> object:
            out: object = 1
            for ct in children:
                v = ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out * v
            return out

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        async def athunk(rt: Runtime) -> object:
            out: object = 1
            for ct in children:
                v = await ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out * v
            return out

        return athunk


class SubQuery(ScalarQuery):
    """The first child minus the second."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = children

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a - b

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
            return a - b

        return athunk


class DivQuery(ScalarQuery):
    """The first child divided by the second (true division)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = children

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a / b

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
            return a / b

        return athunk


class FloorDivQuery(ScalarQuery):
    """The first child floor-divided by the second."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = children

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a // b

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
            return a // b

        return athunk


class ModQuery(ScalarQuery):
    """The first child modulo the second."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = children

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a % b

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
            return a % b

        return athunk


class PowQuery(ScalarQuery):
    """The first child raised to the power of the second."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = children

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a**b

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
            return a**b

        return athunk


class NegQuery(ScalarQuery):
    """The arithmetic negation of its one child."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return -v

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return -v

        return athunk


class PosQuery(ScalarQuery):
    """The unary plus of its one child."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return +v

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return +v

        return athunk


class AbsQuery(ScalarQuery):
    """The absolute value of its one child."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return abs(v)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return abs(v)

        return athunk


class DivModQuery(ScalarQuery):
    """The ``(quotient, remainder)`` pair of its two children."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        left, right = children

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return divmod(a, b)

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
            return divmod(a, b)

        return athunk


class RoundQuery(ScalarQuery):
    """The first child rounded, to the second child's digits when given."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        if len(children) == 1:
            (only,) = children

            def thunk_value(rt: Runtime) -> object:
                v = only(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                return round(v)

            return thunk_value

        value, ndigits = children

        def thunk(rt: Runtime) -> object:
            v = value(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            n = ndigits(rt)
            if n is EMPTY or n is INVALID:
                return INVALID
            return round(v, n)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        if len(children) == 1:
            (only,) = children

            async def athunk_value(rt: Runtime) -> object:
                v = await only(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                return round(v)

            return athunk_value

        value, ndigits = children

        async def athunk(rt: Runtime) -> object:
            v = await value(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            n = await ndigits(rt)
            if n is EMPTY or n is INVALID:
                return INVALID
            return round(v, n)

        return athunk
