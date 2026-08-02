"""Reflection atoms: Python's introspection builtins.

Maps Python's builtins that inspect a value's type, identity, or shape onto Nu
ScalarQueries. Pure compute; no Context effect of their own.

Builtins covered (Python -> Nu):
- type / class: ``type`` -> ``Type``, ``isinstance`` -> ``IsInstance``,
  ``issubclass`` -> ``IsSubclass``, ``callable`` -> ``Callable``
- identity / value: ``id`` -> ``Id``, ``hash`` -> ``Hash``
- namespace: ``dir`` -> ``Dir``, ``vars`` -> ``Vars``

Sorts: all ScalarQuery (Q). ``Type`` / ``Callable`` / ``Id`` / ``Hash`` /
``Dir`` / ``Vars`` are unary; ``IsInstance`` / ``IsSubclass`` are binary (value,
class). ``Dir`` / ``Vars`` yield a collection but are scalar builders (one list /
dict), not streams.

Each atom defines ``compile`` (sync hot path) and ``acompile`` (async hot path).
Both return a thunk ``(rt) -> value`` (sync) or ``(rt) -> awaitable`` (async)
that captures the precompiled child thunks, so recursion skips the
``Runtime.eval`` / ``Runtime.aeval`` dispatch hop per child. Sentinel
propagation is inlined: an EMPTY or INVALID operand collapses the result to
INVALID without inspecting.

OOP descriptors (``super``, ``object``, ``property``, ``classmethod``,
``staticmethod``, ``memoryview``) are NOT in this pass - they go to extensions
later, once the OOP descriptor surface is designed.

These are built fresh against the builtins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable as PyCallable

    from nu.lang.runtime import Runtime

__all__ = [
    "Callable",
    "Dir",
    "Hash",
    "Id",
    "IsInstance",
    "IsSubclass",
    "Type",
    "Vars",
]


class Type(ScalarQuery):
    """The type of its one child (``type``)."""

    def _compile(self, nid: int, children: tuple[PyCallable, ...]) -> PyCallable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return type(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[PyCallable, ...]) -> PyCallable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return type(v)

        return athunk


class IsInstance(ScalarQuery):
    """Whether the first child is an instance of the second (``isinstance``)."""

    def _compile(self, nid: int, children: tuple[PyCallable, ...]) -> PyCallable:
        value, klass = children

        def thunk(rt: Runtime) -> object:
            v = value(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            k = klass(rt)
            if k is EMPTY or k is INVALID:
                return INVALID
            return isinstance(v, k)

        return thunk

    def _acompile(self, nid: int, children: tuple[PyCallable, ...]) -> PyCallable:
        value, klass = children

        async def athunk(rt: Runtime) -> object:
            v = await value(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            k = await klass(rt)
            if k is EMPTY or k is INVALID:
                return INVALID
            return isinstance(v, k)

        return athunk


class IsSubclass(ScalarQuery):
    """Whether the first child is a subclass of the second (``issubclass``)."""

    def _compile(self, nid: int, children: tuple[PyCallable, ...]) -> PyCallable:
        cls, klass = children

        def thunk(rt: Runtime) -> object:
            c = cls(rt)
            if c is EMPTY or c is INVALID:
                return INVALID
            k = klass(rt)
            if k is EMPTY or k is INVALID:
                return INVALID
            return issubclass(c, k)

        return thunk

    def _acompile(self, nid: int, children: tuple[PyCallable, ...]) -> PyCallable:
        cls, klass = children

        async def athunk(rt: Runtime) -> object:
            c = await cls(rt)
            if c is EMPTY or c is INVALID:
                return INVALID
            k = await klass(rt)
            if k is EMPTY or k is INVALID:
                return INVALID
            return issubclass(c, k)

        return athunk


class Callable(ScalarQuery):
    """Whether its one child appears callable (``callable``)."""

    def _compile(self, nid: int, children: tuple[PyCallable, ...]) -> PyCallable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return callable(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[PyCallable, ...]) -> PyCallable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return callable(v)

        return athunk


class Id(ScalarQuery):
    """The identity of its one child (``id``)."""

    def _compile(self, nid: int, children: tuple[PyCallable, ...]) -> PyCallable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return id(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[PyCallable, ...]) -> PyCallable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return id(v)

        return athunk


class Hash(ScalarQuery):
    """The hash of its one child (``hash``)."""

    def _compile(self, nid: int, children: tuple[PyCallable, ...]) -> PyCallable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return hash(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[PyCallable, ...]) -> PyCallable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return hash(v)

        return athunk


class Dir(ScalarQuery):
    """The sorted attribute-name list of its one child (``dir``)."""

    def _compile(self, nid: int, children: tuple[PyCallable, ...]) -> PyCallable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return dir(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[PyCallable, ...]) -> PyCallable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return dir(v)

        return athunk


class Vars(ScalarQuery):
    """The ``__dict__`` of its one child (``vars``)."""

    def _compile(self, nid: int, children: tuple[PyCallable, ...]) -> PyCallable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return vars(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[PyCallable, ...]) -> PyCallable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return vars(v)

        return athunk
