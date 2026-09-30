"""Attributes - the flat name store behind ``ctx.attrs``.

Attached to Context as ctx.attrs. Carried across scope boundaries via copy().
Refs read here, and every binder goes through the three binding operations:
``let`` declares, ``set`` reassigns, ``exists`` asks.
"""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from types import TracebackType


__all__ = ["Attributes"]


class Attributes:
    """Flat name store for pure values, and the one owner of the binding rules.

    A name comes into scope with ``let`` and leaves when that scope ends,
    whatever ends it. ``set`` reassigns the innermost visible binding and
    refuses a name nothing declared, so no write outlives a scope. Binders
    go through these three operations and hold no binding logic of their own.

    The item surface (``attrs[k]``, ``in``, ``items``) is the raw store: it
    carries attrs across a scope boundary or into a worker, and is not a way
    to bind.

    Usage:
        attrs = Attributes()
        with attrs.let("n", 1):
            attrs.set("n", 2)
            attrs.exists("n")           # -> True
        attrs.exists("n")               # -> False

        copied = attrs.copy()           # independent deep copy
        arm = attrs.copy_shallow()      # own key space, values shared
    """

    __slots__ = ("_data",)

    def __init__(self, data: dict[str, object] | None = None) -> None:
        self._data: dict[str, object] = data if data is not None else {}

    def __getitem__(self, key: str) -> object:
        return self._data[key]

    def __setitem__(self, key: str, value: object) -> None:
        self._data[key] = value

    def __delitem__(self, key: str) -> None:
        del self._data[key]

    def __contains__(self, key: object) -> bool:
        return key in self._data

    def __len__(self) -> int:
        return len(self._data)

    def __bool__(self) -> bool:
        return bool(self._data)

    # -- binding -----------------------------------------------------------

    def let(self, name: object, value: object) -> _Let:
        """A scope that declares ``name`` holding ``value``.

        Entering shadows any outer binding of ``name``; leaving restores it,
        or removes the name when nothing was bound, on a clean exit and on an
        error alike. A generator may hold the scope open across its yields,
        so a binding over a stream lives while the stream is drained and is
        released when it is exhausted, closed, or cancelled.

        Raises:
            TypeError: ``name`` is not a ``str``.
        """
        if not isinstance(name, str):
            msg = f"attr name must be a str, got {type(name).__name__}"
            raise TypeError(msg)
        return _Let(self._data, name, value)

    def set(self, name: object, value: object) -> None:
        """Reassign the innermost binding of ``name`` to ``value``.

        Raises:
            NameError: nothing declared ``name``.
        """
        if name not in self._data:
            msg = f"cannot set attr {name!r}: it is not declared. Declare it with nu.Let({name!r}, ...) first."
            raise NameError(msg)
        self._data[name] = value  # type: ignore[index]

    def exists(self, name: object) -> bool:
        """Whether ``name`` is declared, whatever it holds (EMPTY included)."""
        return name in self._data

    # -- raw store -----------------------------------------------------------

    def get(self, key: str, default: object = None) -> object:
        """Get value by key with optional default."""
        return self._data.get(key, default)

    def keys(self):  # noqa: ANN201
        """All attribute keys."""
        return self._data.keys()

    def values(self):  # noqa: ANN201
        """All attribute values."""
        return self._data.values()

    def items(self):  # noqa: ANN201
        """All attribute key-value pairs."""
        return self._data.items()

    def copy(self) -> Attributes:
        """Deep copy for scope carry."""
        return Attributes(deepcopy(self._data))

    def copy_shallow(self) -> Attributes:
        """Shallow copy for a concurrent branch: own key space, values shared.

        Rebinding a key on the copy leaves the original alone, which is what
        a fan-out needs so sibling arms do not stomp each other's loop
        variable. Values are shared by reference, so a live handle (a task, a
        client, an open store) crosses the branch intact where ``copy`` would
        choke on it and mutating one in place is seen by everyone.
        """
        return Attributes(dict(self._data))

    def __repr__(self) -> str:
        if not self._data:
            return "Attributes()"
        items = ", ".join(f"{k}={v!r}" for k, v in self._data.items())
        return f"Attributes({items})"


class _Let:
    """One ``let`` scope: binds on enter, puts the prior state back on exit."""

    __slots__ = ("_data", "_had_prev", "_name", "_prev", "_value")

    def __init__(self, data: dict[str, object], name: str, value: object) -> None:
        self._data = data
        self._name = name
        self._value = value
        self._had_prev = False
        self._prev: object = None

    def __enter__(self) -> None:
        self._had_prev = self._name in self._data
        self._prev = self._data.get(self._name)
        self._data[self._name] = self._value

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._had_prev:
            self._data[self._name] = self._prev
        else:
            self._data.pop(self._name, None)
