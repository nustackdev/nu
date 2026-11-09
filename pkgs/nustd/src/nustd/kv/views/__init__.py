"""Write-through values for the blob refs.

A list, dict or set a blob ref evaluates to in a mutation slot: a real native
container that stores itself whole after every mutating call, so a mutation
written on the ref persists.
"""

from __future__ import annotations

from .writeback import PrimitiveDictView, PrimitiveListView, PrimitiveSetView


__all__ = [
    "PrimitiveDictView",
    "PrimitiveListView",
    "PrimitiveSetView",
]
