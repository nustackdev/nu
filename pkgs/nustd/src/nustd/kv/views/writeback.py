"""Write-through values for the blob refs: a list, dict or set that persists its mutations.

A blob ref (``PrimitiveListRef``, ``PrimitiveDictRef``, ``PrimitiveSetRef``)
stores a whole collection as one leaf value. A mutation written on the ref
(``rows.append(2)``) runs the native method on whatever the ref evaluates to,
so in a mutation slot the ref evaluates to one of these: a subclass of the
native container that writes the whole value back through its parent view
after every mutating call.

Each one is a real ``list`` / ``dict`` / ``set``: every isinstance check passes
and the whole native surface works. Nested values stay plain, so mutating an
element in place does not reach storage.

Notes:
    - Write-through, not buffered: Nu has no scope exit to flush at, so every
      mutating call stores the whole blob at once.
    - The write goes through the storage context the value was read under; a
      read-only one (a Snapshot) raises its read-only error on the first
      mutation, the in-memory value already changed.
    - ``setdefault`` on a key that is there changes nothing and writes nothing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typing_extensions import Self, override


if TYPE_CHECKING:
    from collections.abc import Iterable


__all__ = [
    "PrimitiveDictView",
    "PrimitiveListView",
    "PrimitiveSetView",
]


class _WriteThrough:
    """Holds where the blob lives and stores it whole after each mutation."""

    __slots__ = ()

    _parent: Any
    _address: object

    def _plain(self) -> object:
        """The value to store: a plain copy of the native type."""
        raise NotImplementedError

    def _persist(self) -> None:
        self._parent._primitive_write(self._address, self._plain())


class PrimitiveListView(_WriteThrough, list):
    """A list that stores itself whole after every mutating call."""

    __slots__ = ("_address", "_parent")

    def __init__(self, initial: Iterable[Any], parent: Any, address: object) -> None:  # noqa: ANN401
        super().__init__(initial)
        self._parent = parent
        self._address = address

    def _plain(self) -> list:
        return list(self)

    @override
    def append(self, value: Any) -> None:
        super().append(value)
        self._persist()

    @override
    def extend(self, values: Iterable[Any]) -> None:
        super().extend(values)
        self._persist()

    @override
    def insert(self, index: Any, value: Any) -> None:
        super().insert(index, value)
        self._persist()

    @override
    def remove(self, value: Any) -> None:
        super().remove(value)
        self._persist()

    @override
    def pop(self, index: Any = -1) -> Any:
        value = super().pop(index)
        self._persist()
        return value

    @override
    def clear(self) -> None:
        super().clear()
        self._persist()

    @override
    def reverse(self) -> None:
        super().reverse()
        self._persist()

    @override
    def sort(self, *args: Any, **kwargs: Any) -> None:
        super().sort(*args, **kwargs)
        self._persist()

    @override
    def __setitem__(self, index: Any, value: Any) -> None:
        super().__setitem__(index, value)
        self._persist()

    @override
    def __delitem__(self, index: Any) -> None:
        super().__delitem__(index)
        self._persist()

    @override
    def __iadd__(self, other: Iterable[Any]) -> Self:  # type: ignore[override]
        super().__iadd__(other)
        self._persist()
        return self

    @override
    def __imul__(self, count: Any) -> Self:  # type: ignore[override]
        super().__imul__(count)
        self._persist()
        return self


class PrimitiveDictView(_WriteThrough, dict):
    """A dict that stores itself whole after every mutating call."""

    __slots__ = ("_address", "_parent")

    def __init__(self, initial: Any, parent: Any, address: object) -> None:  # noqa: ANN401
        super().__init__(initial)
        self._parent = parent
        self._address = address

    def _plain(self) -> dict:
        return dict(self)

    @override
    def __setitem__(self, key: Any, value: Any) -> None:
        super().__setitem__(key, value)
        self._persist()

    @override
    def __delitem__(self, key: Any) -> None:
        super().__delitem__(key)
        self._persist()

    @override
    def pop(self, key: Any, *default: Any) -> Any:
        value = super().pop(key, *default)
        self._persist()
        return value

    @override
    def popitem(self) -> tuple[Any, Any]:
        item = super().popitem()
        self._persist()
        return item

    @override
    def clear(self) -> None:
        super().clear()
        self._persist()

    @override
    def update(self, *args: Any, **kwargs: Any) -> None:
        super().update(*args, **kwargs)
        self._persist()

    @override
    def setdefault(self, key: Any, default: Any = None) -> Any:
        if key in self:
            return self[key]
        value = super().setdefault(key, default)
        self._persist()
        return value

    @override
    def __ior__(self, other: Any) -> Self:  # type: ignore[override]
        super().__ior__(other)
        self._persist()
        return self


class PrimitiveSetView(_WriteThrough, set):
    """A set that stores itself whole after every mutating call."""

    __slots__ = ("_address", "_parent")

    def __init__(self, initial: Iterable[Any], parent: Any, address: object) -> None:  # noqa: ANN401
        super().__init__(initial)
        self._parent = parent
        self._address = address

    def _plain(self) -> set:
        return set(self)

    @override
    def add(self, value: Any) -> None:
        super().add(value)
        self._persist()

    @override
    def remove(self, value: Any) -> None:
        super().remove(value)
        self._persist()

    @override
    def discard(self, value: Any) -> None:
        super().discard(value)
        self._persist()

    @override
    def pop(self) -> Any:
        value = super().pop()
        self._persist()
        return value

    @override
    def clear(self) -> None:
        super().clear()
        self._persist()

    @override
    def update(self, *others: Iterable[Any]) -> None:
        super().update(*others)
        self._persist()

    @override
    def intersection_update(self, *others: Iterable[Any]) -> None:
        super().intersection_update(*others)
        self._persist()

    @override
    def difference_update(self, *others: Iterable[Any]) -> None:
        super().difference_update(*others)
        self._persist()

    @override
    def symmetric_difference_update(self, other: Iterable[Any]) -> None:
        super().symmetric_difference_update(other)
        self._persist()

    @override
    def __ior__(self, other: Any) -> Self:  # type: ignore[override]
        super().__ior__(other)
        self._persist()
        return self

    @override
    def __iand__(self, other: Any) -> Self:  # type: ignore[override]
        super().__iand__(other)
        self._persist()
        return self

    @override
    def __isub__(self, other: Any) -> Self:  # type: ignore[override]
        super().__isub__(other)
        self._persist()
        return self

    @override
    def __ixor__(self, other: Any) -> Self:  # type: ignore[override]
        super().__ixor__(other)
        self._persist()
        return self
