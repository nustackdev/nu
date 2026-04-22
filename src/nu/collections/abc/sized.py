"""Sized capability.

SizedI: values that have a length.

Follows Python's collections.abc.Sized pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import Interface


if TYPE_CHECKING:
    from nu.primitives import IntI


__all__ = [
    "SizedI",
]


class SizedI(Interface):
    """Base for values that have a length - like collections.abc.Sized."""

    def len(self) -> IntI:
        """Length of this collection."""
        from nu.ops import LenOp
        from nu.primitives import IntI

        return IntI(LenOp(self))
