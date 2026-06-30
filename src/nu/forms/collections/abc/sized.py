"""Sized capability.

SizedForm: values that have a length.

Follows Python's collections.abc.Sized pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Form


if TYPE_CHECKING:
    from nu.forms.primitives import IntForm


__all__ = [
    "SizedForm",
]


class SizedForm(Form):
    """Base for values that have a length - like collections.abc.Sized."""

    def len(self) -> IntForm:
        """Length of this collection."""
        from nu.core import LenQuery
        from nu.forms.primitives import IntForm

        return IntForm(LenQuery(self))
