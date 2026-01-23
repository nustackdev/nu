"""Python memory list ref.

ListRef = PyRefBase + ListRefBase
"""

from __future__ import annotations

from everybase.refs import ListRefBase

from .base import PyRefBase


__all__ = [
    "ListRef",
]


class ListRef[T](PyRefBase[list[T]], ListRefBase[T]):
    """Concrete list ref for Python memory storage.

    Inherits:
    - PyRefBase: source storage, get() implementation
    - ListRefBase: sequence/comparison traits
    """

    pass
