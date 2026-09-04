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
    """The operand cast to ``int``.

    Args:
        value: the value to convert.
        base: optional. When given, ``value`` is parsed as a string in this
            base instead of being converted directly.

    Notes:
        - Without ``base``, follows ``int()``: numeric strings, floats
          (truncated toward zero) and bools all convert.
        - With ``base``, follows ``int(str, base)``: ``value`` must be a
          string, and a malformed literal for that base raises.

    Yields:
        The int. INVALID when either child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.ToInt("42"))[0]
        42

        >>> nu.run(nu.ToInt("2a", 16))[0]
        42
    """

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
    """The operand cast to ``float``.

    Args:
        value: the value to convert.

    Yields:
        The float. INVALID when the child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.ToFloat("3.14"))[0]
        3.14
    """

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
    """The operand cast to ``complex``.

    Args:
        real: the value to convert, or the real part when ``imag`` is given.
        imag: optional imaginary part.

    Notes:
        - Without ``imag``, follows single-argument ``complex()``: numbers
          and complex-literal strings both convert.

    Yields:
        The complex number. INVALID when either child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.ToComplex(2, 3))[0]
        (2+3j)
    """

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
    """The operand cast to ``str``.

    Args:
        value: the value to convert.

    Yields:
        The string. INVALID when the child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.ToStr(42))[0]
        '42'
    """

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
    """The operand cast to ``bytes``.

    Args:
        value: the value to convert.
        encoding: optional. When given, ``value`` must be a string and is
            encoded with it. Without it, follows single-argument ``bytes()``:
            an int yields that many zero bytes, an iterable of ints yields
            those bytes.

    Yields:
        The bytes. INVALID when either child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.ToBytes("hi", "utf-8"))[0]
        b'hi'
    """

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
    """The operand cast to ``bytearray``.

    Args:
        value: the value to convert.
        encoding: optional. When given, ``value`` must be a string and is
            encoded with it. Without it, follows single-argument
            ``bytearray()``: an int yields that many zero bytes, an iterable
            of ints yields those bytes.

    Yields:
        The bytearray. INVALID when either child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.ToByteArray("hi", "utf-8"))[0]
        bytearray(b'hi')
    """

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
    """The iterable child collected into a ``list``.

    Args:
        value: the iterable to collect.

    Yields:
        The list. INVALID when the child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.ToList((1, 2, 3)))[0]
        [1, 2, 3]
    """

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
    """The iterable child collected into a ``tuple``.

    Args:
        value: the iterable to collect.

    Yields:
        The tuple. INVALID when the child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.ToTuple([1, 2, 3]))[0]
        (1, 2, 3)
    """

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
    """The iterable child collected into a ``set``.

    Args:
        value: the iterable to collect.

    Notes:
        - Duplicates collapse and order is not preserved, as for any
          Python ``set``.

    Yields:
        The set. INVALID when the child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.ToSet([1, 1, 2]))[0]
        {1, 2}
    """

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
    """The iterable child collected into a ``frozenset``.

    Args:
        value: the iterable to collect.

    Notes:
        - Duplicates collapse and order is not preserved, as for any
          Python ``frozenset``.

    Yields:
        The frozenset. INVALID when the child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.ToFrozenSet([1, 1, 2]))[0]
        frozenset({1, 2})
    """

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
    """The key/value pairs of the iterable child collected into a ``dict``.

    Args:
        value: an iterable of ``(key, value)`` pairs.

    Notes:
        - A repeated key keeps the last pair's value, as for any Python
          ``dict``.

    Yields:
        The dict. INVALID when the child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.ToDict([("a", 1), ("b", 2)]))[0]
        {'a': 1, 'b': 2}
    """

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
