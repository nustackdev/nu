"""Python memory set ref.

SetRef = PyRefBase + SetRefBase
"""

from __future__ import annotations

from everybase.refs import SetRefBase

from .base import PyRefBase


__all__ = [
    "SetRef",
]


class SetRef[T](PyRefBase[set[T]], SetRefBase[T]):
    """Concrete set ref for Python memory storage.

    Inherits:
    - PyRefBase: source storage, get() implementation
    - SetRefBase: set operations/comparison traits
    """

    pass
