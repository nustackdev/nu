"""Python memory boolean ref.

BoolRef = PyRefBase + BoolRefBase
"""

from __future__ import annotations

from everybase.refs import BoolRefBase

from .base import PyRefBase


__all__ = [
    "BoolRef",
]


class BoolRef(PyRefBase[bool], BoolRefBase):
    """Concrete boolean ref for Python memory storage.

    Inherits:
    - PyRefBase: source storage, get() implementation
    - BoolRefBase: logical/comparison traits
    """

    pass
