"""Reference implementations - addressable locations in tree.

Refs are LValues that point to specific locations in the tree.

Ref Types:
    - ValueRef: Points to primitive nodes in the tree (int, float, str, bool, dict, etc..)
    - MapRef: Points to mapping containers (key → value)
    - MapItemRef: Points to specific item in mapping

Key Properties:
    - Path caching: static_path computed at construction (O(1) resolution)
    - Dynamic support: is_dynamic flag + key_expr for runtime evaluation
    - Protocol-aware: view_type links to concrete view class

Resolution Strategy:
    Static refs:  return cached static_path (O(1))
    Dynamic refs: walk parent chain, evaluate expressions (O(depth))

Navigation Patterns:
    ValueRef:        Market.signal
    MapRef:          Market.orders
    MapItemRef:      Market.orders["AAPL"]  (static key)
    MapItemRef:      Market.orders[expr]    (dynamic key)

Example:
    # Static navigation
    ref = ValueRef("price", float, DictView, parent=None)
    ref.static_path  # → ("price",)
    ref.resolve(ctx)  # → ("price",) [cached]

    # Dynamic navigation
    ticker_expr = signal_ref.get()  # RValue expression
    item_ref = orders_ref[ticker_expr]  # MapItemRef
    item_ref.is_dynamic  # → True
    item_ref.resolve(ctx)  # → evaluates ticker_expr → ("orders", "AAPL")
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core import Ref


if TYPE_CHECKING:
    from redwood.tree.view import BaseView

    from ..core.term import RValue
    from ..types import Context, PathSegment, PrimitiveNodeValue, TuplePath
    from .commands import SetCmd
    from .operations import GetOp


# ============================================================================
# Value Ref - Primitive Values
# ============================================================================


class ValueRef(Ref):
    """Reference to a primitive value location.

    Points to a slot containing int, float, str, bool, etc.

    Example:
        Market.signal  # ValueRef to float
        Order.price    # ValueRef to float
    """

    def __init__(
        self,
        field_name: str,
        value_type: type,
        view_type: type[BaseView],
        parent_ref: Ref | None = None,
    ) -> None:
        """Initialize value reference.

        Args:
            field_name: Name of the field
            value_type: Python type of the value (int, str, etc.)
            view_type: View class for parent container
            parent_ref: Parent reference in chain
        """
        self.field_name = field_name
        self.value_type = value_type
        self.view_type = view_type
        self.parent_ref = parent_ref

        # Compute static path and dynamic flag
        if parent_ref is None:
            # Root field
            self.static_path = (field_name,)
            self.is_dynamic = False
        elif not parent_ref.is_dynamic:
            # Parent is static - extend its path
            self.static_path = (*parent_ref.static_path, field_name)
            self.is_dynamic = False
        else:
            # Parent is dynamic - can't precompute path
            self.static_path = None
            self.is_dynamic = True

    # ----- LValue contract -----

    def resolve(self, context: Context) -> TuplePath:
        """Resolve to path segments.

        Returns cached path for static refs, computes for dynamic.
        """
        if self.static_path is not None and not self.is_dynamic:
            return self.static_path

        # Dynamic path - walk parent chain
        segments: list[PathSegment] = [self.field_name]
        current = self.parent_ref
        while current is not None:
            segments.insert(0, current.last_segment())
            current = current.parent()

        return tuple(segments)

    def parent(self) -> Ref | None:
        """Return parent reference."""
        return self.parent_ref

    def last_segment(self) -> PathSegment:
        """Return field name as last segment."""
        return self.field_name

    # ----- Term contract -----

    def execute(self, context: Context) -> ValueRef:
        """Execute returns self - refs are locations."""
        return self

    # ----- Operations -----

    def get(self) -> GetOp:
        """Create read operation.

        Returns:
            GetOp that will read this value
        """
        from .operations import GetOp

        return GetOp(self)

    def set(self, value: PrimitiveNodeValue) -> SetCmd:
        """Create write operation.

        Args:
            value: Value to write

        Returns:
            SetCmd that will write this value
        """
        from .commands import SetCmd

        return SetCmd(self, value)

    def __repr__(self) -> str:
        if self.parent_ref:
            return f"{self.parent_ref}.{self.field_name}"
        return self.field_name


# ============================================================================
# Map Ref - Mapping Container
# ============================================================================


class MapRef(Ref):
    """Reference to a mapping container.

    Points to a slot containing key → value mappings.
    Supports item access via __getitem__.

    Example:
        Market.orders         # MapRef
        Market.orders["AAPL"] # MapItemRef (via __getitem__)
    """

    def __init__(
        self,
        field_name: str,
        value_type: type,
        view_type: type[BaseView],
        parent_ref: Ref | None = None,
    ) -> None:
        """Initialize map reference.

        Args:
            field_name: Name of the mapping field
            value_type: Type of values in the map
            view_type: View class for this mapping
            parent_ref: Parent reference in chain
        """
        self.field_name = field_name
        self.value_type = value_type
        self.view_type = view_type
        self.parent_ref = parent_ref

        # Compute static path and dynamic flag
        if parent_ref is None:
            self.static_path = (field_name,)
            self.is_dynamic = False
        elif not parent_ref.is_dynamic:
            self.static_path = (*parent_ref.static_path, field_name)
            self.is_dynamic = False
        else:
            self.static_path = None
            self.is_dynamic = True

    # ----- LValue contract -----

    def resolve(self, context: Context) -> TuplePath:
        """Resolve to path segments."""
        if self.static_path is not None and not self.is_dynamic:
            return self.static_path

        # Dynamic - walk chain
        segments: list[PathSegment] = [self.field_name]
        current = self.parent_ref
        while current is not None:
            segments.insert(0, current.last_segment())
            current = current.parent()

        return tuple(segments)

    def parent(self) -> Ref | None:
        """Return parent reference."""
        return self.parent_ref

    def last_segment(self) -> PathSegment:
        """Return field name."""
        return self.field_name

    # ----- Term contract -----

    def execute(self, context: Context) -> MapRef:
        """Execute returns self."""
        return self

    # ----- Item access -----

    def __getitem__(self, key: str | RValue) -> MapItemRef:
        """Access specific item in mapping.

        Args:
            key: String key (static) or RValue expression (dynamic)

        Returns:
            MapItemRef pointing to the item
        """
        if isinstance(key, str):
            # Static key
            return MapItemRef(
                map_ref=self,
                key=key,
                key_expr=None,
                value_type=self.value_type,
                view_type=self.view_type,
            )
        else:
            # Dynamic key - store expression
            return MapItemRef(
                map_ref=self,
                key=None,
                key_expr=key,
                value_type=self.value_type,
                view_type=self.view_type,
            )

    def __repr__(self) -> str:
        if self.parent_ref:
            return f"{self.parent_ref}.{self.field_name}"
        return self.field_name


# ============================================================================
# Map Item Ref - Specific Item in Mapping
# ============================================================================


class MapItemRef(Ref):
    """Reference to a specific item in a mapping.

    Created by MapRef[key]. Can have static or dynamic keys.

    Example:
        Market.orders["AAPL"]          # Static key
        Market.orders[current.get()]   # Dynamic key
    """

    def __init__(
        self,
        map_ref: MapRef,
        key: str | None,
        key_expr: RValue | None,
        value_type: type,
        view_type: type[BaseView],
    ) -> None:
        """Initialize map item reference.

        Args:
            map_ref: Parent MapRef
            key: Static key (if static)
            key_expr: Dynamic key expression (if dynamic)
            value_type: Type of the item value
            view_type: View class (inherited from parent)
        """
        self.map_ref = map_ref
        self.key = key
        self.key_expr = key_expr
        self.value_type = value_type
        self.view_type = view_type

        # Determine if primitive or nested
        self.is_primitive = value_type in (int, float, str, bool, bytes)

        # Compute static path and dynamic flag
        if key is not None and not map_ref.is_dynamic:
            # Static key + static parent
            self.static_path = (*map_ref.static_path, key)
            self.is_dynamic = False
        else:
            # Dynamic key or dynamic parent
            self.static_path = None
            self.is_dynamic = True

    # ----- LValue contract -----

    def resolve(self, context: Context) -> TuplePath:
        """Resolve to path segments.

        For dynamic keys, evaluates the expression.
        """
        if self.static_path is not None and not self.is_dynamic:
            return self.static_path

        # Resolve parent path
        parent_path = self.map_ref.resolve(context)

        # Get key (static or evaluate expression)
        key_value = self.key if self.key is not None else self.key_expr.execute(context)

        return (*parent_path, key_value)

    def parent(self) -> Ref | None:
        """Return parent MapRef."""
        return self.map_ref

    def last_segment(self) -> PathSegment:
        """Return key as last segment."""
        if self.key is not None:
            return self.key
        return "<dynamic>"

    # ----- Term contract -----

    def execute(self, context: Context) -> MapItemRef:
        """Execute returns self."""
        return self

    # ----- Operations (primitives only) -----

    def get(self) -> GetOp:
        """Create read operation (primitives only)."""
        # if not self.is_primitive:
        #     raise AttributeError(
        #         "Cannot call .get() on non-primitive item. Navigate to a field first."
        #     )

        from .operations import GetOp

        return GetOp(self)

    def set(self, value: PrimitiveNodeValue) -> SetCmd:
        """Create write operation (primitives only)."""
        # if not self.is_primitive:
        #     raise AttributeError(
        #         "Cannot call .set() on non-primitive item. Navigate to a field first."
        #     )

        from .commands import SetCmd

        return SetCmd(self, value)

    # ----- Nested navigation (non-primitives) -----

    def __getattribute__(self, name: str) -> object:
        """Navigate to nested fields for non-primitive values."""
        # Allow internal attributes
        if name in [
            "map_ref",
            "key",
            "key_expr",
            "value_type",
            "view_type",
            "is_primitive",
            "static_path",
            "is_dynamic",
            "resolve",
            "parent",
            "last_segment",
            "execute",
            "get",
            "set",
        ]:
            return object.__getattribute__(self, name)

        # Check if primitive
        is_prim = object.__getattribute__(self, "is_primitive")
        if is_prim:
            raise AttributeError(f"Primitive item has no attribute '{name}'. Use .get()")

        # Navigate to nested field (Shape navigation)
        # This would delegate to Shape/Slot system when implemented
        value_type = object.__getattribute__(self, "value_type")
        if hasattr(value_type, "_slots") and name in value_type._slots:
            slot = value_type._slots[name]
            return slot.create_ref(value_type, parent_ref=self)

        raise AttributeError(f"{value_type.__name__} has no field '{name}'")

    def __repr__(self) -> str:
        if self.key is not None:
            return f'{self.map_ref}["{self.key}"]'
        return f"{self.map_ref}[<dynamic>]"


__all__ = [
    "MapItemRef",
    "MapRef",
    "ValueRef",
]
