"""Percentage slot."""

from __future__ import annotations

from term.shape import Shape, Slot

from every._abc import Ref

from .ref import PercentageRef


__all__ = [
    "PercentageSlot",
]


class _PercentageSlot(Slot):
    """Slot for Percentage values."""

    def __init__(self) -> None:
        super().__init__()
        self.value_type = float

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> PercentageRef:
        return PercentageRef(
            address=self.name,
            value_type=self.value_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )


def PercentageSlot() -> PercentageRef:  # noqa: N802
    """Create slot for percentage values.

    Stored as float.

    Example:
        class Progress(Shape):
            completion = PercentageSlot()
    """
    return _PercentageSlot()  # type: ignore[return-value]
