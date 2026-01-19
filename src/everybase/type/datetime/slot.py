"""Datetime slot."""

from __future__ import annotations

from everyterm.shape import Shape, Slot
from everyterm.term import Ref

from .ref import DatetimeRef


__all__ = [
    "DatetimeSlot",
]


class _DatetimeSlot(Slot):
    """Slot implementation for datetime values."""

    def __init__(self) -> None:
        super().__init__()
        self.value_type = str  # Stored as ISO string

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> DatetimeRef:
        return DatetimeRef(
            address=self.name,
            value_type=self.value_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )


def DatetimeSlot() -> DatetimeRef:  # noqa: N802
    """Create a slot for datetime values."""
    return _DatetimeSlot()  # type: ignore[return-value]
