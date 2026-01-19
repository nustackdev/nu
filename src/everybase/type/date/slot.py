"""Date slot."""

from __future__ import annotations

from everyterm.shape import Shape, Slot
from everyterm.term import Ref

from .ref import DateRef


__all__ = [
    "DateSlot",
]


class _DateSlot(Slot):
    """Slot implementation for date values."""

    def __init__(self) -> None:
        super().__init__()
        self.value_type = str  # Stored as ISO string

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> DateRef:
        return DateRef(
            address=self.name,
            value_type=self.value_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )


def DateSlot() -> DateRef:  # noqa: N802
    """Create a slot for date values."""
    return _DateSlot()  # type: ignore[return-value]
