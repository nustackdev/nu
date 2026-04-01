"""Concrete integer value for Python memory storage."""

from __future__ import annotations

from ...types import IntType
from ..base import ValueBase


class IntValue(ValueBase[int], IntType):
    """Concrete integer value for Python memory storage."""

    pass
