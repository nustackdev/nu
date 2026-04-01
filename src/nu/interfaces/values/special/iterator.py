"""Concrete iterator value for Python memory storage."""

from __future__ import annotations

from collections.abc import Iterator

from ...types.special.iterator import IteratorType
from ..base import ValueBase


__all__ = [
    "IteratorValue",
]


class IteratorValue[T](ValueBase[Iterator[T]], IteratorType[T]):
    """Concrete lazy iterator value for Python memory storage.

    Wraps a Nu that produces an Iterator[T] when executed.
    Each execute() call produces a fresh iterator.
    """

    pass
