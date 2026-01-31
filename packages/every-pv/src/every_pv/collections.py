"""Concrete PV collection ref implementations.

Collection refs need LAZY implementations because PV storage can be huge
(e.g., petabyte-scale RocksDB). Operations like find(), filter(), map()
must work streaming without loading everything into memory.

Unlike primitive refs, collection refs don't inherit from everybase RefBases
because the interface is fundamentally different:
- everybase collection refs: fetch() loads entire collection, then run operations
- PV collection refs: operations work lazily/streaming on the view directly
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from pv.collections import MutableMappingView, MutableSequenceView
from pv.types import Value as StorageValue

from every_pv.primitives import PVDictItemRef, PVListItemRef
from every_pv.ref import PVRefBase, PVViewRef
from everybase import ensure_term
from everyshape import ShapeBase as PVShape


if TYPE_CHECKING:
    from pv.loc import path

    from everyabc import Ref, Sentinel, Term


__all__ = [
    "PVDictRef",
    "PVListRef",
    "PVShapeRef",
    "PVShapesDictRef",
    "PVShapesListRef",
]


# =============================================================================
# SHAPE REF
# =============================================================================


class PVShapeRef[T: PVShape](
    PVViewRef[dict[str, StorageValue], MutableMappingView],
):
    """Reference to a nested shape location.

    Points to container nodes with structure defined by a Shape.
    Supports navigation to nested fields via attribute access.
    """

    # Passthrough attributes that should not trigger slot lookup
    _PASSTHROUGH_ATTRS: ClassVar[frozenset[str]] = frozenset(
        {
            # Python internals
            "__class__",
            "__dict__",
            "__repr__",
            "__str__",
            # Ref base
            "address",
            "_address",
            "view_type",
            "_view_type",
            "parent",
            "_parent",
            "shape",
            "_shape",
            "resolve",
            "execute",
            "fetch",
            "is_self_pure",
            "is_subtree_pure",
            "get_root_shape",
            "_type_marker",
            "_resolve_address",
            # ShapeRef specific
            "shape_type",
            "_shape_type",
            "key_type",
            "value_type",
            "_create_child_ref",
        }
    )

    def __init__(
        self,
        address: path.PathAddress | Term,
        shape_type: type[T],
        view_type: type[MutableMappingView],
        parent: PVRefBase | None = None,
        shape: type[PVShape] | None = None,
    ) -> None:
        """Initialize shape reference."""
        super().__init__(address, view_type, parent, shape)
        self._shape_type = shape_type
        self.key_type: type = str
        self.value_type: type = object

    @property
    def shape_type(self) -> type[T]:
        """The Shape class type at this location."""
        return self._shape_type

    def _create_child_ref(self, key: str | Sentinel) -> Ref:
        """Create a reference to a child at the given key."""
        if not isinstance(key, str):
            raise TypeError(f"key must be str, `{type(key).__name__}` given")

        if hasattr(self._shape_type, "_slots") and key in self._shape_type._slots:
            slot = self._shape_type._slots[key]
            return slot.create_ref(owner_shape=self._shape_type, parent_ref=self)

        raise KeyError(f"{self._shape_type.__name__} has no slot '{key}'")

    def __getattribute__(self, name: str) -> object:
        """Navigate to nested fields via attribute access."""
        passthrough = object.__getattribute__(self, "_PASSTHROUGH_ATTRS")
        if name in passthrough:
            return object.__getattribute__(self, name)

        shape_type: type[PVShape] = object.__getattribute__(self, "_shape_type")

        if hasattr(shape_type, "_slots") and name in shape_type._slots:
            slot = shape_type._slots[name]
            return slot.create_ref(owner_shape=shape_type, parent_ref=self)

        raise AttributeError(f"{shape_type.__name__} has no slot '{name}'")


# =============================================================================
# DICT REF
# =============================================================================


class PVDictRef[K: int | str, V: StorageValue](
    PVViewRef[dict[K, V], MutableMappingView],
):
    """Reference to a mapping container with lazy operations.

    All operations (filter, find, etc.) work lazily on the view
    without loading everything into memory.
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        value_type: type[V],
        key_type: type[K],
        view_type: type[MutableMappingView],
        key_value_type: type,
        value_value_type: type,
        parent: PVRefBase | None = None,
        shape: type[PVShape] | None = None,
    ) -> None:
        """Initialize mapping reference."""
        super().__init__(address, view_type, parent, shape)
        self.value_type = value_type
        self.key_type = key_type
        self.key_value_type = key_value_type
        self.value_value_type = value_value_type

    def _create_child_ref(self, key: K | Sentinel | Term[K | Sentinel]) -> PVDictItemRef[V, ...]:
        """Create a reference to a child at the given key."""
        return PVDictItemRef(
            address=ensure_term(key),
            value_type=self.value_type,
            value_value_type=self.value_value_type,
            parent=self,
            shape=self._shape,
        )


# =============================================================================
# LIST REF
# =============================================================================


class PVListRef[T, ItemValueT](
    PVViewRef[list[T], MutableSequenceView],
):
    """Reference to a sequence container with lazy operations.

    All operations (filter, find, map, etc.) work lazily on the view
    without loading everything into memory.
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        item_type: type[T],
        item_value_type: type[ItemValueT],
        view_type: type[MutableSequenceView],
        parent: PVRefBase | None = None,
        shape: type[PVShape] | None = None,
    ) -> None:
        """Initialize sequence reference."""
        super().__init__(address, view_type, parent, shape)
        self.item_type = item_type
        self.item_value_type = item_value_type

    def _create_item_ref(
        self, index: int | Sentinel | Term[int | Sentinel]
    ) -> PVListItemRef[T, ItemValueT]:
        """Create a reference to an item at the given index."""
        return PVListItemRef(
            address=ensure_term(index),
            value_type=self.item_type,
            value_value_type=self.item_value_type,
            parent=self,
            shape=self._shape,
        )


# =============================================================================
# SHAPES LIST REF
# =============================================================================


class PVShapesListRef[T: PVShape](
    PVViewRef[list[dict], MutableSequenceView],
):
    """Reference to a list of homogeneous shapes."""

    def __init__(
        self,
        address: path.PathAddress | Term,
        shape_type: type[T],
        view_type: type[MutableSequenceView],
        parent: PVRefBase | None = None,
        shape: type[PVShape] | None = None,
    ) -> None:
        """Initialize sequence shape reference."""
        super().__init__(address, view_type, parent, shape)
        self._shape_type = shape_type
        self.item_type = dict

    @property
    def shape_type(self) -> type[T]:
        """The Shape class for items in this list."""
        return self._shape_type

    def _create_item_ref(self, index: int | Sentinel | Term[int | Sentinel]) -> PVShapeRef[T]:
        """Create a reference to a shape at the given index."""
        from every_pv.views import DictView

        return PVShapeRef(
            address=ensure_term(index),
            shape_type=self._shape_type,
            view_type=DictView,
            parent=self,
            shape=self._shape,
        )


# =============================================================================
# SHAPES DICT REF
# =============================================================================


class PVShapesDictRef[K: int | str, T: PVShape, KeyValueT](
    PVViewRef[dict[K, dict], MutableMappingView],
):
    """Reference to a mapping of homogeneous shapes."""

    def __init__(
        self,
        address: path.PathAddress | Term,
        key_type: type[K],
        key_value_type: type[KeyValueT],
        shape_type: type[T],
        view_type: type[MutableMappingView],
        parent: PVRefBase | None = None,
        shape: type[PVShape] | None = None,
    ) -> None:
        """Initialize mapping shape reference."""
        super().__init__(address, view_type, parent, shape)
        self.value_type = dict
        self.key_type = key_type
        self.key_value_type = key_value_type
        self._shape_type = shape_type

    @property
    def shape_type(self) -> type[T]:
        """The Shape class for values in this dict."""
        return self._shape_type

    def _create_child_ref(self, key: K | Sentinel | Term[K | Sentinel]) -> PVShapeRef[T]:
        """Create a reference to a shape at the given key."""
        from every_pv.views import DictView

        return PVShapeRef(
            address=ensure_term(key),
            shape_type=self._shape_type,
            view_type=DictView,
            parent=self,
            shape=self._shape,
        )
