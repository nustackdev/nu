"""Concrete PV item ref implementations.

Item refs combine ReactiveItemRef (everyshape document model) with
PrimitiveRef (PV substrate) for CRUD + observation on PV storage.

Typed refs (IntRef, StrRef, etc.) combine ItemRef behavior with
everybase type operators for a rich interface.

Pattern:
    class ItemRef(ReactiveItemRef[T, ValueT], PrimitiveRef[T]):
        # Document model (CRUD + observe) + PV substrate

    class IntRef(ItemRef[int, IntValue], IntType):
        # PV item + int operators
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from everybase.abc import (
    BoolType,
    BoolValue,
    BytesType,
    BytesValue,
    FloatType,
    FloatValue,
    IntType,
    IntValue,
    StrType,
    StrValue,
)
from everybase.shape import ReactiveItemRef, Slot

from .base import PrimitiveRef


if TYPE_CHECKING:
    from virtuals.loc import path

    from everybase import Term, Value
    from everybase.shape import Shape


__all__ = [
    "BoolRef",
    "BytesRef",
    "FloatRef",
    "IntRef",
    "ItemRef",
    "StrRef",
]


# =============================================================================
# ITEM REFS (document model + PV substrate)
# =============================================================================


class ItemRef[T, ValueT: Value](
    ReactiveItemRef[T, ValueT],
    PrimitiveRef[T],
):
    """PV item reference for primitive values.

    Combines everyshape document model (CRUD + observation) with
    PV substrate (path resolution, view navigation).
    """

    def __init__(
        self,
        *,
        value_value_type: type[ValueT],
        **kwargs: object,
    ) -> None:
        """Initialize item reference."""
        super().__init__(**kwargs)
        self._value_value_type = value_value_type

    @classmethod
    def slot(
        cls,
        value_type: type[T],
        value_value_type: type[ValueT],
    ) -> Self:
        """Create a slot for this item ref type.

        Args:
            value_type: Python type of the value (int, str, float, etc.)
            value_value_type: Value type for serialization

        Returns:
            Slot configured to create ItemRef instances
        """
        return Slot(cls, value_type=value_type, value_value_type=value_value_type)  # type: ignore


# =============================================================================
# TYPED REFS (with everybase interface)
# =============================================================================


class IntRef(ItemRef[int, IntValue], IntType):
    """PV integer reference with full numeric interface.

    Inherits:
        - ItemRef: PV storage access + CRUD + observation
        - IntType: Arithmetic, comparison, bitwise, logical operators
    """

    def __init__(
        self,
        *,
        address: path.PathAddress | Term,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV int ref."""
        super().__init__(
            address=address,
            value_type=int,
            value_value_type=IntValue,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for int values."""
        return Slot(cls)  # type: ignore[return-value]


class StrRef(ItemRef[str, StrValue], StrType):
    """PV string reference with full string interface.

    Inherits:
        - ItemRef: PV storage access + CRUD + observation
        - StrType: String methods (upper, lower, split, etc.), concatenation
    """

    def __init__(
        self,
        *,
        address: path.PathAddress | Term,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV str ref."""
        super().__init__(
            address=address,
            value_type=str,
            value_value_type=StrValue,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for str values."""
        return Slot(cls)  # type: ignore[return-value]


class FloatRef(ItemRef[float, FloatValue], FloatType):
    """PV float reference with full numeric interface.

    Inherits:
        - ItemRef: PV storage access + CRUD + observation
        - FloatType: Arithmetic, comparison, logical operators
    """

    def __init__(
        self,
        *,
        address: path.PathAddress | Term,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV float ref."""
        super().__init__(
            address=address,
            value_type=float,
            value_value_type=FloatValue,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for float values."""
        return Slot(cls)  # type: ignore[return-value]


class BoolRef(ItemRef[bool, BoolValue], BoolType):
    """PV boolean reference with full logical interface.

    Inherits:
        - ItemRef: PV storage access + CRUD + observation
        - BoolType: Logical operators (and_, or_, not_)
    """

    def __init__(
        self,
        *,
        address: path.PathAddress | Term,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV bool ref."""
        super().__init__(
            address=address,
            value_type=bool,
            value_value_type=BoolValue,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for bool values."""
        return Slot(cls)  # type: ignore[return-value]


class BytesRef(ItemRef[bytes, BytesValue], BytesType):
    """PV bytes reference with full bytes interface.

    Inherits:
        - ItemRef: PV storage access + CRUD + observation
        - BytesType: Bytes methods (decode, hex, etc.)
    """

    def __init__(
        self,
        *,
        address: path.PathAddress | Term,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV bytes ref."""
        super().__init__(
            address=address,
            value_type=bytes,
            value_value_type=BytesValue,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for bytes values."""
        return Slot(cls)  # type: ignore[return-value]
