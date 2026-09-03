"""Sized capability.

SizedForm: values that have a length.

Follows Python's collections.abc.Sized pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Form


if TYPE_CHECKING:
    from nu.forms.primitives import Int


__all__ = [
    "SizedForm",
]


class SizedForm(Form):
    """Base for values that have a length, like collections.abc.Sized.

    Example:
        >>> nu.run(nu.List([1, 2, 3]).len())[0]
        3
    """

    def len(self) -> Int:
        """Length of self.

        Yields:
            The element count as Int. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.List([1, 2, 3]).len())[0]
            3
        """
        from nu.core import Len
        from nu.forms.primitives import Int

        return Int(Len(self))
