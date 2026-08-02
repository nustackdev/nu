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
    """The ``repr`` string of its one child."""

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
    """The ``ascii`` string of its one child (non-ASCII escaped)."""

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

    One child applies the empty spec (``format(value)``); two children apply
    the second child as the format spec (``format(value, spec)``).
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
    """The binary string (``0b...``) of its one integer child."""

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
    """The hexadecimal string (``0x...``) of its one integer child."""

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
    """The octal string (``0o...``) of its one integer child."""

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
    """The Unicode code point of its one single-character child."""

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
    """The character for its one integer code-point child."""

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
