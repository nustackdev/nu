"""Arithmetic atoms: Python's numeric builtins and operators.

Maps Python's native numeric functions and arithmetic operators onto Nu
ScalarQueries. None touch the Context on their own - effects only ride in
through Ref children.

Builtins / operators to cover (Python -> Nu):
- ``+`` -> ``Add``, ``-`` -> ``Sub``, ``*`` -> ``Mul``, ``/`` -> ``Div``
- ``//`` -> ``FloorDiv``, ``%`` -> ``Mod``, ``**`` / ``pow`` -> ``Pow``
- unary ``-`` -> ``Neg``, unary ``+`` -> ``Pos``, ``abs`` -> ``Abs``
- ``divmod`` -> ``DivMod``, ``round`` -> ``Round``

Sorts: all ScalarQuery (Q). ``Add`` and ``Mul`` are commutative + associative
and fold a variadic child list; the rest are neither. ``Sub``, ``Div``,
``FloorDiv``, ``Mod``, ``Pow`` and ``DivMod`` are binary. ``Neg``, ``Pos`` and
``Abs`` are unary. ``Round`` takes one child (value) or two (value, ndigits).
``DivMod`` yields the ``(quotient, remainder)`` pair as its single scalar.

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
    "Abs",
    "Add",
    "Div",
    "DivMod",
    "FloorDiv",
    "Mod",
    "Mul",
    "Neg",
    "Pos",
    "Pow",
    "Round",
    "Sub",
]


class Add(ScalarQuery):
    """The sum of its scalar children."""

    _commutative = Declared(value=True, name="commutative")
    _associative = Declared(value=True, name="associative")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            s: object = 0  # additive identity for the no-children case
            for i, ct in enumerate(children):
                v = await ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                s = v if i == 0 else s + v
            return s

        return athunk


class Mul(ScalarQuery):
    """The product of its scalar children."""

    _commutative = Declared(value=True, name="commutative")
    _associative = Declared(value=True, name="associative")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            out: object = 1
            for ct in children:
                v = ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out * v
            return out

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            out: object = 1
            for ct in children:
                v = await ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out * v
            return out

        return athunk


class MatMul(ScalarQuery):
    """The matrix product of its two children (``a @ b``)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left, right = children

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a @ b

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left, right = children

        async def athunk(rt: Runtime) -> object:
            a = await left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a @ b

        return athunk


class Sub(ScalarQuery):
    """The first child minus the second."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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


class Div(ScalarQuery):
    """The first child divided by the second (true division)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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


class FloorDiv(ScalarQuery):
    """The first child floor-divided by the second."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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


class Mod(ScalarQuery):
    """The first child modulo the second."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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


class Pow(ScalarQuery):
    """The first child raised to the power of the second."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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


class Neg(ScalarQuery):
    """The arithmetic negation of its one child."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return -v

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return -v

        return athunk


class Pos(ScalarQuery):
    """The unary plus of its one child."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return +v

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return +v

        return athunk


class Abs(ScalarQuery):
    """The absolute value of its one child."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return abs(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return abs(v)

        return athunk


class DivMod(ScalarQuery):
    """The ``(quotient, remainder)`` pair of its two children."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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


class Round(ScalarQuery):
    """The first child rounded, to the second child's digits when given."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
