"""Python memory frozenset ref.

FrozenSetRef = PyRefBase + FrozenSetRefBase
"""

from __future__ import annotations

from everybase.refs import FrozenSetRefBase

from .base import PyRefBase


__all__ = [
    "FrozenSetRef",
]


class FrozenSetRef[T](PyRefBase[frozenset[T]], FrozenSetRefBase[T]):
    """Concrete frozenset ref for Python memory storage.

    Inherits:
    - PyRefBase: source storage, get() implementation
    - FrozenSetRefBase: set operations/comparison traits
    """

    pass
