"""Attribute access ops.

GetAttrOp: Get an attribute from an instance
SetAttrOp: Set an attribute on an instance
DelAttrOp: Delete an attribute from an instance
"""

from __future__ import annotations

from nu.terms import BinaryOp, TernaryOp


__all__ = [
    "DelAttrOp",
    "GetAttrOp",
    "SetAttrOp",
]


# =============================================================================
# ATTRIBUTE ACCESS
# =============================================================================


class GetAttrOp[ResultT](BinaryOp[ResultT]):
    """Get an attribute from an instance.

    Both instance and attr_name can be Terms for dynamic attribute access.

    Example:
        >>> GetAttrOp(datetime_value, "year")
        >>> GetAttrOp(obj, attr_name_term)  # dynamic attribute
    """

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return getattr(left, str(right))


class SetAttrOp(TernaryOp[None]):
    """Set an attribute on an instance.

    All arguments can be Terms for dynamic attribute setting.
    Mutates state.

    Example:
        >>> SetAttrOp(obj, "name", "value")
    """

    def apply(self, first: object, second: object, third: object) -> None:
        """Apply."""
        setattr(first, str(second), third)


class DelAttrOp(BinaryOp[None]):
    """Delete an attribute from an instance.

    Both instance and attr_name can be Terms for dynamic attribute deletion.
    Mutates state.

    Example:
        >>> DelAttrOp(obj, "cached_value")
    """

    def apply(self, left: object, right: object) -> None:
        """Apply."""
        delattr(left, str(right))
