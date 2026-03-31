"""Concrete dict value for Python memory storage."""

from __future__ import annotations

from ...types import DictType
from ..base import ValueBase


class DictValue[K, V](ValueBase[dict[K, V]], DictType[K, V]):
    """Concrete dict value for Python memory storage."""

    pass
