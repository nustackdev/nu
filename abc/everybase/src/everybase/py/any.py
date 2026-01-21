"""Python memory any/dynamic ref.

AnyRef = PyRefBase + AnyRefBase
"""

from __future__ import annotations

from everybase.refs import AnyRefBase

from .base import PyRefBase


__all__ = [
    "AnyRef",
]


class AnyRef(PyRefBase[object], AnyRefBase):
    """Concrete any ref for Python memory storage.

    Inherits:
    - PyRefBase: source storage, get() implementation
    - AnyRefBase: numeric/comparison/logical/bitwise traits
    """

    pass
