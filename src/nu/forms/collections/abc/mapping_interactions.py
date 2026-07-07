"""Mapping interactions.

Reads (Query): KeysQuery, ValuesQuery, ItemsQuery, GetQuery, ContainsKeyQuery,
    CopyQuery, ReversedKeysQuery, MergeQuery
Mutate, yield nothing (Command): SetItemCommand, DeleteItemCommand, UpdateCommand
Mutate and yield a value (Action): DictPopAction, PopItemAction, SetDefaultAction,
    MergeUpdateAction
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.factory import ScalarQueryFactory
from nu.lang import Command, ScalarAction, ScalarQuery, StreamQuery
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "ContainsKeyQuery",
    "CopyQuery",
    "DeleteItemCommand",
    "DictCreate",
    "DictOf",
    "DictPopAction",
    "GetQuery",
    "ItemsQuery",
    "KeysQuery",
    "MergeQuery",
    "MergeUpdateAction",
    "PopItemAction",
    "ReversedKeysQuery",
    "SetDefaultAction",
    "SetItemCommand",
    "UpdateCommand",
    "ValuesQuery",
]


# =============================================================================
# MAPPING CONSTRUCTORS
# =============================================================================

# Empty dict: deterministic (always {}), but each eval must yield a *fresh*
# mutable object - a future fold/CSE pass must not alias two DictCreate results.
DictCreate = ScalarQueryFactory("DictCreate", dict)
# Dict from named fields: DictOf(a=x, b=y) evaluates each field expression and
# zips names back into a fresh dict. A sentinel field short-circuits the whole
# record to INVALID (propagate_sentinels default).
DictOf = ScalarQueryFactory("DictOf", dict)


# =============================================================================
# MAPPING READS (Query)
# =============================================================================


class KeysQuery(ScalarQuery):
    """Get keys view from mapping: mapping.keys()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            obj = operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            return obj.keys()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            obj = await operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            return obj.keys()

        return athunk


class ValuesQuery(ScalarQuery):
    """Get values view from mapping: mapping.values()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            obj = operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            return obj.values()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            obj = await operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            return obj.values()

        return athunk


class ItemsQuery(ScalarQuery):
    """Get items view from mapping: mapping.items()."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            obj = operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            return obj.items()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            obj = await operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            return obj.items()

        return athunk


class GetQuery(ScalarQuery):
    """Get value from mapping with optional default: mapping.get(key, default) or mapping[key]."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t, c_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            c = c_t(rt)
            if c is EMPTY or c is INVALID:
                return INVALID
            if c is None:
                return a[b]
            return a.get(b, c)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t, c_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            c = await c_t(rt)
            if c is EMPTY or c is INVALID:
                return INVALID
            if c is None:
                return a[b]
            return a.get(b, c)

        return athunk


class ContainsKeyQuery(ScalarQuery):
    """Test key membership: key in mapping. Yields a bool."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, key_t = children

        def thunk(rt: Runtime) -> object:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            key = key_t(rt)
            if key is EMPTY or key is INVALID:
                return INVALID
            return key in target

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, key_t = children

        async def athunk(rt: Runtime) -> object:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            key = await key_t(rt)
            if key is EMPTY or key is INVALID:
                return INVALID
            return key in target

        return athunk


class CopyQuery(ScalarQuery):
    """Shallow copy of the mapping: mapping.copy(). Yields a new dict."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            obj = operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            return obj.copy()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            obj = await operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            return obj.copy()

        return athunk


class ReversedKeysQuery(StreamQuery):
    """Reverse-order keys: reversed(mapping). Yields keys in reverse insertion order."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            obj = operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            return reversed(obj)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            obj = await operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID

            async def agen() -> object:
                for k in reversed(obj):
                    yield k

            return agen()

        return athunk


class MergeQuery(ScalarQuery):
    """Merge two mappings into a new one: mapping | other. Yields a new dict."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a | b

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a | b

        return athunk


# =============================================================================
# MAPPING MUTATIONS, YIELD NOTHING (Command)
# =============================================================================


class SetItemCommand(Command):
    """SetQuery value at key: mapping[key] = value. Mutates slot 0; returns nothing."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, key_t, value_t = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            key = key_t(rt)
            if key is EMPTY or key is INVALID:
                return
            value = value_t(rt)
            if value is EMPTY or value is INVALID:
                return
            target[key] = value

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, key_t, value_t = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            key = await key_t(rt)
            if key is EMPTY or key is INVALID:
                return
            value = await value_t(rt)
            if value is EMPTY or value is INVALID:
                return
            target[key] = value

        return athunk


class DeleteItemCommand(Command):
    """Delete entry by key: del mapping[key]. Mutates slot 0; returns nothing."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, key_t = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            key = key_t(rt)
            if key is EMPTY or key is INVALID:
                return
            del target[key]

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, key_t = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            key = await key_t(rt)
            if key is EMPTY or key is INVALID:
                return
            del target[key]

        return athunk


class UpdateCommand(Command):
    """Update mapping with another: mapping.update(other). Mutates slot 0; returns nothing."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, other_t = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            other = other_t(rt)
            if other is EMPTY or other is INVALID:
                return
            target.update(other)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, other_t = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            other = await other_t(rt)
            if other is EMPTY or other is INVALID:
                return
            target.update(other)

        return athunk


# =============================================================================
# MAPPING MUTATIONS, YIELD A VALUE (Action)
# =============================================================================


class MergeUpdateAction(ScalarAction):
    """In-place merge: mapping |= other. Mutates slot 0 and yields the mapping.

    Python's ``dict.__ior__`` updates in place and returns ``self``, so it both
    mutates and yields -> Action.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, other_t = children

        def thunk(rt: Runtime) -> object:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            other = other_t(rt)
            if other is EMPTY or other is INVALID:
                return INVALID
            target |= other
            return target

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, other_t = children

        async def athunk(rt: Runtime) -> object:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            other = await other_t(rt)
            if other is EMPTY or other is INVALID:
                return INVALID
            target |= other
            return target

        return athunk


class DictPopAction(ScalarAction):
    """Pop value by key with optional default: mapping.pop(key, default).

    Mutates slot 0 (removes the entry) and yields the value or default.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t, c_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            c = c_t(rt)
            if c is EMPTY or c is INVALID:
                return INVALID
            if c is None:
                try:
                    return a.pop(b)
                except KeyError:
                    return INVALID
            return a.pop(b, c)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t, c_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            c = await c_t(rt)
            if c is EMPTY or c is INVALID:
                return INVALID
            if c is None:
                try:
                    return a.pop(b)
                except KeyError:
                    return INVALID
            return a.pop(b, c)

        return athunk


class PopItemAction(ScalarAction):
    """Pop arbitrary item: mapping.popitem().

    Mutates slot 0 (removes the entry) and yields the (key, value) tuple.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            obj = operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            try:
                return obj.popitem()
            except KeyError:
                return INVALID

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            obj = await operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            try:
                return obj.popitem()
            except KeyError:
                return INVALID

        return athunk


class SetDefaultAction(ScalarAction):
    """SetQuery default value if key missing: mapping.setdefault(key, default).

    Mutates slot 0 (inserts the entry when the key is missing) and yields the
    value at the key.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t, c_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            c = c_t(rt)
            if c is EMPTY or c is INVALID:
                return INVALID
            return a.setdefault(b, c)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t, c_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            c = await c_t(rt)
            if c is EMPTY or c is INVALID:
                return INVALID
            return a.setdefault(b, c)

        return athunk
