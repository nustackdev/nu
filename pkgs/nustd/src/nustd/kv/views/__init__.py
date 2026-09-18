"""Write-back views for primitive compound refs.

These views look and behave like native Python set/dict/list, but buffer
mutations and flush them back to storage when the ref's open() context
exits. Purpose: let in-place mutation ops (AddCmd, __setitem__, append, ...)
work transparently on blob-stored refs, without per-method overrides.
"""

from __future__ import annotations

from .writeback import PrimitiveDictView, PrimitiveListView, PrimitiveSetView


__all__ = [
    "PrimitiveDictView",
    "PrimitiveListView",
    "PrimitiveSetView",
]
