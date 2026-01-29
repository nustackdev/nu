"""Slot definitions for standard library types in PV storage.

These slots create PV refs for Shape fields.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyabc import Slot

from .refs import (
    PVBasisPointRef,
    PVComplexRef,
    PVDateRef,
    PVDatetimeRef,
    PVDecimalRef,
    PVFractionRef,
    PVPathRef,
    PVPercentageRef,
    PVTimedeltaRef,
    PVTimeRef,
    PVTimezoneRef,
    PVUUIDRef,
)


if TYPE_CHECKING:
    from everyabc import Ref, Shape


__all__ = [
    "BasisPointSlot",
    "ComplexSlot",
    # Datetime
    "DateSlot",
    "DatetimeSlot",
    # Numeric
    "DecimalSlot",
    "FractionSlot",
    # Path and UUID
    "PathSlot",
    "PercentageSlot",
    "TimeSlot",
    "TimedeltaSlot",
    "TimezoneSlot",
    "UUIDSlot",
]


# =============================================================================
# NUMERIC SLOTS
# =============================================================================


class _DecimalSlot(Slot):
    """Slot for Decimal values."""

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> PVDecimalRef:
        return PVDecimalRef(
            address=self.name,
            parent=parent_ref,
            shape=owner_shape,
        )


def DecimalSlot() -> PVDecimalRef:  # noqa: N802
    """Create a slot for Decimal values."""
    return _DecimalSlot()  # type: ignore


class _FractionSlot(Slot):
    """Slot for Fraction values."""

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> PVFractionRef:
        return PVFractionRef(
            address=self.name,
            parent=parent_ref,
            shape=owner_shape,
        )


def FractionSlot() -> PVFractionRef:  # noqa: N802
    """Create a slot for Fraction values."""
    return _FractionSlot()  # type: ignore


class _ComplexSlot(Slot):
    """Slot for complex values."""

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> PVComplexRef:
        return PVComplexRef(
            address=self.name,
            parent=parent_ref,
            shape=owner_shape,
        )


def ComplexSlot() -> PVComplexRef:  # noqa: N802
    """Create a slot for complex values."""
    return _ComplexSlot()  # type: ignore


class _BasisPointSlot(Slot):
    """Slot for BasisPoint values."""

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> PVBasisPointRef:
        return PVBasisPointRef(
            address=self.name,
            parent=parent_ref,
            shape=owner_shape,
        )


def BasisPointSlot() -> PVBasisPointRef:  # noqa: N802
    """Create a slot for BasisPoint values."""
    return _BasisPointSlot()  # type: ignore


class _PercentageSlot(Slot):
    """Slot for Percentage values."""

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> PVPercentageRef:
        return PVPercentageRef(
            address=self.name,
            parent=parent_ref,
            shape=owner_shape,
        )


def PercentageSlot() -> PVPercentageRef:  # noqa: N802
    """Create a slot for Percentage values."""
    return _PercentageSlot()  # type: ignore


# =============================================================================
# DATETIME SLOTS
# =============================================================================


class _DateSlot(Slot):
    """Slot for date values."""

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> PVDateRef:
        return PVDateRef(
            address=self.name,
            parent=parent_ref,
            shape=owner_shape,
        )


def DateSlot() -> PVDateRef:  # noqa: N802
    """Create a slot for date values."""
    return _DateSlot()  # type: ignore


class _DatetimeSlot(Slot):
    """Slot for datetime values."""

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> PVDatetimeRef:
        return PVDatetimeRef(
            address=self.name,
            parent=parent_ref,
            shape=owner_shape,
        )


def DatetimeSlot() -> PVDatetimeRef:  # noqa: N802
    """Create a slot for datetime values."""
    return _DatetimeSlot()  # type: ignore


class _TimeSlot(Slot):
    """Slot for time values."""

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> PVTimeRef:
        return PVTimeRef(
            address=self.name,
            parent=parent_ref,
            shape=owner_shape,
        )


def TimeSlot() -> PVTimeRef:  # noqa: N802
    """Create a slot for time values."""
    return _TimeSlot()  # type: ignore


class _TimedeltaSlot(Slot):
    """Slot for timedelta values."""

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> PVTimedeltaRef:
        return PVTimedeltaRef(
            address=self.name,
            parent=parent_ref,
            shape=owner_shape,
        )


def TimedeltaSlot() -> PVTimedeltaRef:  # noqa: N802
    """Create a slot for timedelta values."""
    return _TimedeltaSlot()  # type: ignore


class _TimezoneSlot(Slot):
    """Slot for timezone values."""

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> PVTimezoneRef:
        return PVTimezoneRef(
            address=self.name,
            parent=parent_ref,
            shape=owner_shape,
        )


def TimezoneSlot() -> PVTimezoneRef:  # noqa: N802
    """Create a slot for timezone values."""
    return _TimezoneSlot()  # type: ignore


# =============================================================================
# PATH AND UUID SLOTS
# =============================================================================


class _PathSlot(Slot):
    """Slot for Path values."""

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> PVPathRef:
        return PVPathRef(
            address=self.name,
            parent=parent_ref,
            shape=owner_shape,
        )


def PathSlot() -> PVPathRef:  # noqa: N802
    """Create a slot for Path values."""
    return _PathSlot()  # type: ignore


class _UUIDSlot(Slot):
    """Slot for UUID values."""

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> PVUUIDRef:
        return PVUUIDRef(
            address=self.name,
            parent=parent_ref,
            shape=owner_shape,
        )


def UUIDSlot() -> PVUUIDRef:  # noqa: N802
    """Create a slot for UUID values."""
    return _UUIDSlot()  # type: ignore
