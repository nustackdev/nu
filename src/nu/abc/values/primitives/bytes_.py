"""Concrete bytes value for Python memory storage."""

from __future__ import annotations

from ...types import BytesType
from ..base import ValueBase


class BytesValue(ValueBase[bytes], BytesType):
    """Concrete bytes value for Python memory storage."""

    pass
