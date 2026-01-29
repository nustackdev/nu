"""Python memory none ref.

NoneRef = PyRefBase + NoneRefBase
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase.refs import NoneRefBase

from .base import PyRefBase


if TYPE_CHECKING:
    from everyabc import Sentinel, Term


__all__ = [
    "NoneRef",
]


class NoneRef(PyRefBase[None], NoneRefBase):
    """Concrete none ref for Python memory storage.

    Inherits:
    - PyRefBase: source storage, get() implementation
    - NoneRefBase: logical traits
    """

    def __init__(self, source: None | Term[None] | Sentinel = None) -> None:
        """Initialize with None as default source."""
        super().__init__(source if source is not None else None)
