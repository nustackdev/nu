"""Path term implementations.

Provides navigable paths to tree locations with schema-guided access.
Supports both static and dynamic path resolution.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from redwood.dsl.term import PathTerm


if TYPE_CHECKING:
    from redwood.tree.context import ContextType
    from redwood.tree.tree import Tree

    from .operations import GetOperation, SetOperation
    from .schema import PrimitiveField, SchemaField


T = TypeVar("T")  # Schema type


class DocumentPath[T](PathTerm):
    """Path to a nested document (schema instance).

    Represents a location containing a nested schema structure.
    Provides navigation to nested fields via schema definitions.

    Supports dynamic parents - if parent has dynamic components,
    this path inherits that property.

    Example:
        User.profile  # DocumentPath[Profile]
        User.profile.email  # PrimitivePath[str] (navigated from Profile schema)
    """

    def __init__(
        self,
        schema_class: type,
        field_name: str,
        field_def: SchemaField,
        parent: PathTerm | None = None,
    ) -> None:
        """Initialize document path.

        Args:
            schema_class: Schema class this path belongs to
            field_name: Name of the field
            field_def: Field definition (SchemaField)
            parent: Parent path term (if nested)
        """
        super().__init__()
        self.schema_class = schema_class
        self.field_name = field_name
        self.field_def = field_def
        self.parent = parent

        # Metadata - extract nested schema
        self.meta.schema = field_def.schema if hasattr(field_def, "schema") else None

        # View type - DocumentPath uses DictView
        from redwood.tree.view import DictView

        self.meta.view_type = DictView

        # Path resolution - handle dynamic parents
        if parent and parent.meta.has_dynamic_components:
            # Parent is dynamic - we're dynamic too
            self.meta.has_dynamic_components = True
            self.meta.resolved_path = None
        elif parent and parent.meta.resolved_path:
            # Parent is static and resolved
            self.meta.resolved_path = (*parent.meta.resolved_path, field_name)
            self.meta.has_dynamic_components = False
        else:
            # Root path
            self.meta.resolved_path = (field_name,)
            self.meta.has_dynamic_components = False

    def __getattribute__(self, name: str) -> object:
        """Navigate to nested schema fields.

        This enables User.profile.email navigation - when you access
        a field on DocumentPath, it looks up that field in the nested
        schema and returns the appropriate PathTerm.

        Args:
            name: Field name to access

        Returns:
            PathTerm for the nested field (DocumentPath or PrimitivePath)

        Raises:
            AttributeError: If field doesn't exist in schema
        """
        # Allow access to internal attributes
        if name in [
            "meta",
            "evaluate",
            "schema_class",
            "field_name",
            "field_def",
            "parent",
            "resolve_path",
            "parent_path",
            "last_segment",
        ]:
            return object.__getattribute__(self, name)

        # Get nested schema
        schema_type = object.__getattribute__(self, "meta").schema
        if schema_type and hasattr(schema_type, "_fields"):
            fields = schema_type._fields
            if name in fields:
                # Found field in nested schema - create PathTerm for it
                field_def = fields[name]

                # Delegate to field's create_path_term for extensibility
                return field_def.create_path_term(
                    schema_class=schema_type,
                    field_name=name,
                    parent=self,
                )

        # Not a schema field
        raise AttributeError(
            f"DocumentPath[{schema_type.__name__ if schema_type else '?'}] has no field '{name}'"
        )

    def evaluate(self, tree: Tree, ctx: ContextType) -> DocumentPath[T]:
        """Evaluate path - returns self (path is the location)."""
        return self

    def resolve_path(self, tree: Tree, ctx: ContextType) -> tuple[str, ...]:
        """Resolve to path segments.

        For dynamic paths, delegates to parent for resolution then appends own segment.

        Args:
            tree: Tree instance (needed for dynamic resolution)
            ctx: Context (needed for dynamic resolution)

        Returns:
            Tuple of path segments
        """
        if self.meta.has_dynamic_components:
            # Dynamic path - resolve parent first
            if self.parent:
                parent_resolved = self.parent.resolve_path(tree, ctx)
                return (*parent_resolved, self.field_name)
            else:
                # Root dynamic path (shouldn't happen normally)
                return (self.field_name,)
        else:
            # Static path - use cached resolution
            if self.meta.resolved_path:
                return self.meta.resolved_path
            return (self.field_name,)

    def parent_path(self) -> PathTerm | None:
        """Get parent path.

        Returns:
            Parent PathTerm, or None if this is root
        """
        return self.parent

    def last_segment(self) -> str:
        """Get last path segment.

        Returns:
            Field name
        """
        return self.field_name

    def __repr__(self) -> str:
        """String representation."""
        if self.parent:
            return f"{self.parent}.{self.field_name}"
        return f"{self.schema_class.__name__}.{self.field_name}"


class PrimitivePath[T](PathTerm):
    """Path to a primitive value.

    Represents a location containing a primitive value (int, str, float, etc.).
    Provides .get() and .set() operations that delegate to parent view.

    Supports dynamic parents - if parent has dynamic components,
    this path inherits that property.

    Example:
        User.age.get()  # GetOperation[int]
        User.age.set(30)  # SetOperation
    """

    def __init__(
        self,
        schema_class: type,
        field_name: str,
        field_def: PrimitiveField[T],
        parent: PathTerm | None = None,
    ) -> None:
        """Initialize primitive path.

        Args:
            schema_class: Schema class this path belongs to
            field_name: Name of the field
            field_def: Field definition (PrimitiveField)
            parent: Parent path term (if nested)
        """
        super().__init__()
        self.schema_class = schema_class
        self.field_name = field_name
        self.field_def = field_def
        self.parent = parent

        # Metadata - extract primitive type
        self.meta.primitive_type = (
            field_def.primitive_type if hasattr(field_def, "primitive_type") else None
        )

        # Parent view type - inherited from parent or default to DictView
        from redwood.tree.view import DictView

        # if parent and hasattr(parent, "meta") and parent.meta.view_type:
        #     self._parent_view_type = parent.meta.view_type
        # elif parent and hasattr(parent, "_parent_view_type"):
        #     self._parent_view_type = parent._parent_view_type
        # else:
        #     self._parent_view_type = DictView
        self._parent_view_type = DictView

        # Path resolution - handle dynamic parents
        if parent and parent.meta.has_dynamic_components:
            # Parent is dynamic - we're dynamic too
            self.meta.has_dynamic_components = True
            self.meta.resolved_path = None
        elif parent and parent.meta.resolved_path:
            # Parent is static and resolved

            self.meta.resolved_path = (*parent.meta.resolved_path, field_name)
            self.meta.has_dynamic_components = False
        else:
            # Root path
            self.meta.resolved_path = (field_name,)
            self.meta.has_dynamic_components = False

    def get(self) -> GetOperation[T]:
        """Create read operation.

        Returns GetOperation that will read this primitive value
        through the parent view's .get() method.

        Returns:
            GetOperation[T] that evaluates to the primitive value

        Example:
            value = User.age.get().evaluate(tree, ctx)  # Returns int
        """
        from redwood.dsl.operations import GetOperation

        return GetOperation(self, self._parent_view_type)

    def set(self, value: T) -> SetOperation:
        """Create write operation.

        Returns SetOperation that will write this primitive value
        through the parent view's .set() method.

        Args:
            value: Value to set (type T)

        Returns:
            SetOperation that evaluates to None (side effect)

        Example:
            User.age.set(30).evaluate(tree, ctx)  # Writes to tree
        """
        from redwood.dsl.operations import SetOperation

        return SetOperation(self, value, self._parent_view_type)

    def evaluate(self, tree: Tree, ctx: ContextType) -> PrimitivePath[T]:
        """Evaluate path - returns self (path is the location)."""
        return self

    def resolve_path(self, tree: Tree, ctx: ContextType) -> tuple[str, ...]:
        """Resolve to path segments.

        For dynamic paths, delegates to parent for resolution then appends own segment.

        Args:
            tree: Tree instance (needed for dynamic resolution)
            ctx: Context (needed for dynamic resolution)

        Returns:
            Tuple of path segments
        """
        if self.meta.has_dynamic_components:
            # Dynamic path - resolve parent first
            if self.parent:
                parent_resolved = self.parent.resolve_path(tree, ctx)
                return (*parent_resolved, self.field_name)
            else:
                # Root dynamic path (shouldn't happen normally)
                return (self.field_name,)
        else:
            # Static path - use cached resolution
            if self.meta.resolved_path:
                return self.meta.resolved_path
            return (self.field_name,)

    def parent_path(self) -> PathTerm | None:
        """Get parent path.

        Returns:
            Parent PathTerm, or None if this is root
        """
        return self.parent

    def last_segment(self) -> str:
        """Get last path segment.

        Returns:
            Field name
        """
        return self.field_name

    def __repr__(self) -> str:
        """String representation."""
        if self.parent:
            return f"{self.parent}.{self.field_name}"
        return f"{self.schema_class.__name__}.{self.field_name}"
