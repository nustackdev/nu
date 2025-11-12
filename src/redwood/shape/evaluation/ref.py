"""Ref contract - abstract base for all addressable references.

This module defines the Ref abstract class, which serves as the
intermediate contract between LValue (generic addressable term) and
concrete reference implementations (ValueRef, MapRef, etc.).

Contract Hierarchy:
    Term (most abstract)
    └── LValue (addressable location)
        └── Ref (reference with metadata)
            ├── ValueRef (primitive values)
            ├── MapRef (mapping containers)
            ├── MapItemRef (items in mappings)
            └── ListRef (sequence containers)

Ref adds to LValue:
    - Common attributes: value_type, view_type, parent_ref, field_name
    - Path caching: static_path, is_dynamic
    - Default implementations: resolve(), parent(), last_segment()

Key Design Decisions:

    Q: Why intermediate Ref class between LValue and concrete refs?
    A: Captures common structure across all reference types without
       duplicating code in ValueRef, MapRef, etc.

    Q: Why no Slot reference?
    A: Slot is a factory that constructs Refs. Once constructed, refs
       are standalone and don't need to know about their origin.

    Q: What information does Ref store?
    A: Everything needed for resolution and operation:
       - value_type: What type of data this points to
       - view_type: Which view class to use for access
       - parent_ref: Chain for nested navigation
       - field_name: Name of this field/slot
       - static_path: Cached path if fully static
       - is_dynamic: Whether path contains runtime expressions

Ref Types and Their Characteristics:

    ValueRef:
        - Points to: Primitive values (int, float, str, bool)
        - View type: Passed from Slot (usually DictView)
        - Operations: .get(), .set()
        - Example: Market.signal → ValueRef

    MapRef:
        - Points to: Mapping containers (key → value)
        - View type: Passed from Slot (usually DictView)
        - Navigation: .__getitem__(key) → MapItemRef
        - Example: Market.orders → MapRef

    MapItemRef:
        - Points to: Specific item in mapping
        - View type: Inherited from parent MapRef
        - Key types: Static (str) or dynamic (RValue)
        - Example: Market.orders["AAPL"] → MapItemRef

    ListRef:
        - Points to: Sequence containers (index → value)
        - View type: Passed from Slot (usually ListView)
        - Navigation: .__getitem__(index) → ListItemRef
        - Example: Market.trades → ListRef

Path Resolution Strategy:

    Static paths (most common):
        - Computed at construction time
        - Cached in static_path attribute
        - resolve() returns cached tuple (O(1))

Example:
            Market.orders["AAPL"].price
            → static_path = ("orders", "AAPL", "price")

    Dynamic paths (rare):
        - Contain runtime-evaluated expressions
        - is_dynamic = True, static_path = None
        - resolve() evaluates expressions and walks parent chain

Example:
            Market.orders[ticker_expr].price
            → resolve() evaluates ticker_expr at runtime

Construction Pattern:

    Slot constructs Ref and passes all needed information:

    class MapSlot:
        def create_ref(self, owner_shape, parent_ref):
            return MapRef(
                field_name=self.name,
                value_type=self.value_type,
                view_type=self.view_type,  # Slot decides!
                parent_ref=parent_ref,
            )

    After construction, Ref is standalone:
        - No reference to Slot
        - All information self-contained
        - Can be passed around freely

Why This Design?
    - Separation: Slot builds, Ref operates
    - Independence: Refs don't depend on Slot lifecycle
    - Performance: Static path cached at construction
    - Flexibility: Each ref type can customize resolution
    - Type safety: Generic type parameter for value_type

Example:
    # Concrete implementation (in behavior/refs.py)
    class ValueRef(Ref):
        def __init__(self, field_name, value_type, view_type, parent_ref):
            self.field_name = field_name
            self.value_type = value_type
            self.view_type = view_type
            self.parent_ref = parent_ref

            # Compute static_path and is_dynamic
            if parent_ref is None:
                self.static_path = (field_name,)
                self.is_dynamic = False
            # ... more logic
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .term import LValue


if TYPE_CHECKING:
    from redwood.loc import key
    from redwood.view import View

    from ..types import Context


__all__ = [
    "Ref",
]


class Ref[T](LValue, ABC):
    """Abstract base for all reference types.

    Refs are addressable locations that store:
    - Type information (value_type, view_type)
    - Navigation chain (parent_ref, field_name)
    - Resolution cache (static_path, is_dynamic)

    Concrete implementations must define how they:
    - Resolve to paths
    - Navigate to nested fields
    - Create operations
    """

    # ---- Required attributes (set by concrete classes) ----

    field_name: key.KeySegment
    """Name of the field this ref points to."""

    value_type: type[T]
    """Type of value at this location (int, Order, etc.)."""

    view_type: type[View]
    """View class to use for accessing parent container."""

    parent_ref: Ref | None
    """Parent reference in navigation chain (None if root)."""

    static_path: key.Key | None
    """Cached path segments if fully static (None if dynamic)."""

    is_dynamic: bool
    """Whether this ref contains runtime-evaluated components."""

    # ---- LValue contract (must implement) ----

    @abstractmethod
    def resolve(self, context: Context) -> key.Key:
        """Resolve reference to concrete path segments.

        Static refs: Return cached static_path (O(1))
        Dynamic refs: Evaluate expressions and walk parent chain

        Args:
            context: Context for evaluating dynamic components

        Returns:
            Tuple of path segments leading to this location
        """
        ...

    @abstractmethod
    def parent(self) -> Ref | None:
        """Return parent reference in chain.

        Returns:
            Parent Ref, or None if root
        """
        ...

    @abstractmethod
    def last_segment(self) -> key.KeySegment:
        """Return the last segment in the path.

        For most refs, this is field_name.
        For dynamic refs, might be "<dynamic>" placeholder.

        Returns:
            Last path segment (str or int)
        """
        ...

    # ---- Term contract ----

    def execute(self, context: Context) -> Ref:
        """Execute returns self - refs are locations, not computations.

        Args:
            context: Unused (refs don't execute)

        Returns:
            Self (the location)
        """
        return self
