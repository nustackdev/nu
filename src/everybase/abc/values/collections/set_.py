"""Concrete set value types for Python memory storage."""

from __future__ import annotations

from ...types import FrozenSetType, SetType
from ..base import ValueBase


class SetValue[T](ValueBase[set[T]], SetType[T]):
    """Concrete set value for Python memory storage."""

    pass


class FrozenSetValue[T](ValueBase[frozenset[T]], FrozenSetType[T]):
    """Concrete frozenset value for Python memory storage."""

    pass
