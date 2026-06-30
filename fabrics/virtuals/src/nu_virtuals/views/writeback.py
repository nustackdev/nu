"""Write-back wrappers for primitive compound values.

Subclass the native Python container (set/dict/list) so the object passes
every isinstance/duck-typing check and supports the full native interface.
Mutations mark the view dirty; an explicit ._flush() at scope exit writes
the current state back to storage via the parent view's _primitive_write.

The primitive refs (PrimitiveSetRef, PrimitiveDictRef, PrimitiveListRef)
override their open() contextmanager to:
  1. fetch current value (defaulting to empty)
  2. wrap in the corresponding write-back view
  3. yield it
  4. on exit, if dirty, write the whole blob back

This makes blob-ref mutation work uniformly with the in-place algebra that
already works for decomposed view refs. No per-method overrides needed.
"""

from __future__ import annotations

from typing import Any


__all__ = [
    "PrimitiveDictView",
    "PrimitiveListView",
    "PrimitiveSetView",
]


# --- Set --------------------------------------------------------------------


class PrimitiveSetView(set):
    """Set subclass that buffers mutations and flushes back to storage."""

    __slots__ = ("_address", "_dirty", "_parent")

    def __init__(self, initial: Any = (), parent: Any = None, address: Any = None) -> None:
        super().__init__(initial)
        self._parent = parent
        self._address = address
        self._dirty = False

    # --- mutators ---
    def add(self, value: Any) -> None:
        super().add(value)
        self._dirty = True

    def remove(self, value: Any) -> None:
        super().remove(value)
        self._dirty = True

    def discard(self, value: Any) -> None:
        before = len(self)
        super().discard(value)
        if len(self) != before:
            self._dirty = True

    def pop(self) -> Any:
        value = super().pop()
        self._dirty = True
        return value

    def clear(self) -> None:
        if len(self):
            super().clear()
            self._dirty = True

    def update(self, *others: Any) -> None:
        super().update(*others)
        self._dirty = True

    def intersection_update(self, *others: Any) -> None:
        super().intersection_update(*others)
        self._dirty = True

    def difference_update(self, *others: Any) -> None:
        super().difference_update(*others)
        self._dirty = True

    def symmetric_difference_update(self, other: Any) -> None:
        super().symmetric_difference_update(other)
        self._dirty = True

    def __ior__(self, other: Any) -> PrimitiveSetView:
        super().__ior__(other)
        self._dirty = True
        return self

    def __iand__(self, other: Any) -> PrimitiveSetView:
        super().__iand__(other)
        self._dirty = True
        return self

    def __isub__(self, other: Any) -> PrimitiveSetView:
        super().__isub__(other)
        self._dirty = True
        return self

    def __ixor__(self, other: Any) -> PrimitiveSetView:
        super().__ixor__(other)
        self._dirty = True
        return self

    # --- flush ---
    def _flush(self) -> None:
        if self._dirty and self._parent is not None:
            self._parent._primitive_write(self._address, set(self))
            self._dirty = False


# --- Dict -------------------------------------------------------------------


class PrimitiveDictView(dict):
    """Dict subclass that buffers mutations and flushes back to storage."""

    __slots__ = ("_address", "_dirty", "_parent")

    def __init__(self, initial: Any = (), parent: Any = None, address: Any = None) -> None:
        super().__init__(initial)
        self._parent = parent
        self._address = address
        self._dirty = False

    def __setitem__(self, key: Any, value: Any) -> None:
        super().__setitem__(key, value)
        self._dirty = True

    def __delitem__(self, key: Any) -> None:
        super().__delitem__(key)
        self._dirty = True

    def pop(self, key: Any, *args: Any) -> Any:
        existed = key in self
        value = super().pop(key, *args)
        if existed:
            self._dirty = True
        return value

    def popitem(self) -> Any:
        item = super().popitem()
        self._dirty = True
        return item

    def clear(self) -> None:
        if len(self):
            super().clear()
            self._dirty = True

    def update(self, *args: Any, **kwargs: Any) -> None:
        super().update(*args, **kwargs)
        self._dirty = True

    def setdefault(self, key: Any, default: Any = None) -> Any:
        if key not in self:
            self._dirty = True
        return super().setdefault(key, default)

    def _flush(self) -> None:
        if self._dirty and self._parent is not None:
            self._parent._primitive_write(self._address, dict(self))
            self._dirty = False


# --- List -------------------------------------------------------------------


class PrimitiveListView(list):
    """List subclass that buffers mutations and flushes back to storage."""

    __slots__ = ("_address", "_dirty", "_parent")

    def __init__(self, initial: Any = (), parent: Any = None, address: Any = None) -> None:
        super().__init__(initial)
        self._parent = parent
        self._address = address
        self._dirty = False

    def append(self, value: Any) -> None:
        super().append(value)
        self._dirty = True

    def extend(self, values: Any) -> None:
        super().extend(values)
        self._dirty = True

    def insert(self, index: int, value: Any) -> None:
        super().insert(index, value)
        self._dirty = True

    def remove(self, value: Any) -> None:
        super().remove(value)
        self._dirty = True

    def pop(self, index: int = -1) -> Any:
        value = super().pop(index)
        self._dirty = True
        return value

    def clear(self) -> None:
        if len(self):
            super().clear()
            self._dirty = True

    def reverse(self) -> None:
        if len(self) > 1:
            super().reverse()
            self._dirty = True

    def sort(self, *args: Any, **kwargs: Any) -> None:
        super().sort(*args, **kwargs)
        self._dirty = True

    def __setitem__(self, index: Any, value: Any) -> None:
        super().__setitem__(index, value)
        self._dirty = True

    def __delitem__(self, index: Any) -> None:
        super().__delitem__(index)
        self._dirty = True

    def __iadd__(self, other: Any) -> PrimitiveListView:
        super().__iadd__(other)
        self._dirty = True
        return self

    def __imul__(self, count: int) -> PrimitiveListView:
        super().__imul__(count)
        self._dirty = True
        return self

    def _flush(self) -> None:
        if self._dirty and self._parent is not None:
            self._parent._primitive_write(self._address, list(self))
            self._dirty = False
