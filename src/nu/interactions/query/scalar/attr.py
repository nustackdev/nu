"""Attribute access ops.

GetAttr: Get an attribute from an instance
SetAttr: Set an attribute on an instance
DelAttr: Delete an attribute from an instance
"""

from __future__ import annotations

from typing import ClassVar

from nu.terms import BinaryQuery, Mode, TernaryQuery


__all__ = [
    "DelAttr",
    "GetAttr",
    "SetAttr",
]


# =============================================================================
# ATTRIBUTE ACCESS
# =============================================================================


class GetAttr[ResultT](BinaryQuery[ResultT]):
    """Get an attribute from an instance.

    Both instance and attr_name can be Terms for dynamic attribute access.

    Example:
        >>> GetAttr(datetime_value, "year")
        >>> GetAttr(obj, attr_name_term)  # dynamic attribute
    """

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return getattr(left, str(right))


class SetAttr(TernaryQuery[None]):
    """Set an attribute on an instance.

    All arguments can be Terms for dynamic attribute setting.
    Mutates state.

    Example:
        >>> SetAttr(obj, "name", "value")
    """

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, first: object, second: object, third: object) -> None:
        """Apply."""
        setattr(first, str(second), third)


class DelAttr(BinaryQuery[None]):
    """Delete an attribute from an instance.

    Both instance and attr_name can be Terms for dynamic attribute deletion.
    Mutates state.

    Example:
        >>> DelAttr(obj, "cached_value")
    """

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: object, right: object) -> None:
        """Apply."""
        delattr(left, str(right))
