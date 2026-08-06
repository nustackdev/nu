"""Cast atoms: Python's type constructors and conversions.

Maps Python's builtin type constructors onto Nu ScalarQueries that build a
value of the target type from their argument. Pure compute; no Context effect
of their own.

The split follows one rule - what the constructor consumes:

- scalar casts take a scalar operand and compute a scalar, so they are pure
  ScalarQueries with ``compile`` / ``acompile`` thunks (sentinel-aware, like
  ``arithmetic``): ``int`` -> ``ToInt``, ``float`` -> ``ToFloat``,
  ``complex`` -> ``ToComplex``, ``str`` -> ``ToStr``, ``bytes`` -> ``ToBytes``,
  ``bytearray`` -> ``ToByteArray``. ``ToInt``, ``ToBytes`` and ``ToByteArray`` take an
  optional second operand (base / encoding) where Python does, branched on
  child count like ``arithmetic.Round``.
- collection constructors consume an iterable child and fold it to one
  container (Scalar over Stream, a Reduction in spirit), so they need the
  stream/fabric runtime that is not wired yet. They are declared
  structurally - ScalarQuery subclasses with no ``compile`` - and
  evaluate once the fabric lands: ``list`` -> ``ToList``, ``tuple`` -> ``ToTuple``,
  ``set`` -> ``ToSet``, ``frozenset`` -> ``ToFrozenSet``, ``dict`` -> ``ToDict``.

``Bool`` truthiness lives in ``logical``; it is intentionally not defined here.
"""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

from nu.lang import ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = [
    "ToByteArray",
    "ToBytes",
    "ToComplex",
    "ToDict",
    "ToFloat",
    "ToFrozenSet",
    "ToInt",
    "ToList",
    "ToSet",
    "ToStr",
    "ToTuple",
]


# --- scalar casts: evaluable ScalarQueries -------------------------------


class ToInt(ScalarQuery):
    """The operand cast to ``int``; with a second child, parsed in that base."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        if len(children) == 1:
            (only,) = children

            def thunk_value(rt: Runtime) -> object:
                v = only(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                return builtins.int(v)

            return thunk_value

        value, base = children

        def thunk(rt: Runtime) -> object:
            v = value(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            b = base(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return builtins.int(v, b)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        if len(children) == 1:
            (only,) = children

            async def athunk_value(rt: Runtime) -> object:
                v = await only(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                return builtins.int(v)

            return athunk_value

        value, base = children

        async def athunk(rt: Runtime) -> object:
            v = await value(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            b = await base(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return builtins.int(v, b)

        return athunk


class ToFloat(ScalarQuery):
    """The operand cast to ``float``."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return builtins.float(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return builtins.float(v)

        return athunk


class ToComplex(ScalarQuery):
    """The operand cast to ``complex``; with a second child, the imaginary part."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        if len(children) == 1:
            (only,) = children

            def thunk_value(rt: Runtime) -> object:
                v = only(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                return complex(v)

            return thunk_value

        real, imag = children

        def thunk(rt: Runtime) -> object:
            a = real(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = imag(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return complex(a, b)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        if len(children) == 1:
            (only,) = children

            async def athunk_value(rt: Runtime) -> object:
                v = await only(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                return complex(v)

            return athunk_value

        real, imag = children

        async def athunk(rt: Runtime) -> object:
            a = await real(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await imag(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return complex(a, b)

        return athunk


class ToStr(ScalarQuery):
    """The operand cast to ``str``."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return builtins.str(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return builtins.str(v)

        return athunk


class ToBytes(ScalarQuery):
    """The operand cast to ``bytes``; with a second child, encoded in it."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        if len(children) == 1:
            (only,) = children

            def thunk_value(rt: Runtime) -> object:
                v = only(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                return bytes(v)

            return thunk_value

        value, encoding = children

        def thunk(rt: Runtime) -> object:
            v = value(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            e = encoding(rt)
            if e is EMPTY or e is INVALID:
                return INVALID
            return bytes(v, e)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        if len(children) == 1:
            (only,) = children

            async def athunk_value(rt: Runtime) -> object:
                v = await only(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                return bytes(v)

            return athunk_value

        value, encoding = children

        async def athunk(rt: Runtime) -> object:
            v = await value(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            e = await encoding(rt)
            if e is EMPTY or e is INVALID:
                return INVALID
            return bytes(v, e)

        return athunk


class ToByteArray(ScalarQuery):
    """The operand cast to ``bytearray``; with a second child, encoded in it."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        if len(children) == 1:
            (only,) = children

            def thunk_value(rt: Runtime) -> object:
                v = only(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                return bytearray(v)

            return thunk_value

        value, encoding = children

        def thunk(rt: Runtime) -> object:
            v = value(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            e = encoding(rt)
            if e is EMPTY or e is INVALID:
                return INVALID
            return bytearray(v, e)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        if len(children) == 1:
            (only,) = children

            async def athunk_value(rt: Runtime) -> object:
                v = await only(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                return bytearray(v)

            return athunk_value

        value, encoding = children

        async def athunk(rt: Runtime) -> object:
            v = await value(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            e = await encoding(rt)
            if e is EMPTY or e is INVALID:
                return INVALID
            return bytearray(v, e)

        return athunk


# --- collection constructors: scalar over an iterable value --------------
#
# Each takes one scalar child whose value is iterable and applies the Python
# constructor. Draining a *stream* into a container is a Reduction's job
# (``Collect``); these cast an iterable value, so the child is scalar and the
# scalar/stream law is satisfied.


class ToList(ScalarQuery):
    """The iterable child collected into a ``list``."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return builtins.list(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return builtins.list(v)

        return athunk


class ToTuple(ScalarQuery):
    """The iterable child collected into a ``tuple``."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return builtins.tuple(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return builtins.tuple(v)

        return athunk


class ToSet(ScalarQuery):
    """The iterable child collected into a ``set``."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return builtins.set(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return builtins.set(v)

        return athunk


class ToFrozenSet(ScalarQuery):
    """The iterable child collected into a ``frozenset``."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return builtins.frozenset(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return builtins.frozenset(v)

        return athunk


class ToDict(ScalarQuery):
    """The key/value pairs of the iterable child collected into a ``dict``."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return builtins.dict(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return builtins.dict(v)

        return athunk
