"""Representation atoms: Python's string and number renderings.

Maps Python's builtins that render a value to text or to an alternate numeric
notation onto Nu ScalarQueries. Pure compute; no Context effect of their own.

Builtins to cover (Python -> Nu):
- text: ``repr`` -> ``ReprQuery``, ``ascii`` -> ``AsciiQuery``, ``format`` -> ``FormatQuery``
- numeric notation: ``bin`` -> ``BinQuery``, ``hex`` -> ``HexQuery``, ``oct`` -> ``OctQuery``
- code points: ``ord`` -> ``OrdQuery``, ``chr`` -> ``ChrQuery``

Sorts: all ScalarQuery (Q).

Each atom defines ``compile`` (sync hot path) and ``acompile`` (async hot
path). Both return a thunk ``(rt) -> value`` that captures the precompiled
child thunks, so recursion skips the ``Runtime.eval`` / ``Runtime.aeval``
dispatch hop per child. Sentinel propagation is inlined: an EMPTY or INVALID
operand collapses the result to INVALID without further compute.

Most atoms are unary over one child. ``FormatQuery`` mirrors Python's
``format(value[, format_spec])`` and branches on child count: one child
applies the empty format spec, two children apply the second child as the
spec.

The module name ``repr`` shadows the builtin name as a module path
(``nu2.core.repr``); inside the module the builtin ``repr()`` still resolves
normally.

v1 reference: partly ``src/nu/queries/conversion.py``; most of these have no
v1 atom yet, so they are built fresh against the builtins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.lang import ScalarQuery
from nu2.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.runtime import Runtime

__all__ = [
    "AsciiQuery",
    "BinQuery",
    "ChrQuery",
    "FormatQuery",
    "HexQuery",
    "OctQuery",
    "OrdQuery",
    "ReprQuery",
]


class ReprQuery(ScalarQuery):
    """The ``repr`` string of its one child."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return repr(v)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return repr(v)

        return athunk


class AsciiQuery(ScalarQuery):
    """The ``ascii`` string of its one child (non-ASCII escaped)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return ascii(v)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return ascii(v)

        return athunk


class FormatQuery(ScalarQuery):
    """The ``format`` of a value under an optional format spec.

    One child applies the empty spec (``format(value)``); two children apply
    the second child as the format spec (``format(value, spec)``).
    """

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class BinQuery(ScalarQuery):
    """The binary string (``0b...``) of its one integer child."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return bin(v)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return bin(v)

        return athunk


class HexQuery(ScalarQuery):
    """The hexadecimal string (``0x...``) of its one integer child."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return hex(v)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return hex(v)

        return athunk


class OctQuery(ScalarQuery):
    """The octal string (``0o...``) of its one integer child."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return oct(v)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return oct(v)

        return athunk


class OrdQuery(ScalarQuery):
    """The Unicode code point of its one single-character child."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return ord(v)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return ord(v)

        return athunk


class ChrQuery(ScalarQuery):
    """The character for its one integer code-point child."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return chr(v)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return chr(v)

        return athunk
