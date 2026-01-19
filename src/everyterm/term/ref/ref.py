"""Typed reference to storage location.

Term                        - executable node
├── LValue                  - addressable location (has path)
│   └── Ref                 - typed reference to storage location
│       ├── ViewRef         - reference to container (dict, list, set)
│       └── PrimitiveRef    - reference to leaf value (int, str, etc.)
"""

from __future__ import annotations

from abc import ABC
from logging import getLogger
from typing import TYPE_CHECKING

from everyterm.term import LValue


if TYPE_CHECKING:
    from everyterm.shape import Shape


__all__ = [
    "Ref",
]


logger = getLogger(__name__)


class Ref[T](LValue[T], ABC):
    """Typed reference to a location.

    Combines addressability (LValue) with type information.
    Refs are both locations AND terms (dual nature):

    As Ref:
    - Can resolve to paths
    - Can navigate to parent

    As Term:
    - Can execute (returns self)
    - Can be used in children tuples

    Generic type T specifies value type at this location:
        Ref[float] → location holding float
        Ref[str]   → location holding string
        Ref[Order] → location holding Order shape

    Concrete implementations (see in standard library or ecosystem repo):
        ValueRef[T]     - primitive values
        ShapeRef[T]     - nested structures
        MapRef[K,V]     - mapping containers
        MapItemRef[T]   - specific map entries

    Implementations determine:
    - Storage strategy (caching, lazy evaluation)
    - Navigation behavior (nested field access)
    - Available operations (get/set for values, keys/items for maps)
    """

    def __init__(self, parent_ref: Ref | None, owner_shape: type[Shape] | None) -> None:
        """Init Ref."""
        self.parent_ref = parent_ref
        self.owner_shape = owner_shape

    @property
    def is_pure(self) -> bool:
        """Refs are always pure.

        Returns:
            True - refs never have side effects
        """
        return True

    @property
    def parent(self) -> Ref | None:
        """Get parent location in the navigation chain.

        Used for path construction and hierarchy traversal.
        Root locations return None.

        Returns:
            Parent Ref, or None if this is root
        """
        return self.parent_ref

    def get_owner_shape(self) -> type[Shape] | None:
        """Get the Shape class this Ref was created by."""
        if self.owner_shape is not None:
            return self.owner_shape

        if self.parent is not None:
            return self.parent.owner_shape

        return None

    def get_root_shape(self) -> type[Shape] | None:
        """Get the Shape class this Ref was originated from."""
        if self.parent is not None:
            return self.parent.get_root_shape()

        if self.owner_shape is not None:
            return self.owner_shape

        return None
