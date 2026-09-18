"""Representation atoms: Python's string and number renderings.

Maps Python's builtins that render a value to text or to an alternate numeric
notation onto Nu ScalarQueries. Pure compute; no Context effect of their own.

Builtins to cover (Python -> Nu):
- text: ``repr`` -> ``Repr``, ``ascii`` -> ``Ascii``, ``format`` -> ``Format``
- numeric notation: ``bin`` -> ``Bin``, ``hex`` -> ``Hex``, ``oct`` -> ``Oct``
- code points: ``ord`` -> ``Ord``, ``chr`` -> ``Chr``

Sorts: all ScalarQuery (Q).

Each atom defines ``compile`` (sync hot path) and ``acompile`` (async hot
path). Both return a thunk ``(rt) -> value`` that captures the precompiled
child thunks, so recursion skips the ``Runtime.eval`` / ``Runtime.aeval``
dispatch hop per child. Sentinel propagation is inlined: an EMPTY or INVALID
operand collapses the result to INVALID without further compute.

Most atoms are unary over one child. ``Format`` mirrors Python's
``format(value[, format_spec])`` and branches on child count: one child
applies the empty format spec, two children apply the second child as the
spec.

The module name ``repr`` shadows the builtin name as a module path
(``nu.core.repr``); inside the module the builtin ``repr()`` still resolves
normally.

Most of these have no prior atom yet, so they are built fresh against the
builtins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = [
    "Ascii",
    "Bin",
    "Chr",
    "Format",
    "Hex",
    "Oct",
    "Ord",
    "Repr",
]


class Repr(ScalarQuery):
    """The ``repr`` string of its one child.

    Args:
        value: the value to represent.

    Notes:
        - Delegates to Python's ``repr``, so a string comes back quoted with
          its special characters escaped, and any type defining ``__repr__``
          renders however it chooses.

    Yields:
        The repr string. INVALID when the child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Repr("hi"))[0]
        "'hi'"
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return repr(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return repr(v)

        return athunk


class Ascii(ScalarQuery):
    r"""The ``ascii`` string of its one child, with non-ASCII escaped.

    Args:
        value: the value to represent.

    Notes:
        - Same as ``Repr`` except every non-ASCII code point comes back as a
          ``\xXX``, ``\uXXXX`` or ``\UXXXXXXXX`` escape, so the result is
          always plain ASCII text.

    Yields:
        The ascii string. INVALID when the child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Ascii("café"))[0]
        "'caf\\xe9'"
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return ascii(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return ascii(v)

        return athunk


class Format(ScalarQuery):
    """The ``format`` of a value under an optional format spec.

    Args:
        value: the value to format.
        spec: the format spec string. Optional: leave the child out entirely
            to apply the empty spec.

    Notes:
        - One child applies the empty spec (``format(value)``, usually the
          same as ``str(value)``); two children apply the second as the spec
          mini-language string (``format(value, spec)``), e.g. ``.2f`` or
          ``>10``.
        - What a given spec means is up to the value's own ``__format__``.

    Yields:
        The formatted string. INVALID when either child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Format(3.14159, ".2f"))[0]
        '3.14'
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        if len(children) == 1:
            (only,) = children

            def thunk(rt: Runtime) -> object:
                v = only(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                return format(v)

            return thunk

        value, spec = children

        def thunk_spec(rt: Runtime) -> object:
            v = value(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            s = spec(rt)
            if s is EMPTY or s is INVALID:
                return INVALID
            return format(v, s)

        return thunk_spec

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        if len(children) == 1:
            (only,) = children

            async def athunk(rt: Runtime) -> object:
                v = await only(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                return format(v)

            return athunk

        value, spec = children

        async def athunk_spec(rt: Runtime) -> object:
            v = await value(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            s = await spec(rt)
            if s is EMPTY or s is INVALID:
                return INVALID
            return format(v, s)

        return athunk_spec


class Bin(ScalarQuery):
    """The binary string (``0b...``) of its one integer child.

    Args:
        value: the integer to render.

    Notes:
        - A negative value keeps its sign in front of the prefix, e.g. -10
          renders as ``-0b1010``, not a two's-complement bit pattern.

    Yields:
        The binary string. INVALID when the child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Bin(10))[0]
        '0b1010'
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return bin(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return bin(v)

        return athunk


class Hex(ScalarQuery):
    """The hexadecimal string (``0x...``) of its one integer child.

    Args:
        value: the integer to render.

    Notes:
        - A negative value keeps its sign in front of the prefix, e.g. -255
          renders as ``-0xff``, not a two's-complement bit pattern.

    Yields:
        The hex string. INVALID when the child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Hex(255))[0]
        '0xff'
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return hex(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return hex(v)

        return athunk


class Oct(ScalarQuery):
    """The octal string (``0o...``) of its one integer child.

    Args:
        value: the integer to render.

    Notes:
        - A negative value keeps its sign in front of the prefix, e.g. -8
          renders as ``-0o10``, not a two's-complement bit pattern.

    Yields:
        The octal string. INVALID when the child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Oct(8))[0]
        '0o10'
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return oct(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return oct(v)

        return athunk


class Ord(ScalarQuery):
    """The Unicode code point of its one single-character child.

    Args:
        value: a string of exactly one character.

    Notes:
        - A string of any other length raises: this is not a bulk operation.

    Yields:
        The code point, an int. INVALID when the child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Ord("A"))[0]
        65
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return ord(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return ord(v)

        return athunk


class Chr(ScalarQuery):
    """The character for its one integer code-point child.

    Args:
        value: the code point, 0 through 0x10FFFF.

    Notes:
        - Always yields a one-character string, never a raw byte or int.

    Yields:
        The character. INVALID when the child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Chr(65))[0]
        'A'
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return chr(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return chr(v)

        return athunk
