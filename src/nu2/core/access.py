"""Access atoms: Python's item and attribute access.

Maps Python's member-access builtins and operators onto Nu. This file crosses
sorts on purpose: reads are Queries, writes/deletes are Commands - they belong
together as one domain (accessing a value's members), not split by sort.

Builtins / operators to cover (Python -> Nu):
- items (read, Q): ``x[k]`` -> ``GetItem``, ``len`` -> ``Len``,
  ``in`` -> ``Contains``, ``slice`` / ``x[a:b]`` -> ``Slice``
- items (write, C): ``x[k] = v`` -> ``SetItem``, ``del x[k]`` -> ``DelItem``
- attrs (read, Q): ``getattr`` -> ``GetAttr``, ``hasattr`` -> ``HasAttr``
- attrs (write, C): ``setattr`` -> ``SetAttr``, ``delattr`` -> ``DelAttr``

Sorts: ScalarQuery (Q) for the reads, Command (C) for the writes/deletes. A
mutating access whose target is a Ref is a WRITE; off a non-Ref it is local. If
a remove-and-return variant is wanted (pop-style), that is an Action - note it
but the builtins here are plain get/set/del.

The reads are EVALUABLE: each defines ``compile`` (sync hot path) and
``acompile`` (async hot path) returning a thunk that computes from its child
values, with inlined EMPTY / INVALID sentinel propagation (mirroring
``nu2.core.arithmetic``). The writes are STRUCTURAL only: they subclass Command
and declare ``mutates`` (slot 0 is the target Ref), with no ``compile`` - their
runtime lands once the fabric write path is wired.

v1 reference: ``src/nu/queries/access.py`` (Len, At, Slice, Contains) and
``src/nu/queries/attr.py`` (GetAttr, SetAttr, DelAttr).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine.structure import Declared
from nu2.lang import Command, ScalarQuery
from nu2.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.runtime import Runtime

__all__ = [
    "Contains",
    "DelAttr",
    "DelItem",
    "GetAttr",
    "GetItem",
    "HasAttr",
    "Len",
    "SetAttr",
    "SetItem",
    "Slice",
]


# --- reads (ScalarQuery, evaluable) --------------------------------------


class GetItem(ScalarQuery):
    """Subscript access: ``x[k]`` for child 0 indexed by child 1."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target, key = children

        def thunk(rt: Runtime) -> object:
            x = target(rt)
            if x is EMPTY or x is INVALID:
                return INVALID
            k = key(rt)
            if k is EMPTY or k is INVALID:
                return INVALID
            return x[k]

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target, key = children

        async def athunk(rt: Runtime) -> object:
            x = await target(rt)
            if x is EMPTY or x is INVALID:
                return INVALID
            k = await key(rt)
            if k is EMPTY or k is INVALID:
                return INVALID
            return x[k]

        return athunk


class Len(ScalarQuery):
    """Length: ``len(x)`` of its one child."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return len(v)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return len(v)

        return athunk


class Contains(ScalarQuery):
    """Containment: ``item in container`` for child 1 in child 0."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        container, item = children

        def thunk(rt: Runtime) -> object:
            c = container(rt)
            if c is EMPTY or c is INVALID:
                return INVALID
            x = item(rt)
            if x is EMPTY or x is INVALID:
                return INVALID
            return x in c

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        container, item = children

        async def athunk(rt: Runtime) -> object:
            c = await container(rt)
            if c is EMPTY or c is INVALID:
                return INVALID
            x = await item(rt)
            if x is EMPTY or x is INVALID:
                return INVALID
            return x in c

        return athunk


class Slice(ScalarQuery):
    """The ``slice(...)`` builtin: builds a slice object from its children.

    Children are ``start, stop, step`` (mirroring ``slice(start, stop, step)``).
    Used to drive subscript access like ``x[a:b:c]`` as ``GetItem(x, Slice(...))``.
    """

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        start, stop, step = children

        def thunk(rt: Runtime) -> object:
            a = start(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = stop(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            c = step(rt)
            if c is EMPTY or c is INVALID:
                return INVALID
            return slice(a, b, c)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        start, stop, step = children

        async def athunk(rt: Runtime) -> object:
            a = await start(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await stop(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            c = await step(rt)
            if c is EMPTY or c is INVALID:
                return INVALID
            return slice(a, b, c)

        return athunk


class GetAttr(ScalarQuery):
    """Attribute read: ``getattr(obj, name[, default])``.

    Child 0 is the object, child 1 the attribute name. An optional child 2
    supplies the default returned when the attribute is absent (matching the
    three-arg ``getattr`` builtin).
    """

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        obj_t = children[0]
        name_t = children[1]
        default_t = children[2] if len(children) > 2 else None

        def thunk(rt: Runtime) -> object:
            obj = obj_t(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            name = name_t(rt)
            if name is EMPTY or name is INVALID:
                return INVALID
            if default_t is not None:
                default = default_t(rt)
                if default is EMPTY or default is INVALID:
                    return INVALID
                return getattr(obj, str(name), default)
            return getattr(obj, str(name))

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        obj_t = children[0]
        name_t = children[1]
        default_t = children[2] if len(children) > 2 else None

        async def athunk(rt: Runtime) -> object:
            obj = await obj_t(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            name = await name_t(rt)
            if name is EMPTY or name is INVALID:
                return INVALID
            if default_t is not None:
                default = await default_t(rt)
                if default is EMPTY or default is INVALID:
                    return INVALID
                return getattr(obj, str(name), default)
            return getattr(obj, str(name))

        return athunk


class HasAttr(ScalarQuery):
    """Attribute presence: ``hasattr(obj, name)`` for child 0 and child 1."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        obj_t, name_t = children

        def thunk(rt: Runtime) -> object:
            obj = obj_t(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            name = name_t(rt)
            if name is EMPTY or name is INVALID:
                return INVALID
            return hasattr(obj, str(name))

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        obj_t, name_t = children

        async def athunk(rt: Runtime) -> object:
            obj = await obj_t(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            name = await name_t(rt)
            if name is EMPTY or name is INVALID:
                return INVALID
            return hasattr(obj, str(name))

        return athunk


# --- writes (Command, structural) ----------------------------------------


class SetItem(Command):
    """Subscript write: ``x[k] = v``. Writes into the Ref in slot 0.

    Slots: 0 target Ref, 1 key, 2 value. Runtime lands with the fabric write
    path; this declares the effect shape only.
    """

    mutates = Declared(value=frozenset({0}))


class DelItem(Command):
    """Subscript delete: ``del x[k]``. Writes into the Ref in slot 0.

    Slots: 0 target Ref, 1 key. Runtime lands with the fabric write path.
    """

    mutates = Declared(value=frozenset({0}))


class SetAttr(Command):
    """Attribute write: ``setattr(obj, name, value)``. Writes the Ref in slot 0.

    Slots: 0 target Ref, 1 name, 2 value. Runtime lands with the fabric write
    path.
    """

    mutates = Declared(value=frozenset({0}))


class DelAttr(Command):
    """Attribute delete: ``delattr(obj, name)``. Writes the Ref in slot 0.

    Slots: 0 target Ref, 1 name. Runtime lands with the fabric write path.
    """

    mutates = Declared(value=frozenset({0}))
