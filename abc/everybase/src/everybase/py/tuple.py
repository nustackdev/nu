"""Python memory tuple ref.

TupleRef = PyRefBase + TupleRefBase
"""

from __future__ import annotations

from everybase.refs import TupleRefBase

from .base import PyRefBase


__all__ = [
    "TupleRef",
]


class TupleRef[*Ts](PyRefBase[tuple[*Ts]], TupleRefBase[*Ts]):
    """Concrete tuple ref for Python memory storage.

    Inherits:
    - PyRefBase: source storage, get() implementation
    - TupleRefBase: sequence/comparison traits
    """

    pass
