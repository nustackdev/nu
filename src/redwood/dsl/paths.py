"""Path term implementations (minimal stubs for Layer 1).

These are basic stubs to support schema field descriptors.
Full implementation comes in Layer 2.
"""

from typing import TYPE_CHECKING, Any, Generic, TypeVar

from redwood.dsl.term import PathTerm


if TYPE_CHECKING:
    from redwood.tree.context import ContextType
    from redwood.tree.tree import Tree


T = TypeVar("T")  # Schema type


class DocumentPath(PathTerm, Generic[T]):
    """Path to a nested document (schema instance).

    Represents a location containing a nested schema structure.
    Full navigation implementation comes in Layer 2.
    """

    def __init__(
        self,
        schema_class: type,
        field_name: str,
        field_def: Any,
        parent: PathTerm | None = None,
    ) -> None:
        """Initialize document path.

        Args:
            schema_class: Schema class this path belongs to
            field_name: Name of the field
            field_def: Field definition
            parent: Parent path term (if nested)
        """
        super().__init__()
        self.schema_class = schema_class
        self.field_name = field_name
        self.field_def = field_def
        self.parent = parent

        # Metadata
        self.meta.schema = field_def.schema if hasattr(field_def, "schema") else None

        # Path resolution
        if parent and parent.meta.resolved_path:
            self.meta.resolved_path = parent.meta.resolved_path + (field_name,)
        else:
            self.meta.resolved_path = (field_name,)

    def evaluate(self, tree: "Tree", ctx: "ContextType") -> "DocumentPath[T]":
        """Stub evaluation - returns self for now."""
        return self

    def resolve_path(self, tree: "Tree", ctx: "ContextType") -> tuple[str, ...]:
        """Resolve to path segments."""
        if self.meta.resolved_path:
            return self.meta.resolved_path
        return (self.field_name,)

    def parent_path(self) -> PathTerm | None:
        """Get parent path."""
        return self.parent

    def last_segment(self) -> str:
        """Get last segment."""
        return self.field_name

    def __repr__(self) -> str:
        if self.parent:
            return f"{self.parent}.{self.field_name}"
        return f"{self.schema_class.__name__}.{self.field_name}"


class PrimitivePath(PathTerm, Generic[T]):
    """Path to a primitive value.

    Represents a location containing a primitive value (int, str, float, etc.).
    Full operations implementation comes in Layer 2.
    """

    def __init__(
        self,
        schema_class: type,
        field_name: str,
        field_def: Any,
        parent: PathTerm | None = None,
    ) -> None:
        """Initialize primitive path.

        Args:
            schema_class: Schema class this path belongs to
            field_name: Name of the field
            field_def: Field definition
            parent: Parent path term (if nested)
        """
        super().__init__()
        self.schema_class = schema_class
        self.field_name = field_name
        self.field_def = field_def
        self.parent = parent

        # Metadata
        self.meta.primitive_type = (
            field_def.primitive_type if hasattr(field_def, "primitive_type") else None
        )

        # Path resolution
        if parent and parent.meta.resolved_path:
            self.meta.resolved_path = parent.meta.resolved_path + (field_name,)
        else:
            self.meta.resolved_path = (field_name,)

    def evaluate(self, tree: "Tree", ctx: "ContextType") -> "PrimitivePath[T]":
        """Stub evaluation - returns self for now."""
        return self

    def resolve_path(self, tree: "Tree", ctx: "ContextType") -> tuple[str, ...]:
        """Resolve to path segments."""
        if self.meta.resolved_path:
            return self.meta.resolved_path
        return (self.field_name,)

    def parent_path(self) -> PathTerm | None:
        """Get parent path."""
        return self.parent

    def last_segment(self) -> str:
        """Get last segment."""
        return self.field_name

    def __repr__(self) -> str:
        if self.parent:
            return f"{self.parent}.{self.field_name}"
        return f"{self.schema_class.__name__}.{self.field_name}"
