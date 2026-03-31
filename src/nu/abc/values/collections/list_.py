"""Concrete list value for Python memory storage."""

from __future__ import annotations

from ...types import ListType
from ..base import ValueBase


class ListValue[T](ValueBase[list[T]], ListType[T]):
    """Concrete list value for Python memory storage."""

    pass
