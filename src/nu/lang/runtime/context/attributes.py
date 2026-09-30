"""Attributes - the flat name store behind ``ctx.attrs``.

Refs read here, and every binder goes through the three binding operations:
``let`` declares, ``set`` reassigns, ``exists`` asks. A starting task takes
its own table with ``Context.branch``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang.sentinels import EMPTY


if TYPE_CHECKING:
    from collections.abc import ItemsView
    from types import TracebackType


__all__ = ["Attributes"]


class Attributes:
    """Flat name store for pure values, and the one owner of the binding rules.

    A name comes into scope with ``let`` and leaves when that scope ends,
    whatever ends it. ``set`` reassigns the innermost visible binding and
    refuses a name nothing declared, so no write outlives a scope. Binders
    go through these three operations and hold no binding logic of their own.

    Reads (``get``, ``items``) never bind. Names a Context starts with are
    seeded through ``Context(attrs=...)``.

    Usage:
        attrs = Attributes()
        with attrs.let("n", 1):
            attrs.set("n", 2)
            attrs.exists("n")           # -> True
            attrs.get("n")              # -> 2
        attrs.exists("n")               # -> False
    """

    __slots__ = ("_data",)

    def __init__(self, data: dict[str, object] | None = None) -> None:
        self._data: dict[str, object] = data if data is not None else {}

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
            msg = f"cannot set attr {name!r}: it is not declared. Bind it with attrs.let first."
            raise NameError(msg)
        self._data[name] = value  # type: ignore[index]

    def exists(self, name: object) -> bool:
        """Whether ``name`` is declared, whatever it holds (EMPTY included)."""
        return name in self._data

    # -- reads ---------------------------------------------------------------

    def get(self, name: str, default: object = EMPTY) -> object:
        """The value ``name`` holds, or ``default`` when it is not declared."""
        return self._data.get(name, default)

    def items(self) -> ItemsView[str, object]:
        """Every declared name and its value, read-only."""
        return self._data.items()

    def _branch(self) -> Attributes:
        """Own table, same values: a name set or let on the copy stays on the copy."""
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
