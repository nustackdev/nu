"""Concrete PV primitive ref implementations.

These refs inherit from everybase RefBases for the interface (operators, methods)
and use PVPrimitiveRefMixin for PV-specific storage access.

Pattern:
    class PVIntRef(PVPrimitiveRefMixin[int], IntRefBase):
        pass

The IntRefBase provides:
    - Arithmetic operators: +, -, *, /, //, %, **
    - Comparison operators: ==, !=, <, <=, >, >=
    - Bitwise operators: &, |, ^, ~, <<, >>
    - Logical operators: and_(), or_(), not_()

The PVPrimitiveRefMixin provides:
    - get(ctx) -> int | Sentinel: Read from PV storage
    - resolve(ctx) -> path: Path resolution
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from every import Ref
from every_pv.traits.bases_primitive import (
    CollectionItemRefBase,
    MutableMappingItemRefBase,
    MutableSequenceItemRefBase,
)
from everybase.refs import (
    BoolRefBase,
    BytesRefBase,
    FloatRefBase,
    IntRefBase,
    StrRefBase,
)

from .base import PVPrimitiveRefMixin


if TYPE_CHECKING:
    from pv.loc import path

    from every import Ref, RValue, Shape


__all__ = [
    "PVBoolRef",
    "PVBytesRef",
    "PVDictItemRef",
    "PVFloatRef",
    "PVIntRef",
    "PVItemRef",
    "PVListItemRef",
    "PVStrRef",
]


# =============================================================================
# PRIMITIVE REFS (with everybase interface)
# =============================================================================


class PVIntRef(PVPrimitiveRefMixin[int], IntRefBase):
    """PV integer reference with full numeric interface.

    Inherits:
        - IntRefBase: Arithmetic, comparison, bitwise, logical operators
        - PVPrimitiveRefMixin: PV storage access via get()
    """

    def __init__(
        self,
        address: path.PathAddress | RValue,
        parent_ref: Ref | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV int ref."""
        super().__init__(parent_ref, owner_shape)
        self.address = address
        self.value_type = int


class PVStrRef(PVPrimitiveRefMixin[str], StrRefBase):
    """PV string reference with full string interface.

    Inherits:
        - StrRefBase: String methods (upper, lower, split, etc.), concatenation
        - PVPrimitiveRefMixin: PV storage access via get()
    """

    def __init__(
        self,
        address: path.PathAddress | RValue,
        parent_ref: Ref | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV str ref."""
        super().__init__(parent_ref, owner_shape)
        self.address = address
        self.value_type = str


class PVFloatRef(PVPrimitiveRefMixin[float], FloatRefBase):
    """PV float reference with full numeric interface.

    Inherits:
        - FloatRefBase: Arithmetic, comparison, logical operators
        - PVPrimitiveRefMixin: PV storage access via get()
    """

    def __init__(
        self,
        address: path.PathAddress | RValue,
        parent_ref: Ref | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV float ref."""
        super().__init__(parent_ref, owner_shape)
        self.address = address
        self.value_type = float


class PVBoolRef(PVPrimitiveRefMixin[bool], BoolRefBase):
    """PV boolean reference with full logical interface.

    Inherits:
        - BoolRefBase: Logical operators (and_, or_, not_)
        - PVPrimitiveRefMixin: PV storage access via get()
    """

    def __init__(
        self,
        address: path.PathAddress | RValue,
        parent_ref: Ref | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV bool ref."""
        super().__init__(parent_ref, owner_shape)
        self.address = address
        self.value_type = bool


class PVBytesRef(PVPrimitiveRefMixin[bytes], BytesRefBase):
    """PV bytes reference with full bytes interface.

    Inherits:
        - BytesRefBase: Bytes methods (decode, hex, etc.)
        - PVPrimitiveRefMixin: PV storage access via get()
    """

    def __init__(
        self,
        address: path.PathAddress | RValue,
        parent_ref: Ref | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV bytes ref."""
        super().__init__(parent_ref, owner_shape)
        self.address = address
        self.value_type = bytes


# =============================================================================
# ITEM REFS (for items within collections)
# =============================================================================


class PVItemRef[T, ValueT: Ref](
    PVPrimitiveRefMixin[T],
    CollectionItemRefBase[T, ValueT],
):
    """PV item reference for primitive values.

    Used for standalone primitive values in shapes.
    Combines PV storage access with collection item capabilities.
    """

    def __init__(
        self,
        address: path.PathAddress | RValue,
        value_type: type[T],
        value_value_type: type[ValueT],
        parent_ref: Ref | None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize item reference."""
        super().__init__(parent_ref, owner_shape)
        self.address = address
        self.value_type = value_type
        self.value_value_type = value_value_type


class PVListItemRef[T, ValueT: Ref](
    PVPrimitiveRefMixin[T],
    MutableSequenceItemRefBase[T, ValueT],
):
    """PV list item reference for items in a list.

    Same capabilities as PVItemRef - the distinction is semantic
    for type clarity when building refs for sequence items.
    """

    def __init__(
        self,
        address: path.PathAddress | RValue,
        value_type: type[T],
        value_value_type: type[ValueT],
        parent_ref: Ref | None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize list item reference."""
        super().__init__(parent_ref, owner_shape)
        self.address = address
        self.value_type = value_type
        self.value_value_type = value_value_type


class PVDictItemRef[T, ValueT: Ref](
    PVPrimitiveRefMixin[T],
    MutableMappingItemRefBase[T, ValueT],
):
    """PV dict item reference for items in a mapping.

    Same capabilities as PVItemRef - the distinction is semantic
    for type clarity when building refs for mapping values.
    """

    def __init__(
        self,
        address: path.PathAddress | RValue,
        value_type: type[T],
        value_value_type: type[ValueT],
        parent_ref: Ref | None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize dict item reference."""
        super().__init__(parent_ref, owner_shape)
        self.address = address
        self.value_type = value_type
        self.value_value_type = value_value_type
