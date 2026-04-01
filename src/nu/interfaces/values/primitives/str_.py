"""Concrete string value for Python memory storage."""

from __future__ import annotations

from ...types import StrType
from ..base import ValueBase


class StrValue(ValueBase[str], StrType):
    """Concrete string value for Python memory storage."""

    pass
