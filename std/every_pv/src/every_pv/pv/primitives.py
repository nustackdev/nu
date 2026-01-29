"""Concrete PV primitive ref implementations.

These refs inherit from PVPrimitiveRef for storage access and everybase
RefBases for the operator interface.

Pattern:
    class PVIntRef(PVPrimitiveRef[int], IntRefBase):
        def __init__(self, address, parent=None, shape=None):
            super().__init__(address, int, parent, shape)

The IntRefBase provides:
    - Arithmetic operators: +, -, *, /, //, %, **
    - Comparison operators: ==, !=, <, <=, >, >=
    - Bitwise operators: &, |, ^, ~, <<, >>
    - Logical operators: and_(), or_(), not_()

The PVPrimitiveRef provides:
    - fetch(ctx) -> int | Sentinel: Read from PV storage
    - resolve(ctx) -> path: Path resolution from parent chain
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from every_pv.ref import PVPrimitiveRef
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


if TYPE_CHECKING:
    from pv.loc import path

    from every_pv.shape import PVShape
    from everyabc import Ref, Term


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


class PVIntRef(PVPrimitiveRef[int], IntRefBase):
    """PV integer reference with full numeric interface.

    Inherits:
        - PVPrimitiveRef: PV storage access via fetch()
        - IntRefBase: Arithmetic, comparison, bitwise, logical operators
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PVPrimitiveRef | None = None,
        shape: type[PVShape] | None = None,
    ) -> None:
        """Initialize PV int ref."""
        super().__init__(address, int, parent, shape)


class PVStrRef(PVPrimitiveRef[str], StrRefBase):
    """PV string reference with full string interface.

    Inherits:
        - PVPrimitiveRef: PV storage access via fetch()
        - StrRefBase: String methods (upper, lower, split, etc.), concatenation
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PVPrimitiveRef | None = None,
        shape: type[PVShape] | None = None,
    ) -> None:
        """Initialize PV str ref."""
        super().__init__(address, str, parent, shape)


class PVFloatRef(PVPrimitiveRef[float], FloatRefBase):
    """PV float reference with full numeric interface.

    Inherits:
        - PVPrimitiveRef: PV storage access via fetch()
        - FloatRefBase: Arithmetic, comparison, logical operators
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PVPrimitiveRef | None = None,
        shape: type[PVShape] | None = None,
    ) -> None:
        """Initialize PV float ref."""
        super().__init__(address, float, parent, shape)


class PVBoolRef(PVPrimitiveRef[bool], BoolRefBase):
    """PV boolean reference with full logical interface.

    Inherits:
        - PVPrimitiveRef: PV storage access via fetch()
        - BoolRefBase: Logical operators (and_, or_, not_)
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PVPrimitiveRef | None = None,
        shape: type[PVShape] | None = None,
    ) -> None:
        """Initialize PV bool ref."""
        super().__init__(address, bool, parent, shape)


class PVBytesRef(PVPrimitiveRef[bytes], BytesRefBase):
    """PV bytes reference with full bytes interface.

    Inherits:
        - PVPrimitiveRef: PV storage access via fetch()
        - BytesRefBase: Bytes methods (decode, hex, etc.)
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PVPrimitiveRef | None = None,
        shape: type[PVShape] | None = None,
    ) -> None:
        """Initialize PV bytes ref."""
        super().__init__(address, bytes, parent, shape)


# =============================================================================
# ITEM REFS (for items within collections)
# =============================================================================


class PVItemRef[T, ValueT: Ref](
    PVPrimitiveRef[T],
    CollectionItemRefBase[T, ValueT],
):
    """PV item reference for primitive values.

    Used for standalone primitive values in shapes.
    Combines PV storage access with collection item capabilities.
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        value_type: type[T],
        value_value_type: type[ValueT],
        parent: PVPrimitiveRef | None = None,
        shape: type[PVShape] | None = None,
    ) -> None:
        """Initialize item reference."""
        super().__init__(address, value_type, parent, shape)
        self._value_value_type = value_value_type

    @property
    def value_value_type(self) -> type[ValueT]:
        """The ref type for this item's value."""
        return self._value_value_type


class PVListItemRef[T, ValueT: Ref](
    PVPrimitiveRef[T],
    MutableSequenceItemRefBase[T, ValueT],
):
    """PV list item reference for items in a list.

    Same capabilities as PVItemRef - the distinction is semantic
    for type clarity when building refs for sequence items.
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        value_type: type[T],
        value_value_type: type[ValueT],
        parent: PVPrimitiveRef | None = None,
        shape: type[PVShape] | None = None,
    ) -> None:
        """Initialize list item reference."""
        super().__init__(address, value_type, parent, shape)
        self._value_value_type = value_value_type

    @property
    def value_value_type(self) -> type[ValueT]:
        """The ref type for this item's value."""
        return self._value_value_type


class PVDictItemRef[T, ValueT: Ref](
    PVPrimitiveRef[T],
    MutableMappingItemRefBase[T, ValueT],
):
    """PV dict item reference for items in a mapping.

    Same capabilities as PVItemRef - the distinction is semantic
    for type clarity when building refs for mapping values.
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        value_type: type[T],
        value_value_type: type[ValueT],
        parent: PVPrimitiveRef | None = None,
        shape: type[PVShape] | None = None,
    ) -> None:
        """Initialize dict item reference."""
        super().__init__(address, value_type, parent, shape)
        self._value_value_type = value_value_type

    @property
    def value_value_type(self) -> type[ValueT]:
        """The ref type for this item's value."""
        return self._value_value_type
