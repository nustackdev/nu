# ruff: noqa: D102
"""Mapping capability protocol — Collection + keys/values/items/get.

Follows Python's collections.abc.Mapping pattern.
"""

from __future__ import annotations

from typing import Protocol

from .col_collection_protocol import CollectionProtocol


__all__ = [
    "MappingProtocol",
]


class MappingProtocol[KeyT, ValueT, ResultT](
    CollectionProtocol[KeyT, ResultT],
    Protocol,
):
    """Protocol for mapping values — like collections.abc.Mapping."""

    def keys_(self) -> ResultT: ...
    def values_(self) -> ResultT: ...
    def items_(self) -> ResultT: ...
    def get_(self, key: KeyT, default: ValueT | None = None) -> ResultT: ...
