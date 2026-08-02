"""Container capability.

ContainerForm: values that support containment checks.

Follows Python's collections.abc.Container pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Form


if TYPE_CHECKING:
    from nu.forms.primitives import Bool


__all__ = [
    "ContainerForm",
]


class ContainerForm(Form):
    """Base for values that support containment checks - like collections.abc.Container.

    Note: Python's ``in`` operator coerces the result of ``__contains__`` to
    ``bool`` at the C level, which would discard the Nu tree and yield a
    constant ``True`` for any Form instance. We expose ``.contains(item)``
    instead, returning a real ``Bool`` tree node.
    """

    def contains(self, item: object) -> Bool:
        """Check if item is in this collection. Returns a Bool tree."""
        from nu.core import Contains
        from nu.forms.primitives import Bool

        return Bool(Contains(self, item))
