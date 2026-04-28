"""Mapping ops.

KeysOp, ValuesOp, ItemsOp, GetOp
SetItemCmd, DeleteItemCmd, UpdateCmd
DictPopCmd, PopItemCmd, SetDefaultCmd
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from typing import Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.sentinels import INVALID
from nu.terms.types import Mode


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


class SetItemCmd(ScalarQuery):
    """Set value at key: mapping[key] = value. Returns None."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, first: Any, second: Any, third: Any) -> None:  # noqa: ANN401
        super().__init__(first, second, third)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b, c = ops
        if not isinstance(a, MutableMapping):
            raise TypeError(f"set() requires mutable mapping, got {type(a).__name__}")
        a[b] = c
        return None


class DeleteItemCmd(ScalarQuery):
    """Delete entry by key: del mapping[key]. Returns None."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b = ops
        if not isinstance(a, MutableMapping):
            raise TypeError(f"delete() requires mutable mapping, got {type(a).__name__}")
        try:
            del a[b]
        except KeyError:
            return INVALID
        return None


class UpdateCmd(ScalarQuery):
    """Update mapping with another: mapping.update(other). Returns None (mutates in-place)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b = ops
        if not isinstance(a, MutableMapping):
            raise TypeError(f"update() requires mutable mapping, got {type(a).__name__}")
        if not isinstance(b, Mapping):
            return INVALID
        a.update(b)
        return None


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
