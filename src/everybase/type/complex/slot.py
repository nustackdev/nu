"""Complex slot."""

from __future__ import annotations

from everyterm.shape import Shape, Slot
from everyterm.term import Ref

from .ref import ComplexRef


__all__ = [
    "ComplexSlot",
]


class _ComplexSlot(Slot):
    """Slot implementation for complex values."""

    def __init__(self) -> None:
        super().__init__()
        self.value_type = str  # Stored as "real,imag"

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> ComplexRef:
        """Create ComplexRef for this slot."""
        return ComplexRef(
            address=self.name,
            value_type=self.value_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )


def ComplexSlot() -> ComplexRef:  # noqa: N802
    """Create a slot for complex values.

    Complex numbers are stored as "real,imag" strings and
    automatically converted to/from Python complex objects.

    Returns:
        ComplexRef slot.

    Example:
        class Signal(Shape):
            amplitude = ComplexSlot()
            phase = ComplexSlot()
    """
    return _ComplexSlot()  # type: ignore[return-value]
