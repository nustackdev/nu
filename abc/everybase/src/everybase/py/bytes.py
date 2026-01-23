"""Python memory bytes ref.

BytesRef = PyRefBase + BytesRefBase
"""

from __future__ import annotations

from everybase.refs import BytesRefBase

from .base import PyRefBase


__all__ = [
    "BytesRef",
]


class BytesRef(PyRefBase[bytes], BytesRefBase):
    """Concrete bytes ref for Python memory storage.

    Inherits:
    - PyRefBase: source storage, get() implementation
    - BytesRefBase: bytes operations, comparison, logical traits
    """

    pass
