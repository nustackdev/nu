"""Concrete float value for Python memory storage."""

from __future__ import annotations

from ...types import FloatType
from ..base import ValueBase


class FloatValue(ValueBase[float], FloatType):
    """Concrete float value for Python memory storage."""

    pass
