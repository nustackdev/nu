"""Python memory dict ref.

DictRef = PyRefBase + DictRefBase
"""

from __future__ import annotations

from everybase.refs import DictRefBase

from .base import PyRefBase


__all__ = [
    "DictRef",
]


class DictRef[K, V](PyRefBase[dict[K, V]], DictRefBase[K, V]):
    """Concrete dict ref for Python memory storage.

    Inherits:
    - PyRefBase: source storage, get() implementation
    - DictRefBase: mapping/comparison traits
    """

    pass
