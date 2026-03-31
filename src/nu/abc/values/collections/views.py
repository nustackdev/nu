"""Concrete dict view value types for Python memory storage."""

from __future__ import annotations

from collections.abc import ItemsView, KeysView, ValuesView

from ...types.collections.views import DictItemsType, DictKeysType, DictValuesType
from ..base import ValueBase


class DictKeysValue[K](ValueBase[KeysView[K]], DictKeysType[K]):
    """Concrete dict keys view value."""

    pass


class DictValuesValue[V](ValueBase[ValuesView[V]], DictValuesType[V]):
    """Concrete dict values view value."""

    pass


class DictItemsValue[K, V](ValueBase[ItemsView[K, V]], DictItemsType[K, V]):
    """Concrete dict items view value."""

    pass
