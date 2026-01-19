"""Core definitions for Key location.

Keys are tuples of strings and integers, used for identifying
entries in storage systems.

Keys are primarily used storage and tree layers.
"""

from __future__ import annotations


__all__ = [
    "Key",
    "KeySegment",
]

type KeySegment = str | int
type Key = tuple[KeySegment, ...]
