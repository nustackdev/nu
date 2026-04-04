"""Container capability - protocol + base.

ContainerProtocol/Base: values that support containment checks.

Follows Python's collections.abc.Container pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable


if TYPE_CHECKING:
    from nu.interfaces.primitives import BoolI


__all__ = [
    "ContainerBase",
    "ContainerProtocol",
]


@runtime_checkable
class ContainerProtocol(Protocol):
    """Protocol for values that support containment checks - like collections.abc.Container."""

    def __contains__(self, item: object) -> BoolI: ...


class ContainerBase:
    """Base for values that support containment checks - like collections.abc.Container."""

    def __contains__(self, item: object) -> BoolI:
        """Check if item is in this collection."""
        from nu.interfaces.primitives import BoolI
        from nu.ops.access import ContainsOp

        return BoolI(ContainsOp(self, item))
