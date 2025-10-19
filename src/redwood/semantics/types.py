"""Core type definitions for Redwood Semantics.

Provides type aliases and shared data structures used across all layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from redwood.tree.context import ContextType
    from redwood.tree.tree import Tree
    from redwood.tree.view import BaseView
    from redwood.types import Value

    from .core.term import RValue


# ============================================================================
# Path Types
# ============================================================================

type PathSegment = str | int
"""A single segment in a path - either a string key or integer index."""

type TuplePath = tuple[PathSegment, ...]

# ============================================================================
# Primitive Node Value Types
# ============================================================================

type PrimitiveNodeValue = Value


# ============================================================================
# Execution types
# ============================================================================


@dataclass(frozen=True)
class Context:
    """Execution context for operations and commands.

    Bundles together the tree instance and storage context needed
    for executing operations.

    Attributes:
        tree: Tree instance for navigation
        storage_context: Context for data access (transaction or snapshot)
    """

    tree: Tree
    storage_context: ContextType


# ============================================================================
# Special Values
# ============================================================================


class SpecialValue:
    """Sentinel values for semantics evaluation.

    - Empty: Value doesn't exist
    - NaN: Operation not applicable
    """

    pass


class _Empty(SpecialValue):
    """Sentinel for non-existent values."""

    def __repr__(self) -> str:
        return "Empty"


class _NaN(SpecialValue):
    """Sentinel for invalid operations."""

    def __repr__(self) -> str:
        return "NaN"


# Singleton instances
Empty = _Empty()
NaN = _NaN()


def is_empty(value: object) -> bool:
    """Check if value is Empty sentinel."""
    return isinstance(value, _Empty)


def is_nan(value: object) -> bool:
    """Check if value is NaN sentinel."""
    return isinstance(value, _NaN)


def is_special(value: object) -> bool:
    """Check if value is any special sentinel."""
    return isinstance(value, SpecialValue)


def propagate_special(*values: object) -> SpecialValue | None:
    """Propagate special values through operations.

    Rules:
    1. Any NaN → NaN
    2. Any Empty → NaN
    3. All normal → None

    Returns:
        NaN if any special value present, None otherwise
    """
    for val in values:
        if is_nan(val):
            return NaN

    for val in values:
        if is_empty(val):
            return NaN

    return None


# ============================================================================
# Reference resolution types (Refs)
# ============================================================================


@dataclass(frozen=True)
class RefStaticSegment:
    """A static path segment in reference resolution."""

    view_type: type[BaseView]
    key: PathSegment


@dataclass(frozen=True)
class RefDynamicSegment:
    """A dynamic path segment in reference resolution."""

    view_type: type[BaseView]
    key_expr: RValue


RefResolution = tuple[RefStaticSegment | RefDynamicSegment, ...]
