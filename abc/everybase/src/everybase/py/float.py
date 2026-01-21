"""Python memory float ref.

FloatRef = PyRefBase + FloatRefBase
"""

from __future__ import annotations

from everybase.refs import FloatRefBase

from .base import PyRefBase


__all__ = [
    "FloatRef",
]


class FloatRef(PyRefBase[float], FloatRefBase):
    """Concrete float ref for Python memory storage.

    Inherits:
    - PyRefBase: source storage, get() implementation
    - FloatRefBase: numeric/comparison/logical traits
    """

    pass
