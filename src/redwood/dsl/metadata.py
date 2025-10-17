"""Metadata system for term nodes.

TermMetadata tracks static information about terms during construction.
Computed eagerly to enable optimization and analysis.
"""

from typing import Any


class TermMetadata:
    """Metadata attached to every term node.

    Computed during term construction (not evaluation) for optimization
    and static analysis.

    Attributes:
        is_pure: Whether term has no side effects (queries vs commands)
        has_side_effects: Whether term modifies tree state
        value_type: Expected Python type of evaluation result
        primitive_type: For primitive fields, the primitive type
        schema: For container fields, the nested schema
        view_type: For container fields, the view class
        resolved_path: For static paths, the tuple of path segments
        has_dynamic_components: Whether path contains runtime-evaluated indices
        dependencies: Set of path strings this term reads during evaluation
        is_constant: Whether term can be evaluated once and cached
    """

    def __init__(
        self,
        is_pure: bool = True,
        has_side_effects: bool = False,
        value_type: type | None = None,
        primitive_type: type | None = None,
        schema: Any = None,  # Schema type
        view_type: type | None = None,
        resolved_path: tuple[str, ...] | None = None,
        has_dynamic_components: bool = False,
        dependencies: frozenset[str] | None = None,
        is_constant: bool = False,
    ) -> None:
        """Initialize metadata with provided values."""
        self.is_pure = is_pure
        self.has_side_effects = has_side_effects
        self.value_type = value_type
        self.primitive_type = primitive_type
        self.schema = schema
        self.view_type = view_type
        self.resolved_path = resolved_path
        self.has_dynamic_components = has_dynamic_components
        self.dependencies = dependencies if dependencies is not None else frozenset()
        self.is_constant = is_constant

    def merge(self, **updates: Any) -> "TermMetadata":
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
        # Start with current values
        current = {
            "is_pure": self.is_pure,
            "has_side_effects": self.has_side_effects,
            "value_type": self.value_type,
            "primitive_type": self.primitive_type,
            "schema": self.schema,
            "view_type": self.view_type,
            "resolved_path": self.resolved_path,
            "has_dynamic_components": self.has_dynamic_components,
            "dependencies": self.dependencies,
            "is_constant": self.is_constant,
        }
        # Apply updates
        current.update(updates)
        return TermMetadata(**current)

    def merge_dependencies(self, *others: "TermMetadata") -> "TermMetadata":
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

    def mark_impure(self) -> "TermMetadata":
        """Mark this metadata as impure (has side effects).

        Convenience method for command terms.

        Returns:
            New TermMetadata marked as impure
        """
        return self.merge(is_pure=False, has_side_effects=True)

    def with_value_type(self, value_type: type) -> "TermMetadata":
        """Set the expected value type.

        Args:
            value_type: Expected Python type of evaluation result

        Returns:
            New TermMetadata with value_type set
        """
        return self.merge(value_type=value_type)

    def with_dependencies(self, *paths: str) -> "TermMetadata":
        """Add dependencies to this metadata.

        Args:
            *paths: Path strings to add as dependencies

        Returns:
            New TermMetadata with added dependencies
        """
        new_deps = self.dependencies | frozenset(paths)
        return self.merge(dependencies=new_deps)

    def as_constant(self) -> "TermMetadata":
        """Mark this metadata as constant (can be cached).

        Returns:
            New TermMetadata marked as constant
        """
        return self.merge(is_constant=True)
