"""
Structural Path System for Expressions

Provides deterministic, hierarchical paths for expression execution trees.
Enables resumable and distributed execution through structural identification.
"""

from __future__ import annotations

from hashlib import md5
from typing import TYPE_CHECKING

import attrs

if TYPE_CHECKING:
    from .expression import Expression

__all__ = [
    "StructuralPath",
    "create_component",
]

INTERNAL_PREFIX = ("__",)
CANCELLATION_PREFIX = INTERNAL_PREFIX + ("c",)


@attrs.define(frozen=True, slots=True)
class StructuralPath:
    """
    Immutable structural path representing expression hierarchy.

    Uses tuple of components for deterministic, structure-based identification.
    Each component represents an expression in the execution tree.
    """

    components: tuple[str, ...] = attrs.field(factory=tuple)

    @property
    def is_root(self) -> bool:
        """Check if this is the root path."""
        return len(self.components) == 0

    @property
    def parent(self) -> StructuralPath:
        """Get the parent path."""
        if self.is_root:
            return self
        return StructuralPath(self.components[:-1])

    @property
    def last_component(self) -> str | None:
        """Get the last component in the path."""
        return self.components[-1] if self.components else None

    def append(self, component: str) -> StructuralPath:
        """Create a new path with an additional component."""
        return StructuralPath(self.components + (component,))

    def to_storage_key(self, prefix: tuple[str, ...] = CANCELLATION_PREFIX) -> tuple[str, ...]:
        """
        Convert to storage key, using MD5 hash if too long.

        Args:
            prefix: Storage key prefix (default: cancellation prefix)

        Returns:
            Storage key that fits within length constraints
        """
        path_str = "/".join(self.components)
        path_hash = md5(path_str.encode()).hexdigest()

        return CANCELLATION_PREFIX + (path_hash,)

    def __str__(self) -> str:
        """String representation for debugging."""
        return "/".join(self.components)

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"StructuralPath({self.components!r})"


def create_component(expression: Expression, index: str | int | None = None) -> str:
    """
    Create structural component for an expression.

    Args:
        expression: Expression to create component for
        index: Optional index for multiple instances of same type

    Returns:
        Deterministic component string based on structure
    """
    class_name = expression.__class__.__name__

    if index is not None:
        return f"{class_name}[{index}]"
    else:
        return class_name
