"""Attributes -- flat mutable key-value store for primitive data.

Attached to Context as ctx.attrs. Carried across Teleport boundaries
via copy(). Used by PrimRef (attribute refs) for simple name-based storage.
"""

from __future__ import annotations

from copy import deepcopy


__all__ = [
    "Attributes",
]


class Attributes:
    """Flat mutable key-value store for primitive data.

    Usage:
        attrs = Attributes()
        attrs["error"] = "timeout"
        attrs["attempt"] = 3

        attrs["error"]          # -> "timeout"
        "error" in attrs        # -> True
        del attrs["error"]

        copied = attrs.copy()   # independent deep copy
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
        """Deep copy for Teleport carry."""
        return Attributes(deepcopy(self._data))

    def __repr__(self) -> str:
        if not self._data:
            return "Attributes()"
        items = ", ".join(f"{k}={v!r}" for k, v in self._data.items())
        return f"Attributes({items})"
