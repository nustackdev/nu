"""Path slot."""

from __future__ import annotations

from everyterm.shape import Shape, Slot
from everyterm.term import Ref

from .ref import PathRef


__all__ = [
    "PathSlot",
]


class _PathSlot(Slot):
    """Slot implementation for Path values."""

    def __init__(self) -> None:
        super().__init__()
        self.value_type = str  # Stored as string

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> PathRef:
        return PathRef(
            address=self.name,
            value_type=self.value_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )


def PathSlot() -> PathRef:  # noqa: N802
    """Create a slot for Path values."""
    return _PathSlot()  # type: ignore[return-value]
