"""Concrete PV item ref implementations.

Item refs combine ReactiveItemRef (everyshape document model) with
PrimitiveRef (PV substrate) for CRUD + observation on PV storage.

Typed refs (IntRef, StrRef, etc.) combine ItemRef behavior with
everybase type operators for a rich interface.

Pattern:
    class ItemRef(ReactiveItemRef[T, ValueT], PrimitiveRef[T]):
        # Document model (CRUD + observe) + PV substrate

    class IntRef(ItemRef[int, IntI], IntI):
        # PV item + int operators
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from nu import (
    BoolI,
    BytesI,
    DictI,
    FloatI,
    IntI,
    ListI,
    SetI,
    StrI,
)
from nu.shapes import ReactiveItemRef, Slot

from .base import PrimitiveRef


if TYPE_CHECKING:
    from virtuals.loc import path

    from nu import Nu, Value
    from nu.interfaces import NoneI
    from nu.shapes import Shape

__all__ = [
    "BoolRef",
    "BytesRef",
    "FloatRef",
    "IntRef",
    "ItemRef",
    "PrimitiveDictRef",
    "PrimitiveListRef",
    "PrimitiveSetRef",
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

    Overrides store() to use _primitive_write() directly, skipping
    the container type check that __setitem__ would trigger.
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

    def store(self, value: object) -> NoneI:
        from nu import NoneI, ensure_nu
        from nu_virtuals.morphisms.item import PrimitiveStoreCmd

        return NoneI(PrimitiveStoreCmd(self, ensure_nu(value)))

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


class IntRef(ItemRef[int, IntI], IntI):
    """PV integer reference with full numeric interface.

    Inherits:
        - ItemRef: PV storage access + CRUD + observation
        - IntI: Arithmetic, comparison, bitwise, logical operators
    """

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV int ref."""
        super().__init__(
            address=address,
            value_type=int,
            value_value_type=IntI,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for int values."""
        return Slot(cls)  # type: ignore[return-value]


class StrRef(ItemRef[str, StrI], StrI):
    """PV string reference with full string interface.

    Inherits:
        - ItemRef: PV storage access + CRUD + observation
        - StrI: String methods (upper, lower, split, etc.), concatenation
    """

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV str ref."""
        super().__init__(
            address=address,
            value_type=str,
            value_value_type=StrI,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for str values."""
        return Slot(cls)  # type: ignore[return-value]


class FloatRef(ItemRef[float, FloatI], FloatI):
    """PV float reference with full numeric interface.

    Inherits:
        - ItemRef: PV storage access + CRUD + observation
        - FloatI: Arithmetic, comparison, logical operators
    """

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV float ref."""
        super().__init__(
            address=address,
            value_type=float,
            value_value_type=FloatI,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for float values."""
        return Slot(cls)  # type: ignore[return-value]


class BoolRef(ItemRef[bool, BoolI], BoolI):
    """PV boolean reference with full logical interface.

    Inherits:
        - ItemRef: PV storage access + CRUD + observation
        - BoolI: Logical operators (and_, or_, not_)
    """

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV bool ref."""
        super().__init__(
            address=address,
            value_type=bool,
            value_value_type=BoolI,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for bool values."""
        return Slot(cls)  # type: ignore[return-value]


class BytesRef(ItemRef[bytes, BytesI], BytesI):
    """PV bytes reference with full bytes interface.

    Inherits:
        - ItemRef: PV storage access + CRUD + observation
        - BytesI: Bytes methods (decode, hex, etc.)
    """

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV bytes ref."""
        super().__init__(
            address=address,
            value_type=bytes,
            value_value_type=BytesI,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for bytes values."""
        return Slot(cls)  # type: ignore[return-value]


# =============================================================================
# COMPOUND PRIMITIVE REFS (stored as single blob, not decomposed)
# =============================================================================


class PrimitiveDictRef[K, V](
    ItemRef[dict[K, V], DictI[K, V]],
    DictI[K, V],
):
    """PV dict reference stored as a single primitive blob.

    Unlike DictRef which decomposes into per-key storage, this stores the
    entire dict as one value. Operations work on the fetched Python dict.

    Inherits:
        - ItemRef: PV storage access + CRUD + observation
        - DictI: Dict methods (keys, values, items, get, set, etc.)
    """

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV primitive dict ref."""
        super().__init__(
            address=address,
            value_type=dict,
            value_value_type=DictI,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for primitive dict values."""
        return Slot(cls)  # type: ignore[return-value]


class PrimitiveListRef[T](
    ItemRef[list[T], ListI[T]],
    ListI[T],
):
    """PV list reference stored as a single primitive blob.

    Unlike ListRef which decomposes into per-index storage, this stores the
    entire list as one value. Operations work on the fetched Python list.

    Inherits:
        - ItemRef: PV storage access + CRUD + observation
        - ListI: List methods (append, extend, insert, etc.)
    """

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV primitive list ref."""
        super().__init__(
            address=address,
            value_type=list,
            value_value_type=ListI,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for primitive list values."""
        return Slot(cls)  # type: ignore[return-value]


class PrimitiveSetRef[T](
    ItemRef[set[T], SetI[T]],
    SetI[T],
):
    """PV set reference stored as a single primitive blob.

    Unlike SetRef which decomposes into per-element storage, this stores the
    entire set as one value. Operations work on the fetched Python set.

    Inherits:
        - ItemRef: PV storage access + CRUD + observation
        - SetI: Set methods (add, remove, union, intersection, etc.)
    """

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV primitive set ref."""
        super().__init__(
            address=address,
            value_type=set,
            value_value_type=SetI,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Create a slot for primitive set values."""
        return Slot(cls)  # type: ignore[return-value]
