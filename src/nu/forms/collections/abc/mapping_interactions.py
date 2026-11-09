"""Mapping interactions.

Reads (Query): Keys, KeysPage, Values, Items, Get, ContainsKey,
    Copy, ReversedKeysPage, Merge
Streams (StreamQuery): ReversedKeys, ReversedValues, ReversedItems
Mutate, yield nothing (Command): DeleteItem, Update (SetItem lives in nu.core.access)
Mutate and yield a value (Action): DictPop, PopItem, SetDefault,
    MergeUpdate
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from nu.engine.structure import Declared
from nu.factory.host import host
from nu.lang import Command, ScalarAction, ScalarQuery, StreamQuery
from nu.lang.null import is_null
from nu.lang.sentinels import UNSET

from .paged_mapping import PagedMapping


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator

    from nu.lang.runtime import Runtime


__all__ = [
    "ContainsKey",
    "Copy",
    "DeleteItem",
    "DictCreate",
    "DictOf",
    "DictPop",
    "Get",
    "Items",
    "Keys",
    "KeysPage",
    "Merge",
    "MergeUpdate",
    "PopItem",
    "ReversedItems",
    "ReversedKeys",
    "ReversedKeysPage",
    "ReversedValues",
    "SetDefault",
    "Update",
    "Values",
]


# =============================================================================
# MAPPING CONSTRUCTORS
# =============================================================================

# Empty dict: deterministic (always {}), but each eval must yield a *fresh*
# mutable object - a future fold/CSE pass must not alias two DictCreate results.
DictCreate = host(dict, name="DictCreate")
# Dict from named fields: DictOf(a=x, b=y) evaluates each field expression and
# zips names back into a fresh dict.
DictOf = host(dict, name="DictOf")


# =============================================================================
# MAPPING READS (Query)
# =============================================================================


class Keys(ScalarQuery):
    """Get keys view from mapping: mapping.keys()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            obj = operand(rt)
            return obj.keys()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            obj = await operand(rt)
            return obj.keys()

        return athunk


def _page_args(op: str, cursor: str, at: object, limit: object) -> tuple[object, int | None]:
    """Refuse a NULL cursor or limit: a page past nothing is not an empty page."""
    if is_null(at):
        raise ValueError(f"{op}({cursor}=) read NULL: branch on it first (IsNull)")
    if is_null(limit):
        raise ValueError(f"{op}(limit=) read NULL: branch on it first (IsNull)")
    return at, cast("int | None", limit)


def _paged(obj: object, op: str) -> PagedMapping:
    """``obj`` as the :class:`PagedMapping` it must be to hand out a page of keys."""
    if not isinstance(obj, PagedMapping):
        msg = (
            f"{op}(...) pages: {type(obj).__name__} is not a PagedMapping. "
            f"A plain dict has no paged keys; a fabric registers its paging mappings"
        )
        raise TypeError(msg)
    return obj


class KeysPage(ScalarQuery):
    """One page of keys: list(mapping.keys(after=after, limit=limit)).

    Calls the mapping's own paged ``keys`` and collects the page into a list.
    A mapping that is no :class:`PagedMapping` raises TypeError (Python's
    ``dict.keys`` takes no arguments). ``after`` and ``limit`` reach it as
    they read; one that reads NULL raises ValueError before the mapping is
    called.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        operand, after_t, limit_t = children

        def thunk(rt: Runtime) -> object:
            obj = _paged(operand(rt), "keys")
            after, limit = _page_args("keys", "after", after_t(rt), limit_t(rt))
            return list(obj.keys(after=after, limit=limit))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        operand, after_t, limit_t = children

        async def athunk(rt: Runtime) -> object:
            obj = _paged(await operand(rt), "keys")
            after, limit = _page_args("keys", "after", await after_t(rt), await limit_t(rt))
            return list(obj.keys(after=after, limit=limit))

        return athunk


class Values(ScalarQuery):
    """Get values view from mapping: mapping.values()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            obj = operand(rt)
            return obj.values()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            obj = await operand(rt)
            return obj.values()

        return athunk


class Items(ScalarQuery):
    """Get items view from mapping: mapping.items()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            obj = operand(rt)
            return obj.items()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            obj = await operand(rt)
            return obj.items()

        return athunk


class Get(ScalarQuery):
    """Value at a key: ``mapping[key]``, or ``mapping.get(key, default)`` when a default is given.

    Children are ``(mapping, key)`` or ``(mapping, key, default)``. A default,
    NULL and None included, is forwarded to the mapping's own ``get``, which
    decides when it applies; with none, a missing key raises as ``[]`` does.
    """

    def __init__(self, mapping: object, key: object, default: object = UNSET) -> None:
        if default is UNSET:
            super().__init__(mapping, key)
        else:
            super().__init__(mapping, key, default)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t, *rest = children
        c_t = rest[0] if rest else None

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            b = b_t(rt)
            if c_t is None:
                return a[b]
            return a.get(b, c_t(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t, *rest = children
        c_t = rest[0] if rest else None

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            b = await b_t(rt)
            if c_t is None:
                return a[b]
            return a.get(b, await c_t(rt))

        return athunk


class ContainsKey(ScalarQuery):
    """Test key membership: key in mapping. Yields a bool."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, key_t = children

        def thunk(rt: Runtime) -> object:
            target = target_t(rt)
            key = key_t(rt)
            return key in target

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, key_t = children

        async def athunk(rt: Runtime) -> object:
            target = await target_t(rt)
            key = await key_t(rt)
            return key in target

        return athunk


class Copy(ScalarQuery):
    """Shallow copy of the mapping: mapping.copy(). Yields a new dict."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            obj = operand(rt)
            return obj.copy()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            obj = await operand(rt)
            return obj.copy()

        return athunk


class ReversedKeys(StreamQuery):
    """Keys last first, as a stream: reversed(mapping).

    The thunk returns ``reversed(obj)``, the mapping's own reverse walk, so a
    consumer pulling ``n`` keys reads only ``n``. The async twin yields the
    same walk as an async stream.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            return reversed(operand(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            return _astream(reversed(await operand(rt)))

        return athunk


class ReversedKeysPage(ScalarQuery):
    """One page of keys, last first: list(mapping.reversed_keys(before=before, limit=limit)).

    The reverse twin of :class:`KeysPage`: calls the mapping's own paged
    ``reversed_keys`` and collects the page into a list. A mapping that is no
    :class:`PagedMapping` raises TypeError, and so does a ``before`` or
    ``limit`` that reads NULL (ValueError).
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        operand, before_t, limit_t = children

        def thunk(rt: Runtime) -> object:
            obj = _paged(operand(rt), "reversed_keys")
            before, limit = _page_args("reversed_keys", "before", before_t(rt), limit_t(rt))
            return list(obj.reversed_keys(before=before, limit=limit))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        operand, before_t, limit_t = children

        async def athunk(rt: Runtime) -> object:
            obj = _paged(await operand(rt), "reversed_keys")
            before, limit = _page_args(
                "reversed_keys", "before", await before_t(rt), await limit_t(rt)
            )
            return list(obj.reversed_keys(before=before, limit=limit))

        return athunk


class ReversedValues(StreamQuery):
    """Values last first, as a stream: reversed(mapping.values()).

    Lazy like :class:`ReversedKeys`: the mapping's own reverse walk over its
    values. Works for Python ``dict`` and any mapping whose ``.values()`` is
    reversible.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            return reversed(operand(rt).values())

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            return _astream(reversed((await operand(rt)).values()))

        return athunk


class ReversedItems(StreamQuery):
    """``(key, value)`` pairs last first, as a stream: reversed(mapping.items()).

    Lazy like :class:`ReversedKeys`. Works for Python ``dict`` and any
    mapping whose ``.items()`` is reversible.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            return reversed(operand(rt).items())

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            return _astream(reversed((await operand(rt)).items()))

        return athunk


async def _astream(items: Iterator) -> AsyncIterator:
    """A sync walk as the async stream an async stream thunk returns."""
    for item in items:
        yield item


class Merge(ScalarQuery):
    """Merge two mappings into a new one: mapping | other. Yields a new dict."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            b = b_t(rt)
            return a | b

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            b = await b_t(rt)
            return a | b

        return athunk


# =============================================================================
# MAPPING MUTATIONS, YIELD NOTHING (Command)
# =============================================================================


class DeleteItem(Command):
    """Delete entry by key: del mapping[key]. Mutates slot 0; returns nothing.

    An absent key raises whatever the mapping's own ``del`` raises. With the
    construction-time ``missing_ok`` flag (carried in the payload) set, a
    ``KeyError`` from that ``del`` is a no-op.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")
    _creates = Declared(value=frozenset(), name="creates")
    """Acts on an absent container as on an empty one, and leaves it absent."""

    def __init__(self, target: object, key: object, *, missing_ok: bool = False) -> None:
        super().__init__(target, key)
        self._payload = {**self._payload, "missing_ok": missing_ok}

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, key_t = children
        missing_ok = bool(self._payload["missing_ok"])

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            key = key_t(rt)
            if is_null(key):
                raise ValueError("cannot write with a NULL operand")
            try:
                del target[key]
            except KeyError:
                if not missing_ok:
                    raise

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, key_t = children
        missing_ok = bool(self._payload["missing_ok"])

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            key = await key_t(rt)
            if is_null(key):
                raise ValueError("cannot write with a NULL operand")
            try:
                del target[key]
            except KeyError:
                if not missing_ok:
                    raise

        return athunk


class Update(Command):
    """Update mapping with another: mapping.update(other). Mutates slot 0; returns nothing."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, other_t = children

        def thunk(rt: Runtime) -> None:
            # Operands first: a refused one must not create the target.
            other = other_t(rt)
            if is_null(other):
                raise ValueError("cannot write with a NULL operand")
            target = target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            target.update(other)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, other_t = children

        async def athunk(rt: Runtime) -> None:
            # Operands first: a refused one must not create the target.
            other = await other_t(rt)
            if is_null(other):
                raise ValueError("cannot write with a NULL operand")
            target = await target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            target.update(other)

        return athunk


# =============================================================================
# MAPPING MUTATIONS, YIELD A VALUE (Action)
# =============================================================================


class MergeUpdate(ScalarAction):
    """In-place merge: mapping |= other. Mutates slot 0 and yields the mapping.

    Python's ``dict.__ior__`` updates in place and returns ``self``, so it both
    mutates and yields -> Action.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, other_t = children

        def thunk(rt: Runtime) -> object:
            # Operands first: a refused one must not create the target.
            other = other_t(rt)
            if is_null(other):
                raise ValueError("cannot write with a NULL operand")
            target = target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            target |= other
            return target

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, other_t = children

        async def athunk(rt: Runtime) -> object:
            # Operands first: a refused one must not create the target.
            other = await other_t(rt)
            if is_null(other):
                raise ValueError("cannot write with a NULL operand")
            target = await target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            target |= other
            return target

        return athunk


class DictPop(ScalarAction):
    """Pop value by key with optional default: mapping.pop(key, default).

    Mutates slot 0 (removes the entry) and yields the value or default.
    Children are ``(mapping, key)`` or ``(mapping, key, default)``. A default,
    NULL and None included, is forwarded to the mapping's own ``pop``: it is
    yielded, never written, so NULL is a valid default.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")
    _creates = Declared(value=frozenset(), name="creates")
    """Acts on an absent container as on an empty one, and leaves it absent."""

    def __init__(self, mapping: object, key: object, default: object = UNSET) -> None:
        if default is UNSET:
            super().__init__(mapping, key)
        else:
            super().__init__(mapping, key, default)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t, *rest = children
        c_t = rest[0] if rest else None

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if is_null(a):
                raise ValueError("cannot write with a NULL operand")
            b = b_t(rt)
            if is_null(b):
                raise ValueError("cannot write with a NULL operand")
            if c_t is None:
                return a.pop(b)
            return a.pop(b, c_t(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t, *rest = children
        c_t = rest[0] if rest else None

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if is_null(a):
                raise ValueError("cannot write with a NULL operand")
            b = await b_t(rt)
            if is_null(b):
                raise ValueError("cannot write with a NULL operand")
            if c_t is None:
                return a.pop(b)
            return a.pop(b, await c_t(rt))

        return athunk


class PopItem(ScalarAction):
    """Pop arbitrary item: mapping.popitem().

    Mutates slot 0 (removes the entry) and yields the (key, value) tuple.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")
    _creates = Declared(value=frozenset(), name="creates")
    """Acts on an absent container as on an empty one, and leaves it absent."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            obj = operand(rt)
            if is_null(obj):
                raise ValueError("cannot write with a NULL operand")
            return obj.popitem()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            obj = await operand(rt)
            if is_null(obj):
                raise ValueError("cannot write with a NULL operand")
            return obj.popitem()

        return athunk


class SetDefault(ScalarAction):
    """Set default value if key missing: mapping.setdefault(key, default).

    Mutates slot 0 (inserts the entry when the key is missing) and yields the
    value at the key.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t, c_t = children

        def thunk(rt: Runtime) -> object:
            # Operands first: a refused one must not create the target.
            b = b_t(rt)
            if is_null(b):
                raise ValueError("cannot write with a NULL operand")
            c = c_t(rt)
            if is_null(c):
                raise ValueError("cannot write with a NULL operand")
            a = a_t(rt)
            if is_null(a):
                raise ValueError("cannot write with a NULL operand")
            return a.setdefault(b, c)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t, c_t = children

        async def athunk(rt: Runtime) -> object:
            # Operands first: a refused one must not create the target.
            b = await b_t(rt)
            if is_null(b):
                raise ValueError("cannot write with a NULL operand")
            c = await c_t(rt)
            if is_null(c):
                raise ValueError("cannot write with a NULL operand")
            a = await a_t(rt)
            if is_null(a):
                raise ValueError("cannot write with a NULL operand")
            return a.setdefault(b, c)

        return athunk
