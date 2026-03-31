"""Concrete boolean value for Python memory storage."""

from __future__ import annotations

from ...types import BoolType
from ..base import ValueBase


class BoolValue(ValueBase[bool], BoolType):
    """Concrete boolean value for Python memory storage."""

    pass
