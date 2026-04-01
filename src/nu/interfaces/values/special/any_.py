"""Concrete any/dynamic value for Python memory storage."""

from __future__ import annotations

from ...types import AnyType
from ..base import ValueBase


class AnyValue(ValueBase[object], AnyType):
    """Concrete any/dynamic value for Python memory storage."""

    pass
