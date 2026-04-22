"""Container capability.

ContainerI: values that support containment checks.

Follows Python's collections.abc.Container pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import Interface


if TYPE_CHECKING:
    from nu.primitives import BoolI


__all__ = [
    "ContainerI",
]


class ContainerI(Interface):
    """Base for values that support containment checks - like collections.abc.Container."""

    def __contains__(self, item: object) -> BoolI:
        """Check if item is in this collection."""
        from nu.interactions import Contains
        from nu.primitives import BoolI

        return BoolI(Contains(self, item))
