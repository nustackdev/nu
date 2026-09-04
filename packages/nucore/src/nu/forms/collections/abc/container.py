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
    """Base for values that support containment checks, like collections.abc.Container.

    Notes:
        - Python's `in` operator coerces `__contains__`'s result to `bool` at
          the C level, which would collapse the Nu tree to a constant `True`.
          `.contains(item)` returns a real Bool tree node instead.

    Example:
        >>> nu.run(nu.Set({1, 2, 3}).contains(2))[0]
        True
    """

    def contains(self, item: object) -> Bool:
        """Whether item is a member of self.

        Args:
            item: the value to test for membership.

        Yields:
            True when item is in self, False otherwise. INVALID when self or
            item is a sentinel.

        Example:
            >>> nu.run(nu.Set({1, 2, 3}).contains(2))[0]
            True

            >>> nu.run(nu.Set({1, 2, 3}).contains(9))[0]
            False
        """
        from nu.core import Contains
        from nu.forms.primitives import Bool

        return Bool(Contains(self, item))
