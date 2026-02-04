# ruff: noqa: D102
"""Collection view protocols — structural contracts for storage/view objects.

These protocols formalize what storage views must implement for
collection-level morphisms (extract, store, clear) to operate on them.

Used by morphisms via isinstance() checks instead of hasattr().
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


__all__ = [
    "ClearableProtocol",
    "ExtractableProtocol",
    "StorableProtocol",
]


@runtime_checkable
class ExtractableProtocol(Protocol):
    """View that can extract its contents as a Python value."""

    def extract(self) -> object: ...


@runtime_checkable
class StorableProtocol(Protocol):
    """View that can replace its contents from a Python value."""

    def store(self, data: object) -> None: ...


@runtime_checkable
class ClearableProtocol(Protocol):
    """View that can clear all its contents."""

    def clear(self) -> None: ...
