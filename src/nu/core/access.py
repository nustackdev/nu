"""Access atoms: Python's item and attribute management.

Maps Python's member-access builtins and operators onto Nu - getting, setting,
and deleting an item or attribute of a plain Python value. Every atom here is a
``ScalarQuery``: a read yields the member, a write/delete mutates the value
in-place and yields it back. This is local Python mutation off a value, not a
fabric write - writing into a Ref's fabric location is the fabric's own
interaction (``context.Set`` / ``context.Delete`` and the like), which lives in
the fabric dirs, never here. ``core`` is the pure Python builtins.

Builtins / operators to cover (Python -> Nu):
- items (read): ``x[k]`` -> ``GetItem``, ``len`` -> ``Len``,
  ``in`` -> ``Contains``, ``slice`` / ``x[a:b]`` -> ``Slice``
- items (write): ``x[k] = v`` -> ``SetItem``, ``del x[k]`` -> ``DelItem``
- attrs (read): ``getattr`` -> ``GetAttr``, ``hasattr`` -> ``HasAttr``
- attrs (write): ``setattr`` -> ``SetAttr``, ``delattr`` -> ``DelAttr``

Every atom is EVALUABLE: each defines ``compile`` (sync hot path) and
``acompile`` (async hot path) returning a thunk that computes from its child
values, with inlined EMPTY / INVALID sentinel propagation (mirroring
``nu.core.arithmetic``). The writes apply Python's ``x[k]=v`` / ``setattr`` /
``del`` to the object value and return that object so they compose. If a
remove-and-return variant is wanted (pop-style), that is an Action - note it,
but the builtins here are plain get/set/del.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Command, ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

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

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return len(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return len(v)

        return athunk


class Contains(ScalarQuery):
    """Containment: ``item in container`` for child 1 in child 0."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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


# --- writes (ScalarQuery, local Python mutation) -------------------------


class SetItem(Command):
    """Subscript write: ``x[k] = v`` for child 0 keyed by child 1.

    Slots: 0 container, 1 key, 2 value. Mutates the container in place; returns
    nothing, matching Python's ``x[k] = v``.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target, key, value = children

        def thunk(rt: Runtime) -> None:
            x = target(rt)
            if x is EMPTY or x is INVALID:
                return
            k = key(rt)
            if k is EMPTY or k is INVALID:
                return
            v = value(rt)
            if v is EMPTY or v is INVALID:
                return
            x[k] = v

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target, key, value = children

        async def athunk(rt: Runtime) -> None:
            x = await target(rt)
            if x is EMPTY or x is INVALID:
                return
            k = await key(rt)
            if k is EMPTY or k is INVALID:
                return
            v = await value(rt)
            if v is EMPTY or v is INVALID:
                return
            x[k] = v

        return athunk


class DelItem(Command):
    """Subscript delete: ``del x[k]`` for child 0 keyed by child 1.

    Slots: 0 container, 1 key. Mutates the container in place; returns nothing.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target, key = children

        def thunk(rt: Runtime) -> None:
            x = target(rt)
            if x is EMPTY or x is INVALID:
                return
            k = key(rt)
            if k is EMPTY or k is INVALID:
                return
            del x[k]

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target, key = children

        async def athunk(rt: Runtime) -> None:
            x = await target(rt)
            if x is EMPTY or x is INVALID:
                return
            k = await key(rt)
            if k is EMPTY or k is INVALID:
                return
            del x[k]

        return athunk


class SetAttr(Command):
    """Attribute write: ``setattr(obj, name, value)``.

    Slots: 0 object, 1 name, 2 value. Mutates the object in place; returns
    nothing, matching Python's ``setattr``.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        obj_t, name_t, value_t = children

        def thunk(rt: Runtime) -> None:
            obj = obj_t(rt)
            if obj is EMPTY or obj is INVALID:
                return
            name = name_t(rt)
            if name is EMPTY or name is INVALID:
                return
            value = value_t(rt)
            if value is EMPTY or value is INVALID:
                return
            setattr(obj, str(name), value)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        obj_t, name_t, value_t = children

        async def athunk(rt: Runtime) -> None:
            obj = await obj_t(rt)
            if obj is EMPTY or obj is INVALID:
                return
            name = await name_t(rt)
            if name is EMPTY or name is INVALID:
                return
            value = await value_t(rt)
            if value is EMPTY or value is INVALID:
                return
            setattr(obj, str(name), value)

        return athunk


class DelAttr(Command):
    """Attribute delete: ``delattr(obj, name)``.

    Slots: 0 object, 1 name. Mutates the object in place; returns nothing.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        obj_t, name_t = children

        def thunk(rt: Runtime) -> None:
            obj = obj_t(rt)
            if obj is EMPTY or obj is INVALID:
                return
            name = name_t(rt)
            if name is EMPTY or name is INVALID:
                return
            delattr(obj, str(name))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        obj_t, name_t = children

        async def athunk(rt: Runtime) -> None:
            obj = await obj_t(rt)
            if obj is EMPTY or obj is INVALID:
                return
            name = await name_t(rt)
            if name is EMPTY or name is INVALID:
                return
            delattr(obj, str(name))

        return athunk
