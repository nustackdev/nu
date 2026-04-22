"""Attribute access ops.

GetAttr: Get an attribute from an instance
SetAttr: Set an attribute on an instance
DelAttr: Delete an attribute from an instance
"""

from __future__ import annotations

from nu.terms import BinaryScalar, TernaryScalar


__all__ = [
    "DelAttr",
    "GetAttr",
    "SetAttr",
]


# =============================================================================
# ATTRIBUTE ACCESS
# =============================================================================


class GetAttr[ResultT](BinaryScalar[ResultT]):
    """Get an attribute from an instance.

    Both instance and attr_name can be Terms for dynamic attribute access.

    Example:
        >>> GetAttr(datetime_value, "year")
        >>> GetAttr(obj, attr_name_term)  # dynamic attribute
    """

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return getattr(left, str(right))


class SetAttr(TernaryScalar[None]):
    """Set an attribute on an instance.

    All arguments can be Terms for dynamic attribute setting.
    Mutates state.

    Example:
        >>> SetAttr(obj, "name", "value")
    """

    def apply(self, first: object, second: object, third: object) -> None:
        """Apply."""
        setattr(first, str(second), third)


class DelAttr(BinaryScalar[None]):
    """Delete an attribute from an instance.

    Both instance and attr_name can be Terms for dynamic attribute deletion.
    Mutates state.

    Example:
        >>> DelAttr(obj, "cached_value")
    """

    def apply(self, left: object, right: object) -> None:
        """Apply."""
        delattr(left, str(right))
