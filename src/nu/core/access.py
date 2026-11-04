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
values, with no NULL handling: NULL's own interface decides.
The writes apply Python's ``x[k]=v`` / ``setattr`` / ``del`` to the object
value and return that object so they compose; a NULL operand to a write
raises. If a remove-and-return variant is wanted (pop-style), that is an Action - note it,
but the builtins here are plain get/set/del.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Command, ScalarQuery
from nu.lang.null import is_null


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
    """Subscript access: ``x[k]``.

    Args:
        target: the object to index.
        key: the index or key to look up.

    Notes:
        - A missing key or out-of-range index raises Python's own
          ``KeyError`` / ``IndexError``, as in Python.

    Yields:
        The member at that key.

    Example:
        >>> nu.run(nu.GetItem(nu.Literal([10, 20, 30]), nu.Literal(1)))[0]
        20
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target, key = children

        def thunk(rt: Runtime) -> object:
            x = target(rt)
            k = key(rt)
            return x[k]

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target, key = children

        async def athunk(rt: Runtime) -> object:
            x = await target(rt)
            k = await key(rt)
            return x[k]

        return athunk


class Len(ScalarQuery):
    """Length: ``len(x)`` of its one child.

    Args:
        value: the object to measure.

    Yields:
        The length.

    Example:
        >>> nu.run(nu.Len(nu.Literal("abcd")))[0]
        4
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            return len(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            return len(v)

        return athunk


class Contains(ScalarQuery):
    """Containment: ``item in container``.

    Args:
        container: the object to search.
        item: the value to look for.

    Yields:
        True or False.

    Example:
        >>> nu.run(nu.Contains(nu.Literal([1, 2, 3]), nu.Literal(9)))[0]
        False
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        container, item = children

        def thunk(rt: Runtime) -> object:
            c = container(rt)
            x = item(rt)
            return x in c

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        container, item = children

        async def athunk(rt: Runtime) -> object:
            c = await container(rt)
            x = await item(rt)
            return x in c

        return athunk


class Slice(ScalarQuery):
    """The ``slice(...)`` builtin: builds a slice object.

    Args:
        start: the start index, or None for the beginning.
        stop: the stop index, or None for the end.
        step: the step, or None for 1.

    Yields:
        A ``slice`` object.

    Example:
        >>> nu.run(nu.Slice(nu.Literal(1), nu.Literal(3), nu.Literal(None)))[0]
        slice(1, 3, None)
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        start, stop, step = children

        def thunk(rt: Runtime) -> object:
            a = start(rt)
            b = stop(rt)
            c = step(rt)
            return slice(a, b, c)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        start, stop, step = children

        async def athunk(rt: Runtime) -> object:
            a = await start(rt)
            b = await stop(rt)
            c = await step(rt)
            return slice(a, b, c)

        return athunk


class GetAttr(ScalarQuery):
    """Attribute read: ``getattr(obj, name[, default])``.

    Args:
        obj: the object to read from.
        name: the attribute name.
        default: value to return when the attribute is absent. Optional:
            leave the child out entirely to let a missing attribute raise.

    Notes:
        - Without a default child, a missing attribute raises Python's own
          ``AttributeError``, as in Python.

    Yields:
        The attribute value.

    Example:
        >>> nu.run(nu.GetAttr(nu.Literal(1j), nu.Literal("imag")))[0]
        1.0
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        obj_t = children[0]
        name_t = children[1]
        default_t = children[2] if len(children) > 2 else None

        def thunk(rt: Runtime) -> object:
            obj = obj_t(rt)
            name = name_t(rt)
            if default_t is not None:
                default = default_t(rt)
                return getattr(obj, str(name), default)
            return getattr(obj, str(name))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        obj_t = children[0]
        name_t = children[1]
        default_t = children[2] if len(children) > 2 else None

        async def athunk(rt: Runtime) -> object:
            obj = await obj_t(rt)
            name = await name_t(rt)
            if default_t is not None:
                default = await default_t(rt)
                return getattr(obj, str(name), default)
            return getattr(obj, str(name))

        return athunk


class HasAttr(ScalarQuery):
    """Attribute presence: ``hasattr(obj, name)``.

    Args:
        obj: the object to check.
        name: the attribute name.

    Yields:
        True or False.

    Example:
        >>> nu.run(nu.HasAttr(nu.Literal(1j), nu.Literal("imag")))[0]
        True
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        obj_t, name_t = children

        def thunk(rt: Runtime) -> object:
            obj = obj_t(rt)
            name = name_t(rt)
            return hasattr(obj, str(name))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        obj_t, name_t = children

        async def athunk(rt: Runtime) -> object:
            obj = await obj_t(rt)
            name = await name_t(rt)
            return hasattr(obj, str(name))

        return athunk


# --- writes (ScalarQuery, local Python mutation) -------------------------


class SetItem(Command):
    """Subscript write: ``x[k] = v``.

    Args:
        target: the container to mutate. Slot 0, so it must hold a Ref.
        key: the index or key to write to.
        value: the value to store.

    Notes:
        - Mutates the container in place and yields nothing, matching
          Python's ``x[k] = v``.

    Yields:
        Nothing.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target, key, value = children

        def thunk(rt: Runtime) -> None:
            x = target(rt)
            if is_null(x):
                raise ValueError("cannot write with a NULL operand")
            k = key(rt)
            if is_null(k):
                raise ValueError("cannot write with a NULL operand")
            v = value(rt)
            if is_null(v):
                raise ValueError("cannot write with a NULL operand")
            x[k] = v

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target, key, value = children

        async def athunk(rt: Runtime) -> None:
            x = await target(rt)
            if is_null(x):
                raise ValueError("cannot write with a NULL operand")
            k = await key(rt)
            if is_null(k):
                raise ValueError("cannot write with a NULL operand")
            v = await value(rt)
            if is_null(v):
                raise ValueError("cannot write with a NULL operand")
            x[k] = v

        return athunk


class DelItem(Command):
    """Subscript delete: ``del x[k]``.

    Args:
        target: the container to mutate. Slot 0, so it must hold a Ref.
        key: the index or key to remove.

    Notes:
        - Mutates the container in place and yields nothing.
        - A missing key raises Python's own ``KeyError`` / ``IndexError``,
          it does not bail silently.

    Yields:
        Nothing.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target, key = children

        def thunk(rt: Runtime) -> None:
            x = target(rt)
            if is_null(x):
                raise ValueError("cannot write with a NULL operand")
            k = key(rt)
            if is_null(k):
                raise ValueError("cannot write with a NULL operand")
            del x[k]

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target, key = children

        async def athunk(rt: Runtime) -> None:
            x = await target(rt)
            if is_null(x):
                raise ValueError("cannot write with a NULL operand")
            k = await key(rt)
            if is_null(k):
                raise ValueError("cannot write with a NULL operand")
            del x[k]

        return athunk


class SetAttr(Command):
    """Attribute write: ``setattr(obj, name, value)``.

    Args:
        obj: the object to mutate. Slot 0, so it must hold a Ref.
        name: the attribute name.
        value: the value to store.

    Notes:
        - Mutates the object in place and yields nothing, matching Python's
          ``setattr``.

    Yields:
        Nothing.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        obj_t, name_t, value_t = children

        def thunk(rt: Runtime) -> None:
            obj = obj_t(rt)
            if is_null(obj):
                raise ValueError("cannot write with a NULL operand")
            name = name_t(rt)
            if is_null(name):
                raise ValueError("cannot write with a NULL operand")
            value = value_t(rt)
            if is_null(value):
                raise ValueError("cannot write with a NULL operand")
            setattr(obj, str(name), value)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        obj_t, name_t, value_t = children

        async def athunk(rt: Runtime) -> None:
            obj = await obj_t(rt)
            if is_null(obj):
                raise ValueError("cannot write with a NULL operand")
            name = await name_t(rt)
            if is_null(name):
                raise ValueError("cannot write with a NULL operand")
            value = await value_t(rt)
            if is_null(value):
                raise ValueError("cannot write with a NULL operand")
            setattr(obj, str(name), value)

        return athunk


class DelAttr(Command):
    """Attribute delete: ``delattr(obj, name)``.

    Args:
        obj: the object to mutate. Slot 0, so it must hold a Ref.
        name: the attribute name to remove.

    Notes:
        - Mutates the object in place and yields nothing.
        - A missing attribute raises Python's own ``AttributeError``, it
          does not bail silently.

    Yields:
        Nothing.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        obj_t, name_t = children

        def thunk(rt: Runtime) -> None:
            obj = obj_t(rt)
            if is_null(obj):
                raise ValueError("cannot write with a NULL operand")
            name = name_t(rt)
            if is_null(name):
                raise ValueError("cannot write with a NULL operand")
            delattr(obj, str(name))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        obj_t, name_t = children

        async def athunk(rt: Runtime) -> None:
            obj = await obj_t(rt)
            if is_null(obj):
                raise ValueError("cannot write with a NULL operand")
            name = await name_t(rt)
            if is_null(name):
                raise ValueError("cannot write with a NULL operand")
            delattr(obj, str(name))

        return athunk
