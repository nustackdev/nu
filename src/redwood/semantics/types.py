"""Core type definitions for Redwood Semantics.

Provides type aliases and shared data structures used across all layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from redwood.abc import KeyComponent
    from redwood.backends import StorageContextType
    from redwood.tree import BaseView, Tree

    from .core.term import RValue


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
    storage_context: StorageContextType


@dataclass(frozen=True)
class RefStaticSegment:
    """A static path segment in reference resolution."""

    view_type: type[BaseView]
    key: KeyComponent


@dataclass(frozen=True)
class RefDynamicSegment:
    """A dynamic path segment in reference resolution."""

    view_type: type[BaseView]
    key_expr: RValue


RefResolution = tuple[RefStaticSegment | RefDynamicSegment, ...]
