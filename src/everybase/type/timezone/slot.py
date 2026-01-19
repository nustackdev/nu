"""Timezone slot."""

from __future__ import annotations

from everyterm.shape import Shape, Slot
from everyterm.term import Ref

from .ref import TimezoneRef


__all__ = [
    "TimezoneSlot",
]


class _TimezoneSlot(Slot):
    """Slot implementation for timezone values."""

    def __init__(self) -> None:
        super().__init__()
        self.value_type = float  # Stored as offset seconds from UTC

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> TimezoneRef:
        return TimezoneRef(
            address=self.name,
            value_type=self.value_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )


def TimezoneSlot() -> TimezoneRef:  # noqa: N802
    """Create a slot for timezone values."""
    return _TimezoneSlot()  # type: ignore[return-value]
