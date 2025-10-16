"""Metadata system for term nodes.

This module provides the TermMetadata dataclass that tracks static information
about terms during construction. Metadata is immutable and computed eagerly to
enable optimization and analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from redwood.dsl.schema import Schema

__all__ = ["TermMetadata"]


@dataclass(frozen=True)
class TermMetadata:
    """Metadata attached to every term node.

    Computed during term construction (not evaluation) and immutable for
    thread-safety and optimization passes.

    Attributes:
        is_pure: Whether term has no side effects (queries vs commands)
        has_side_effects: Whether term modifies tree state
        value_type: Expected Python type of evaluation result (int, float, str, bool)
        primitive_type: For primitive fields, the primitive type
        schema: For container fields, the nested schema
        view_type: For container fields, the view class (DictView, ListView, etc.)
        resolved_path: For static paths, the tuple of path segments
        has_dynamic_components: Whether path contains runtime-evaluated indices
        dependencies: Set of path strings this term reads during evaluation
        is_constant: Whether term can be evaluated once and cached
    """

    # Purity analysis
    is_pure: bool = True
    has_side_effects: bool = False

    # Type information
    value_type: type | None = None
    primitive_type: type | None = None

    # Schema/View info
    schema: Schema | None = None
    view_type: type | None = None

    # Path analysis
    resolved_path: tuple[str, ...] | None = None
    has_dynamic_components: bool = False

    # Dependency tracking (paths read during evaluation)
    dependencies: frozenset[str] = field(default_factory=frozenset)

    # Optimization hints
    is_constant: bool = False

    def merge(self, **updates: Any) -> TermMetadata:
        """Create new metadata with specified updates.

        Args:
            **updates: Fields to update

        Returns:
            New TermMetadata instance with updates applied

        Examples:
            >>> meta = TermMetadata(is_pure=True)
            >>> meta2 = meta.merge(is_pure=False, has_side_effects=True)
            >>> meta2.is_pure
            False
        """
        return replace(self, **updates)

    def merge_dependencies(self, *others: TermMetadata) -> TermMetadata:
        """Merge dependencies from multiple metadata objects.

        Used when constructing composite terms that depend on multiple sub-terms.

        Args:
            *others: Other metadata objects to merge dependencies from

        Returns:
            New TermMetadata with union of all dependencies

        Examples:
            >>> meta1 = TermMetadata(dependencies=frozenset(["User.age"]))
            >>> meta2 = TermMetadata(dependencies=frozenset(["User.name"]))
            >>> merged = meta1.merge_dependencies(meta2)
            >>> merged.dependencies
            frozenset({'User.age', 'User.name'})
        """
        all_deps = self.dependencies
        for other in others:
            all_deps = all_deps | other.dependencies
        return self.merge(dependencies=all_deps)

    def mark_impure(self) -> TermMetadata:
        """Mark this metadata as impure (has side effects).

        Convenience method for command terms.

        Returns:
            New TermMetadata marked as impure
        """
        return self.merge(is_pure=False, has_side_effects=True)

    def with_value_type(self, value_type: type) -> TermMetadata:
        """Set the expected value type.

        Args:
            value_type: Expected Python type of evaluation result

        Returns:
            New TermMetadata with value_type set
        """
        return self.merge(value_type=value_type)

    def with_dependencies(self, *paths: str) -> TermMetadata:
        """Add dependencies to this metadata.

        Args:
            *paths: Path strings to add as dependencies

        Returns:
            New TermMetadata with added dependencies
        """
        new_deps = self.dependencies | frozenset(paths)
        return self.merge(dependencies=new_deps)

    def as_constant(self) -> TermMetadata:
        """Mark this metadata as constant (can be cached).

        Returns:
            New TermMetadata marked as constant
        """
        return self.merge(is_constant=True)
