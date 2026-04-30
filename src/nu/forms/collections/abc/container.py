"""Container capability.

ContainerForm: values that support containment checks.

Follows Python's collections.abc.Container pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import Form


if TYPE_CHECKING:
    from nu.forms.primitives import BoolForm


__all__ = [
    "ContainerForm",
]


class ContainerForm(Form):
    """Base for values that support containment checks - like collections.abc.Container."""

    def __contains__(self, item: object) -> BoolForm:
        """Check if item is in this collection."""
        from nu import Contains
        from nu.forms.primitives import BoolForm

        return BoolForm(Contains(self, item))
