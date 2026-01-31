"""Concrete PV primitive ref implementations.

Typed leaf refs combine PVPrimitiveRef (PV substrate) with everybase
type operators (IntType, StrType, etc.).

Item refs combine ReactiveItemRef (everyshape document model) with
PVPrimitiveRef (PV substrate) for CRUD + observation on PV storage.

Pattern:
    class PVIntRef(PVPrimitiveRef[int], IntType):
        # PV substrate + int operators

    class PVItemRef(ReactiveItemRef[T, ValueT], PVPrimitiveRef[T]):
        # Document model (CRUD + observe) + PV substrate
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from every_pv.ref import PVPrimitiveRef
from everybase.types import (
    BoolType,
    BytesType,
    FloatType,
    IntType,
    StrType,
)
from everyshape import ReactiveItemRef


if TYPE_CHECKING:
    from pv.loc import path

    from everyabc import Term, Value
    from everyshape import ShapeBase as PVShape


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


class PVIntRef(PVPrimitiveRef[int], IntType):
    """PV integer reference with full numeric interface.

    Inherits:
        - PVPrimitiveRef: PV storage access via fetch()
        - IntType: Arithmetic, comparison, bitwise, logical operators
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PVPrimitiveRef | None = None,
        shape: type[PVShape] | None = None,
    ) -> None:
        """Initialize PV int ref."""
        super().__init__(address, int, parent, shape)


class PVStrRef(PVPrimitiveRef[str], StrType):
    """PV string reference with full string interface.

    Inherits:
        - PVPrimitiveRef: PV storage access via fetch()
        - StrType: String methods (upper, lower, split, etc.), concatenation
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PVPrimitiveRef | None = None,
        shape: type[PVShape] | None = None,
    ) -> None:
        """Initialize PV str ref."""
        super().__init__(address, str, parent, shape)


class PVFloatRef(PVPrimitiveRef[float], FloatType):
    """PV float reference with full numeric interface.

    Inherits:
        - PVPrimitiveRef: PV storage access via fetch()
        - FloatType: Arithmetic, comparison, logical operators
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PVPrimitiveRef | None = None,
        shape: type[PVShape] | None = None,
    ) -> None:
        """Initialize PV float ref."""
        super().__init__(address, float, parent, shape)


class PVBoolRef(PVPrimitiveRef[bool], BoolType):
    """PV boolean reference with full logical interface.

    Inherits:
        - PVPrimitiveRef: PV storage access via fetch()
        - BoolType: Logical operators (and_, or_, not_)
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PVPrimitiveRef | None = None,
        shape: type[PVShape] | None = None,
    ) -> None:
        """Initialize PV bool ref."""
        super().__init__(address, bool, parent, shape)


class PVBytesRef(PVPrimitiveRef[bytes], BytesType):
    """PV bytes reference with full bytes interface.

    Inherits:
        - PVPrimitiveRef: PV storage access via fetch()
        - BytesType: Bytes methods (decode, hex, etc.)
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
# ITEM REFS (document model + PV substrate)
# =============================================================================


class PVItemRef[T, ValueT: Value](
    ReactiveItemRef[T, ValueT],
    PVPrimitiveRef[T],
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
        parent: PVPrimitiveRef | None = None,
        shape: type[PVShape] | None = None,
    ) -> None:
        """Initialize item reference."""
        super().__init__(address, value_type, parent, shape)
        self._value_value_type = value_value_type


class PVListItemRef[T, ValueT: Value](
    ReactiveItemRef[T, ValueT],
    PVPrimitiveRef[T],
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


class PVDictItemRef[T, ValueT: Value](
    ReactiveItemRef[T, ValueT],
    PVPrimitiveRef[T],
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
