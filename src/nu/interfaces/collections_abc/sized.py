"""Sized capability - protocol + base.

SizedProtocol/Base: values that have a length.

Follows Python's collections.abc.Sized pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable


if TYPE_CHECKING:
    from nu.interfaces.primitives import IntI


__all__ = [
    "SizedBase",
    "SizedProtocol",
]


@runtime_checkable
class SizedProtocol(Protocol):
    """Protocol for values that have a length - like collections.abc.Sized."""

    def len(self) -> IntI:
        """Length of this collection."""
        ...


class SizedBase:
    """Base for values that have a length - like collections.abc.Sized."""

    def len(self) -> IntI:
        """Length of this collection."""
        from nu.interfaces.primitives import IntI
        from nu.ops.access import LenOp

        return IntI(LenOp(self))
