"""Time slot."""

from __future__ import annotations

from everyterm.shape import Shape, Slot
from everyterm.term import Ref

from .ref import TimeRef


__all__ = [
    "TimeSlot",
]


class _TimeSlot(Slot):
    """Slot implementation for time values."""

    def __init__(self) -> None:
        super().__init__()
        self.value_type = str  # Stored as ISO string

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> TimeRef:
        return TimeRef(
            address=self.name,
            value_type=self.value_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )


def TimeSlot() -> TimeRef:  # noqa: N802
    """Create a slot for time values."""
    return _TimeSlot()  # type: ignore[return-value]
