"""Sized capability.

SizedSurface: values that have a length.

Follows Python's collections.abc.Sized pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Surface


if TYPE_CHECKING:
    from nu.forms import Int


__all__ = [
    "SizedSurface",
]


class SizedSurface(Surface):
    """Base for values that have a length, like collections.abc.Sized.

    Example:
        >>> nu.run(nu.List([1, 2, 3]).len())[0]
        3
    """

    def len(self) -> Int:
        """Length of self.

        Yields:
            The element count as Int.

        Example:
            >>> nu.run(nu.List([1, 2, 3]).len())[0]
            3
        """
        from nu.core import Len
        from nu.forms import Int

        return Int(Len(self))
