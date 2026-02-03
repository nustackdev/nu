"""Concrete PV primitive ref implementations.

Typed leaf refs combine PrimitiveRef (PV substrate) with everybase
type operators (IntType, StrType, etc.).

Item refs combine ReactiveItemRef (everyshape document model) with
PrimitiveRef (PV substrate) for CRUD + observation on PV storage.

Pattern:
    class IntRef(PrimitiveRef[int], IntType):
        # PV substrate + int operators

    class ItemRef(ReactiveItemRef[T, ValueT], PrimitiveRef[T]):
        # Document model (CRUD + observe) + PV substrate
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from everybase.types import (
    BoolType,
    BytesType,
    FloatType,
    IntType,
    StrType,
)
from everyshape import ReactiveItemRef, Slot

from .base import PrimitiveRef


if TYPE_CHECKING:
    from pv.loc import path

    from everyabc import Term, Value
    from everyshape import Shape


__all__ = [
    "BoolRef",
    "BytesRef",
    "DictItemRef",
    "FloatRef",
    "IntRef",
    "ItemRef",
    "ListItemRef",
    "StrRef",
]


# =============================================================================
# PRIMITIVE REFS (with everybase interface)
# =============================================================================


class IntRef(PrimitiveRef[int], IntType):
    """PV integer reference with full numeric interface.

    Inherits:
        - PrimitiveRef: PV storage access via fetch()
        - IntType: Arithmetic, comparison, bitwise, logical operators
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV int ref."""
        super().__init__(address, int, parent, owner_shape)

    @classmethod
    def slot(cls) -> Self:
        """Create a slot for int values."""
        return Slot(cls)  # type: ignore[return-value]


class StrRef(PrimitiveRef[str], StrType):
    """PV string reference with full string interface.

    Inherits:
        - PrimitiveRef: PV storage access via fetch()
        - StrType: String methods (upper, lower, split, etc.), concatenation
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV str ref."""
        super().__init__(address, str, parent, owner_shape)

    @classmethod
    def slot(cls) -> Self:
        """Create a slot for str values."""
        return Slot(cls)  # type: ignore[return-value]


class FloatRef(PrimitiveRef[float], FloatType):
    """PV float reference with full numeric interface.

    Inherits:
        - PrimitiveRef: PV storage access via fetch()
        - FloatType: Arithmetic, comparison, logical operators
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV float ref."""
        super().__init__(address, float, parent, owner_shape)

    @classmethod
    def slot(cls) -> Self:
        """Create a slot for float values."""
        return Slot(cls)  # type: ignore[return-value]


class BoolRef(PrimitiveRef[bool], BoolType):
    """PV boolean reference with full logical interface.

    Inherits:
        - PrimitiveRef: PV storage access via fetch()
        - BoolType: Logical operators (and_, or_, not_)
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV bool ref."""
        super().__init__(address, bool, parent, owner_shape)

    @classmethod
    def slot(cls) -> Self:
        """Create a slot for bool values."""
        return Slot(cls)  # type: ignore[return-value]


class BytesRef(PrimitiveRef[bytes], BytesType):
    """PV bytes reference with full bytes interface.

    Inherits:
        - PrimitiveRef: PV storage access via fetch()
        - BytesType: Bytes methods (decode, hex, etc.)
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV bytes ref."""
        super().__init__(address, bytes, parent, owner_shape)

    @classmethod
    def slot(cls) -> Self:
        """Create a slot for bytes values."""
        return Slot(cls)  # type: ignore[return-value]


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
        address: path.PathAddress | Term,
        value_type: type[T],
        value_value_type: type[ValueT],
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize item reference."""
        super().__init__(address, value_type, parent, owner_shape)
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


class ListItemRef[T, ValueT: Value](
    ReactiveItemRef[T, ValueT],
    PrimitiveRef[T],
):
    """PV list item reference for items in a list.

    Same capabilities as ItemRef - the distinction is semantic
    for type clarity when building refs for sequence items.
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        value_type: type[T],
        value_value_type: type[ValueT],
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize list item reference."""
        super().__init__(address, value_type, parent, owner_shape)
        self._value_value_type = value_value_type

    @classmethod
    def slot(
        cls,
        value_type: type[T],
        value_value_type: type[ValueT],
    ) -> Self:
        """Create a slot for this list item ref type.

        Args:
            value_type: Python type of the value
            value_value_type: Value type for serialization

        Returns:
            Slot configured to create ListItemRef instances
        """
        return Slot(cls, value_type=value_type, value_value_type=value_value_type)  # type: ignore


class DictItemRef[T, ValueT: Value](
    ReactiveItemRef[T, ValueT],
    PrimitiveRef[T],
):
    """PV dict item reference for items in a mapping.

    Same capabilities as ItemRef - the distinction is semantic
    for type clarity when building refs for mapping values.
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        value_type: type[T],
        value_value_type: type[ValueT],
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize dict item reference."""
        super().__init__(address, value_type, parent, owner_shape)
        self._value_value_type = value_value_type

    @classmethod
    def slot(
        cls,
        value_type: type[T],
        value_value_type: type[ValueT],
    ) -> Self:
        """Create a slot for this dict item ref type.

        Args:
            value_type: Python type of the value
            value_value_type: Value type for serialization

        Returns:
            Slot configured to create DictItemRef instances
        """
        return Slot(cls, value_type=value_type, value_value_type=value_value_type)  # type: ignore
