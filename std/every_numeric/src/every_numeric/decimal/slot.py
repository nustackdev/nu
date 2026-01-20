"""Decimal slot."""

from __future__ import annotations

from term.shape import Shape, Slot

from every._abc import Ref

from .ref import DecimalRef


__all__ = [
    "DecimalSlot",
]


class _DecimalSlot(Slot):
    """Slot implementation for Decimal values."""

    def __init__(self) -> None:
        super().__init__()
        self.value_type = str  # Stored as string for exact representation

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> DecimalRef:
        return DecimalRef(
            address=self.name,
            value_type=self.value_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )


def DecimalSlot() -> DecimalRef:  # noqa: N802
    """Create a slot for Decimal values."""
    return _DecimalSlot()  # type: ignore[return-value]
