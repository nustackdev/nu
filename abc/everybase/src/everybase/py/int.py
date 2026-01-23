"""Python memory integer ref.

IntRef = PyRefBase + IntRefBase
"""

from __future__ import annotations

from everybase.refs import IntRefBase

from .base import PyRefBase


__all__ = [
    "IntRef",
]


class IntRef(PyRefBase[int], IntRefBase):
    """Concrete integer ref for Python memory storage.

    Inherits:
    - PyRefBase: source storage, get() implementation
    - IntRefBase: numeric/comparison/logical/bitwise traits
    """

    pass
