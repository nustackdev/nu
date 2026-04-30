"""Mapping ops.

KeysOp, ValuesOp, ItemsOp, GetOp
SetItemCmd, DeleteItemCmd, UpdateCmd
DictPopCmd, PopItemCmd, SetDefaultCmd
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from typing import Any, ClassVar

from nu.terms.command import ScalarCommand
from nu.terms.query import ScalarQuery
from nu.terms.sentinels import INVALID
from nu.terms.types import Effect, Mode


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


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


# =============================================================================
# MAPPING READS
# =============================================================================


class KeysOp(ScalarQuery):
    """Get keys view from mapping: mapping.keys()."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand = ops[0]
        if not isinstance(operand, Mapping):
            raise TypeError(f"keys() requires mapping, got {type(operand).__name__}")
        return operand.keys()


class ValuesOp(ScalarQuery):
    """Get values view from mapping: mapping.values()."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand = ops[0]
        if not isinstance(operand, Mapping):
            raise TypeError(f"values() requires mapping, got {type(operand).__name__}")
        return operand.values()


class ItemsOp(ScalarQuery):
    """Get items view from mapping: mapping.items()."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand = ops[0]
        if not isinstance(operand, Mapping):
            raise TypeError(f"items() requires mapping, got {type(operand).__name__}")
        return operand.items()


class GetOp(ScalarQuery):
    """Get value from mapping with optional default: mapping.get(key, default) or mapping[key]."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, first: Any, second: Any, third: Any) -> None:  # noqa: ANN401
        super().__init__(first, second, third)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b, c = ops
        if not isinstance(a, Mapping):
            raise TypeError(f"get() requires mapping, got {type(a).__name__}")
        if c is None:
            return a[b]
        return a.get(b, c)


# =============================================================================
# MAPPING MUTATIONS
# =============================================================================


class SetItemCmd(ScalarCommand):
    """Set value at key: mapping[key] = value. Mutates target Ref in-place."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, first: Any, second: Any, third: Any) -> None:  # noqa: ANN401
        super().__init__(first, second, third)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = runtime.first(self._children[0], ctx)
        key = runtime.first(self._children[1], ctx)
        value = runtime.first(self._children[2], ctx)
        if not isinstance(target, MutableMapping):
            raise TypeError(f"set() requires mutable mapping, got {type(target).__name__}")
        target[key] = value

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = await runtime.afirst(self._children[0], ctx)
        key = await runtime.afirst(self._children[1], ctx)
        value = await runtime.afirst(self._children[2], ctx)
        if not isinstance(target, MutableMapping):
            raise TypeError(f"set() requires mutable mapping, got {type(target).__name__}")
        target[key] = value


class DeleteItemCmd(ScalarCommand):
    """Delete entry by key: del mapping[key]. Mutates target Ref in-place."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = runtime.first(self._children[0], ctx)
        key = runtime.first(self._children[1], ctx)
        if not isinstance(target, MutableMapping):
            raise TypeError(f"delete() requires mutable mapping, got {type(target).__name__}")
        del target[key]

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = await runtime.afirst(self._children[0], ctx)
        key = await runtime.afirst(self._children[1], ctx)
        if not isinstance(target, MutableMapping):
            raise TypeError(f"delete() requires mutable mapping, got {type(target).__name__}")
        del target[key]


class UpdateCmd(ScalarCommand):
    """Update mapping with another: mapping.update(other). Mutates target Ref in-place."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = runtime.first(self._children[0], ctx)
        other = runtime.first(self._children[1], ctx)
        if not isinstance(target, MutableMapping):
            raise TypeError(f"update() requires mutable mapping, got {type(target).__name__}")
        if not isinstance(other, Mapping):
            raise TypeError(f"update() requires mapping, got {type(other).__name__}")
        target.update(other)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = await runtime.afirst(self._children[0], ctx)
        other = await runtime.afirst(self._children[1], ctx)
        if not isinstance(target, MutableMapping):
            raise TypeError(f"update() requires mutable mapping, got {type(target).__name__}")
        if not isinstance(other, Mapping):
            raise TypeError(f"update() requires mapping, got {type(other).__name__}")
        target.update(other)


class DictPopCmd(ScalarQuery):
    """Pop value by key with optional default: mapping.pop(key, default). Returns value or default."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, first: Any, second: Any, third: Any) -> None:  # noqa: ANN401
        super().__init__(first, second, third)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b, c = ops
        if not isinstance(a, MutableMapping):
            raise TypeError(f"pop() requires mutable mapping, got {type(a).__name__}")
        if c is None:
            try:
                return a.pop(b)
            except KeyError:
                return INVALID
        return a.pop(b, c)


class PopItemCmd(ScalarQuery):
    """Pop arbitrary item: mapping.popitem(). Returns (key, value) tuple."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand = ops[0]
        if not isinstance(operand, MutableMapping):
            raise TypeError(f"popitem() requires mutable mapping, got {type(operand).__name__}")
        try:
            return operand.popitem()
        except KeyError:
            return INVALID


class SetDefaultCmd(ScalarQuery):
    """Set default value if key missing: mapping.setdefault(key, default). Returns value at key."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, first: Any, second: Any, third: Any) -> None:  # noqa: ANN401
        super().__init__(first, second, third)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b, c = ops
        if not isinstance(a, MutableMapping):
            raise TypeError(f"setdefault() requires mutable mapping, got {type(a).__name__}")
        return a.setdefault(b, c)
