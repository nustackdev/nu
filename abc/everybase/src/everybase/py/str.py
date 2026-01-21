"""Python memory string ref.

StrRef = PyRefBase + StrRefBase
"""

from __future__ import annotations

from everybase.refs import StrRefBase

from .base import PyRefBase


__all__ = [
    "StrRef",
]


class StrRef(PyRefBase[str], StrRefBase):
    """Concrete string ref for Python memory storage.

    Inherits:
    - PyRefBase: source storage, get() implementation
    - StrRefBase: string operations, comparison, logical traits
    """

    pass
