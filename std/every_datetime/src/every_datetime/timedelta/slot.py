"""Timedelta slot."""

from __future__ import annotations

from term.shape import Shape, Slot

from every._abc import Ref

from .ref import TimedeltaRef


__all__ = [
    "TimedeltaSlot",
]


class _TimedeltaSlot(Slot):
    """Slot implementation for timedelta values."""

    def __init__(self) -> None:
        super().__init__()
        self.value_type = float  # Stored as total seconds

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> TimedeltaRef:
        return TimedeltaRef(
            address=self.name,
            value_type=self.value_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )


def TimedeltaSlot() -> TimedeltaRef:  # noqa: N802
    """Create a slot for timedelta values."""
    return _TimedeltaSlot()  # type: ignore[return-value]
