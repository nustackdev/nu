# ruff: noqa: D102
"""Dict substrate collection refs — containers in nested dicts.

These combine everyshape document model bases (navigation, capabilities)
with RefBase (plain dict navigation). No reactivity.

Structural types:
    ShapeRef        structured container with named slots
    MappingRef      key-value container (child ref creation)
    SequenceRef     ordered container (item ref creation)
    ShapesListRef   sequence of homogeneous shapes
    ShapesDictRef   mapping of homogeneous shapes
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from every_dict.items import ItemRef
from every_dict.ref import RefBase
from everybase import (
    AnyValue,
    BoolValue,
    BytesValue,
    DictValue,
    FloatValue,
    IntValue,
    ListValue,
    SetValue,
    StrValue,
    ensure_term,
)
from everyshape import Slot
from everyshape.refs import (
    MutableMappingRefBase,
    MutableSequenceRefBase,
    MutableShapeRef,
    MutableShapesDictRefBase,
    MutableShapesListRefBase,
)
from everyshape.refs import ShapeRef as _BaseShapeRef


if TYPE_CHECKING:
    from typing import Self

    from everyabc import Sentinel, Term, Value
    from everyshape import Shape as ShapeBase


def _value_type_for(python_type: type) -> type[Value]:
    """Map Python type to its corresponding Value type."""
    mapping: dict[type, type[Value]] = {
        int: IntValue,
        str: StrValue,
        float: FloatValue,
        bool: BoolValue,
        bytes: BytesValue,
        list: ListValue,
        dict: DictValue,
        set: SetValue,
    }
    return mapping.get(python_type, AnyValue)


__all__ = [
    "MappingRef",
    "SequenceRef",
    "ShapeRef",
    "ShapesDictRef",
    "ShapesListRef",
]


# =============================================================================
# SHAPE REF
# =============================================================================


class ShapeRef[T: ShapeBase](
    MutableShapeRef[T],
    RefBase[dict[str, object]],
):
    """Dict shape reference — structured container backed by nested dict."""

    _PASSTHROUGH_ATTRS: ClassVar[frozenset[str]] = _BaseShapeRef._PASSTHROUGH_ATTRS

    def __init__(
        self,
        address: str | int | Term,
        shape_type: type[T],
        parent: RefBase | None = None,
        shape: type[ShapeBase] | None = None,
    ) -> None:
        """Initialize shape reference."""
        super().__init__(address, parent, shape)
        self._shape_type = shape_type
        self.key_type: type = str
        self.value_type: type = object

    @classmethod
    def slot(cls, shape_type: type[T]) -> Self:
        """Create a slot for this shape ref type.

        Args:
            shape_type: Shape class for the nested structure.

        Returns:
            Slot that creates ShapeRef instances.
        """
        return Slot(cls, shape_type=shape_type)  # type: ignore[return-value]


# =============================================================================
# MAPPING REF
# =============================================================================


class MappingRef[K, V](
    MutableMappingRefBase[K, V, DictValue[K, V], AnyValue],
    RefBase[dict[K, V]],
):
    """Dict mapping reference — key-value container backed by nested dict."""

    def result(self, op: Term) -> DictValue[K, V]:
        return DictValue(op)

    def element_result(self, op: Term) -> AnyValue:
        return AnyValue(op)

    def iterable_result(self, op: Term) -> ListValue:
        return ListValue(op)

    def __init__(
        self,
        address: str | int | Term,
        value_type: type[V],
        key_type: type[K],
        key_value_type: type,
        value_value_type: type,
        parent: RefBase | None = None,
        shape: type[ShapeBase] | None = None,
    ) -> None:
        """Initialize mapping reference."""
        super().__init__(address, parent, shape)
        self.value_type = value_type
        self.key_type = key_type
        self.key_value_type = key_value_type
        self.value_value_type = value_value_type

    def _create_child_ref(self, key: K | Sentinel | Term[K | Sentinel]) -> ItemRef[V, ...]:
        """Create a reference to the value at the given key."""
        return ItemRef(
            address=ensure_term(key),
            value_type=self.value_type,
            value_value_type=self.value_value_type,
            parent=self,
            shape=self._shape,
        )

    @classmethod
    def slot(cls, value_type: type[V], key_type: type[K] = str) -> Self:  # type: ignore[assignment]
        """Create a slot for this mapping ref type.

        Args:
            value_type: Python type of values.
            key_type: Python type of keys (default: str).

        Returns:
            Slot that creates MappingRef instances.
        """
        return Slot(
            cls,
            value_type=value_type,
            key_type=key_type,
            key_value_type=_value_type_for(key_type),
            value_value_type=_value_type_for(value_type),
        )  # type: ignore[return-value]


# =============================================================================
# SEQUENCE REF
# =============================================================================


class SequenceRef[T](
    MutableSequenceRefBase[T, ListValue[T], AnyValue],
    RefBase[list[T]],
):
    """Dict sequence reference — ordered container backed by nested list."""

    def result(self, op: Term) -> ListValue[T]:
        return ListValue(op)

    def element_result(self, op: Term) -> AnyValue:
        return AnyValue(op)

    def __init__(
        self,
        address: str | int | Term,
        item_type: type[T],
        item_value_type: type,
        parent: RefBase | None = None,
        shape: type[ShapeBase] | None = None,
    ) -> None:
        """Initialize sequence reference."""
        super().__init__(address, parent, shape)
        self.item_type = item_type
        self.item_value_type = item_value_type

    def _create_item_ref(self, index: int | Sentinel | Term[int | Sentinel]) -> ItemRef[T, ...]:
        """Create a reference to the item at the given index."""
        return ItemRef(
            address=ensure_term(index),
            value_type=self.item_type,
            value_value_type=self.item_value_type,
            parent=self,
            shape=self._shape,
        )

    @classmethod
    def slot(cls, item_type: type[T]) -> Self:
        """Create a slot for this sequence ref type.

        Args:
            item_type: Python type of items.

        Returns:
            Slot that creates SequenceRef instances.
        """
        return Slot(
            cls,
            item_type=item_type,
            item_value_type=_value_type_for(item_type),
        )  # type: ignore[return-value]


# =============================================================================
# SHAPES LIST REF
# =============================================================================


class ShapesListRef[T: ShapeBase](
    MutableShapesListRefBase[T],
    RefBase[list[dict]],
):
    """Dict shapes list reference — sequence of homogeneous shapes."""

    def __init__(
        self,
        address: str | int | Term,
        shape_type: type[T],
        parent: RefBase | None = None,
        shape: type[ShapeBase] | None = None,
    ) -> None:
        """Initialize shapes list reference."""
        super().__init__(address, parent, shape)
        self._shape_type = shape_type
        self.item_type = dict

    def _create_item_ref(self, index: int | Sentinel | Term[int | Sentinel]) -> ShapeRef[T]:
        """Create a reference to a shape at the given index."""
        return ShapeRef(
            address=ensure_term(index),
            shape_type=self._shape_type,
            parent=self,
            shape=self._shape,
        )

    @classmethod
    def slot(cls, shape_type: type[T]) -> Self:
        """Create a slot for this shapes list ref type.

        Args:
            shape_type: Shape class for items.

        Returns:
            Slot that creates ShapesListRef instances.
        """
        return Slot(cls, shape_type=shape_type)  # type: ignore[return-value]


# =============================================================================
# SHAPES DICT REF
# =============================================================================


class ShapesDictRef[K, T: ShapeBase](
    MutableShapesDictRefBase[K, T],
    RefBase[dict[K, dict]],
):
    """Dict shapes dict reference — mapping of homogeneous shapes."""

    def __init__(
        self,
        address: str | int | Term,
        key_type: type[K],
        key_value_type: type,
        shape_type: type[T],
        parent: RefBase | None = None,
        shape: type[ShapeBase] | None = None,
    ) -> None:
        """Initialize shapes dict reference."""
        super().__init__(address, parent, shape)
        self.value_type = dict
        self.key_type = key_type
        self.key_value_type = key_value_type
        self._shape_type = shape_type

    def _create_child_ref(self, key: K | Sentinel | Term[K | Sentinel]) -> ShapeRef[T]:
        """Create a reference to a shape at the given key."""
        return ShapeRef(
            address=ensure_term(key),
            shape_type=self._shape_type,
            parent=self,
            shape=self._shape,
        )

    @classmethod
    def slot(cls, shape_type: type[T], key_type: type[K] = str) -> Self:  # type: ignore[assignment]
        """Create a slot for this shapes dict ref type.

        Args:
            shape_type: Shape class for values.
            key_type: Python type for keys (default: str).

        Returns:
            Slot that creates ShapesDictRef instances.
        """
        return Slot(
            cls,
            shape_type=shape_type,
            key_type=key_type,
            key_value_type=_value_type_for(key_type),
        )  # type: ignore[return-value]
