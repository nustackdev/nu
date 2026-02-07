"""Dict substrate item refs — typed value holders in nested dicts.

ItemRef combines MutableItemRef (eb_shape CRUD) with RefBase
(dict navigation). No reactivity.

Typed refs (IntRef, StrRef, etc.) combine ItemRef behavior with
everybase type operators for a rich interface.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from eb_shape import MutableItemRef, Slot
from everybase import Value
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

from .base import RefBase


if TYPE_CHECKING:
    from eb_shape import Shape
    from everybase import Term


__all__ = [
    "BoolRef",
    "BytesRef",
    "FloatRef",
    "IntRef",
    "ItemRef",
    "StrRef",
]


class ItemRef[T, ValueT: Value](
    MutableItemRef[T, ValueT],
    RefBase[T],
):
    """Dict item reference for values in nested dicts.

    Combines eb_shape document model (get/set/delete/exists)
    with dict substrate (plain dict navigation).
    """

    def __init__(
        self,
        address: str | int | Term,
        value_type: type[T],
        value_value_type: type[ValueT],
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize item reference."""
        super().__init__(address, parent, owner_shape)
        self._value_type = value_type
        self._value_value_type = value_value_type

    @classmethod
    def slot(cls, value_type: type[T], value_value_type: type[ValueT]) -> Self:
        """Create a slot for this item ref type.

        Args:
            value_type: Python type of the value (int, str, float, etc.)
            value_value_type: Value wrapper type (IntValue, StrValue, etc.)

        Returns:
            Slot that creates ItemRef instances.
        """
        return Slot(cls, value_type=value_type, value_value_type=value_value_type)  # type: ignore[return-value]


# =============================================================================
# TYPED REFS (with everybase interface)
# =============================================================================


class IntRef(ItemRef[int, IntValue], IntType):
    """Dict integer reference with full numeric interface.

    Inherits:
        - ItemRef: Dict substrate access + CRUD
        - IntType: Arithmetic, comparison, bitwise, logical operators
    """

    def __init__(
        self,
        address: str | int | Term,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize dict int ref."""
        super().__init__(address, int, IntValue, parent, owner_shape)

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for int values."""
        return Slot(cls)  # type: ignore[return-value]


class StrRef(ItemRef[str, StrValue], StrType):
    """Dict string reference with full string interface.

    Inherits:
        - ItemRef: Dict substrate access + CRUD
        - StrType: String methods (upper, lower, split, etc.), concatenation
    """

    def __init__(
        self,
        address: str | int | Term,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize dict str ref."""
        super().__init__(address, str, StrValue, parent, owner_shape)

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for str values."""
        return Slot(cls)  # type: ignore[return-value]


class FloatRef(ItemRef[float, FloatValue], FloatType):
    """Dict float reference with full numeric interface.

    Inherits:
        - ItemRef: Dict substrate access + CRUD
        - FloatType: Arithmetic, comparison, logical operators
    """

    def __init__(
        self,
        address: str | int | Term,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize dict float ref."""
        super().__init__(address, float, FloatValue, parent, owner_shape)

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for float values."""
        return Slot(cls)  # type: ignore[return-value]


class BoolRef(ItemRef[bool, BoolValue], BoolType):
    """Dict boolean reference with full logical interface.

    Inherits:
        - ItemRef: Dict substrate access + CRUD
        - BoolType: Logical operators (and_, or_, not_)
    """

    def __init__(
        self,
        address: str | int | Term,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize dict bool ref."""
        super().__init__(address, bool, BoolValue, parent, owner_shape)

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for bool values."""
        return Slot(cls)  # type: ignore[return-value]


class BytesRef(ItemRef[bytes, BytesValue], BytesType):
    """Dict bytes reference with full bytes interface.

    Inherits:
        - ItemRef: Dict substrate access + CRUD
        - BytesType: Bytes methods (decode, hex, etc.)
    """

    def __init__(
        self,
        address: str | int | Term,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize dict bytes ref."""
        super().__init__(address, bytes, BytesValue, parent, owner_shape)

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for bytes values."""
        return Slot(cls)  # type: ignore[return-value]
