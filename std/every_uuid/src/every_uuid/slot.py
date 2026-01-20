"""UUID slot."""

from __future__ import annotations

from term.shape import Shape, Slot

from every._abc import Ref

from .ref import UUIDRef


__all__ = [
    "UUIDSlot",
]


class _UUIDSlot(Slot):
    """Slot implementation for UUID values."""

    def __init__(self) -> None:
        super().__init__()
        self.value_type = str  # Stored as string

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> UUIDRef:
        return UUIDRef(
            address=self.name,
            value_type=self.value_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )


def UUIDSlot() -> UUIDRef:  # noqa: N802
    """Create a slot for UUID values."""
    return _UUIDSlot()  # type: ignore[return-value]
