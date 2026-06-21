"""Mapping ops.

KeysOp, ValuesOp, ItemsOp, GetOp
SetItemCmd, DeleteItemCmd, UpdateCmd
DictPopCmd, PopItemCmd, SetDefaultCmd
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.lang import ScalarQuery
from nu2.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.runtime import Runtime


__all__ = [
    "DeleteItemCmd",
    "DictPopCmd",
    "GetOp",
    "ItemsOp",
    "KeysOp",
    "PopItemCmd",
    "SetDefaultCmd",
    "SetItemCmd",
    "UpdateCmd",
    "ValuesOp",
]


# =============================================================================
# MAPPING READS
# =============================================================================


class KeysOp(ScalarQuery):
    """Get keys view from mapping: mapping.keys()."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            obj = operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            return obj.keys()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            obj = await operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            return obj.keys()

        return athunk


class ValuesOp(ScalarQuery):
    """Get values view from mapping: mapping.values()."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            obj = operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            return obj.values()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            obj = await operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            return obj.values()

        return athunk


class ItemsOp(ScalarQuery):
    """Get items view from mapping: mapping.items()."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            obj = operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            return obj.items()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            obj = await operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            return obj.items()

        return athunk


class GetOp(ScalarQuery):
    """Get value from mapping with optional default: mapping.get(key, default) or mapping[key]."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


# =============================================================================
# MAPPING MUTATIONS
# =============================================================================


class SetItemCmd(ScalarQuery):
    """Set value at key: mapping[key] = value; yields the mapping."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, key_t, value_t = children

        def thunk(rt: Runtime) -> object:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            key = key_t(rt)
            if key is EMPTY or key is INVALID:
                return INVALID
            value = value_t(rt)
            if value is EMPTY or value is INVALID:
                return INVALID
            target[key] = value
            return target

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, key_t, value_t = children

        async def athunk(rt: Runtime) -> object:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            key = await key_t(rt)
            if key is EMPTY or key is INVALID:
                return INVALID
            value = await value_t(rt)
            if value is EMPTY or value is INVALID:
                return INVALID
            target[key] = value
            return target

        return athunk


class DeleteItemCmd(ScalarQuery):
    """Delete entry by key: del mapping[key]; yields the mapping."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, key_t = children

        def thunk(rt: Runtime) -> object:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            key = key_t(rt)
            if key is EMPTY or key is INVALID:
                return INVALID
            del target[key]
            return target

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, key_t = children

        async def athunk(rt: Runtime) -> object:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            key = await key_t(rt)
            if key is EMPTY or key is INVALID:
                return INVALID
            del target[key]
            return target

        return athunk


class UpdateCmd(ScalarQuery):
    """Update mapping with another: mapping.update(other); yields the mapping."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, other_t = children

        def thunk(rt: Runtime) -> object:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            other = other_t(rt)
            if other is EMPTY or other is INVALID:
                return INVALID
            target.update(other)
            return target

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, other_t = children

        async def athunk(rt: Runtime) -> object:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            other = await other_t(rt)
            if other is EMPTY or other is INVALID:
                return INVALID
            target.update(other)
            return target

        return athunk


class DictPopCmd(ScalarQuery):
    """Pop value by key with optional default: mapping.pop(key, default). Returns value or default."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class PopItemCmd(ScalarQuery):
    """Pop arbitrary item: mapping.popitem(). Returns (key, value) tuple."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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


class SetDefaultCmd(ScalarQuery):
    """Set default value if key missing: mapping.setdefault(key, default). Returns value at key."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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
