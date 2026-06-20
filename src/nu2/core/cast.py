"""Cast atoms: Python's type constructors and conversions.

Maps Python's builtin type constructors onto Nu ScalarQueries that build a
value of the target type from their argument. Pure compute; no Context effect
of their own.

The split follows one rule - what the constructor consumes:

- scalar casts take a scalar operand and compute a scalar, so they are pure
  ScalarQueries with ``compile`` / ``acompile`` thunks (sentinel-aware, like
  ``arithmetic``): ``int`` -> ``Int``, ``float`` -> ``Float``,
  ``complex`` -> ``Complex``, ``str`` -> ``Str``, ``bytes`` -> ``Bytes``,
  ``bytearray`` -> ``ByteArray``. ``Int``, ``Bytes`` and ``ByteArray`` take an
  optional second operand (base / encoding) where Python does, branched on
  child count like ``arithmetic.Round``.
- collection constructors consume an iterable child and fold it to one
  container (Scalar over Stream, a Reduction in spirit), so they need the
  stream/fabric runtime that is not wired yet. They are declared
  structurally - ScalarQuery subclasses with no ``compile`` - matching v1, and
  evaluate once the fabric lands: ``list`` -> ``List``, ``tuple`` -> ``Tuple``,
  ``set`` -> ``Set``, ``frozenset`` -> ``FrozenSet``, ``dict`` -> ``Dict``.

``Bool`` truthiness lives in ``logical``; it is intentionally not defined here.

v1 reference: ``src/nu/queries/conversion.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.lang import ScalarQuery
from nu2.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.runtime import Runtime

__all__ = [
    "ByteArray",
    "Bytes",
    "Complex",
    "Dict",
    "Float",
    "FrozenSet",
    "Int",
    "List",
    "Set",
    "Str",
    "Tuple",
]


# --- scalar casts: evaluable ScalarQueries -------------------------------


class Int(ScalarQuery):
    """The operand cast to ``int``; with a second child, parsed in that base."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        if len(children) == 1:
            (only,) = children

            def thunk_value(rt: Runtime) -> object:
                v = only(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                return int(v)

            return thunk_value

        value, base = children

        def thunk(rt: Runtime) -> object:
            v = value(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            b = base(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return int(v, b)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        if len(children) == 1:
            (only,) = children

            async def athunk_value(rt: Runtime) -> object:
                v = await only(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                return int(v)

            return athunk_value

        value, base = children

        async def athunk(rt: Runtime) -> object:
            v = await value(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            b = await base(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return int(v, b)

        return athunk


class Float(ScalarQuery):
    """The operand cast to ``float``."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return float(v)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return float(v)

        return athunk


class Complex(ScalarQuery):
    """The operand cast to ``complex``; with a second child, the imaginary part."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class Str(ScalarQuery):
    """The operand cast to ``str``."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return str(v)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return str(v)

        return athunk


class Bytes(ScalarQuery):
    """The operand cast to ``bytes``; with a second child, encoded in it."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class ByteArray(ScalarQuery):
    """The operand cast to ``bytearray``; with a second child, encoded in it."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


# --- collection constructors: structural, evaluable once the fabric lands -


class List(ScalarQuery):
    """The iterable child collected into a ``list``."""


class Tuple(ScalarQuery):
    """The iterable child collected into a ``tuple``."""


class Set(ScalarQuery):
    """The iterable child collected into a ``set``."""


class FrozenSet(ScalarQuery):
    """The iterable child collected into a ``frozenset``."""


class Dict(ScalarQuery):
    """The key/value pairs of the iterable child collected into a ``dict``."""
