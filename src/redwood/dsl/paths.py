"""Path term implementations.

PathTerms represent navigable locations in the tree (L-values). They support:
- Field access: User.name
- Index access: User.orders["AAPL"]
- Dynamic indices: User.orders[User.current_symbol]

All path operations are lazy and construct term trees without tree access.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from redwood.dsl.exceptions import DSLPathError
from redwood.dsl.metadata import TermMetadata
from redwood.dsl.term import PathTerm, ValueTerm
from redwood.dsl.types import Empty, TermResult


if TYPE_CHECKING:
    from redwood.dsl.schema import Field, Schema
    from redwood.tree import ContextType, Tree

__all__ = ["FieldPath", "IndexPath", "RootPath"]


@dataclass(frozen=True)
class RootPath(PathTerm):
    """Root path in schema: User, Market, etc.

    Represents the entry point for a schema-based path traversal.

    Attributes:
        name: Root name (typically schema class name)
        schema: Schema class this root represents
    """

    name: str
    schema: type[Schema] | None = None

    def __init__(self, name: str, schema: type[Schema] | None = None) -> None:
        """Initialize root path.

        Args:
            name: Root name
            schema: Schema class for this root
        """
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "schema", schema)

        # Initialize base Term (manually since frozen dataclass)
        super(PathTerm, self).__init__()

        # Set metadata
        meta = TermMetadata(
            is_pure=True,
            resolved_path=(name,),
            has_dynamic_components=False,
            schema=schema,
        )
        object.__setattr__(self, "meta", meta)

    def __getattr__(self, name: str) -> FieldPath:
        """Enable User.field access.

        Args:
            name: Field name

        Returns:
            FieldPath for User.field

        Raises:
            DSLPathError: If schema doesn't have field
        """
        # Avoid infinite recursion for internal attributes
        if name.startswith("_") or name in ("name", "schema", "meta"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        # Check schema if available
        if self.schema is not None:
            if not self.schema.has_field(name):
                msg = f"Schema {self.schema.__name__} has no field '{name}'"
                raise DSLPathError(msg)
            field_def = self.schema.get_field(name)
        else:
            field_def = None

        return FieldPath(parent=self, field_name=name, field_def=field_def)

    def __getitem__(self, key: Any) -> IndexPath:
        """Enable User[key] access.

        Args:
            key: Index key (string, int, or ValueTerm)

        Returns:
            IndexPath for User[key]
        """
        return IndexPath(parent=self, index=key)

    def evaluate(self, tree: Tree, ctx: ContextType) -> TermResult[Any]:
        """Evaluate root path (returns Empty - root itself has no value).

        Args:
            tree: Tree instance
            ctx: Context

        Returns:
            Empty (root is just a namespace)
        """
        return Empty

    def resolve_path(self, tree: Tree, ctx: ContextType) -> tuple[str, ...]:
        """Resolve to path tuple.

        Args:
            tree: Tree instance (not used for static root)
            ctx: Context (not used for static root)

        Returns:
            Tuple with root name
        """
        return (self.name,)

    def parent_path(self) -> PathTerm | None:
        """Get parent path.

        Returns:
            None (root has no parent)
        """
        return None

    def last_segment(self) -> str:
        """Get last segment.

        Returns:
            Root name
        """
        return self.name


@dataclass(frozen=True)
class FieldPath(PathTerm):
    """Field access path: User.name, Market.orders.

    Represents accessing a named field within a parent path.

    Attributes:
        parent: Parent path
        field_name: Field name being accessed
        field_def: Field definition from schema (if available)
    """

    parent: PathTerm
    field_name: str
    field_def: Field | None = None

    def __init__(
        self,
        parent: PathTerm,
        field_name: str,
        field_def: Field | None = None,
    ) -> None:
        """Initialize field path.

        Args:
            parent: Parent path
            field_name: Field name
            field_def: Field definition from schema
        """
        object.__setattr__(self, "parent", parent)
        object.__setattr__(self, "field_name", field_name)
        object.__setattr__(self, "field_def", field_def)

        super(PathTerm, self).__init__()

        # Compute metadata
        parent_path = parent.meta.resolved_path
        if parent_path is not None and not parent.meta.has_dynamic_components:
            resolved = parent_path + (field_name,)
        else:
            resolved = None

        meta = TermMetadata(
            is_pure=True,
            resolved_path=resolved,
            has_dynamic_components=parent.meta.has_dynamic_components,
            dependencies=parent.meta.dependencies,
            primitive_type=field_def.primitive if field_def and field_def.is_primitive() else None,
            schema=field_def.schema if field_def and field_def.has_schema() else None,
            view_type=field_def.view if field_def and field_def.is_container() else None,
        )
        object.__setattr__(self, "meta", meta)

    def __getattr__(self, name: str) -> FieldPath:
        """Enable User.profile.email chaining.

        Args:
            name: Field name

        Returns:
            FieldPath for nested field

        Raises:
            DSLPathError: If field is primitive (can't navigate further)
        """
        # Avoid infinite recursion
        if name.startswith("_") or name in ("parent", "field_name", "field_def", "meta"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        # Check if current field is primitive
        if self.field_def and self.field_def.is_primitive():
            msg = f"Cannot navigate through primitive field '{self.field_name}'"
            raise DSLPathError(msg)

        # Check nested schema if available
        if self.field_def and self.field_def.has_schema():
            nested_schema = self.field_def.schema
            if nested_schema and not nested_schema.has_field(name):
                msg = f"Schema {nested_schema.__name__} has no field '{name}'"
                raise DSLPathError(msg)
            field_def = nested_schema.get_field(name) if nested_schema else None
        else:
            field_def = None

        return FieldPath(parent=self, field_name=name, field_def=field_def)

    def __getitem__(self, key: Any) -> IndexPath:
        """Enable User.orders["AAPL"] access.

        Args:
            key: Index key

        Returns:
            IndexPath for indexed access

        Raises:
            DSLPathError: If field is primitive
        """
        # Check if current field is primitive
        if self.field_def and self.field_def.is_primitive():
            msg = f"Cannot index primitive field '{self.field_name}'"
            raise DSLPathError(msg)

        return IndexPath(parent=self, index=key)

    def evaluate(self, tree: Tree, ctx: ContextType) -> TermResult[Any]:
        """Evaluate field path by reading through parent view.

        Args:
            tree: Tree instance
            ctx: Context for data access

        Returns:
            Field value, or Empty if doesn't exist
        """
        from redwood.dsl.types import Empty

        try:
            # Resolve parent path
            parent_segments = self.parent.resolve_path(tree, ctx)

            # Navigate to parent container
            current = tree
            for segment in parent_segments:
                current = current.at(segment)

            # Determine parent view type
            if self.parent.meta.view_type is not None:
                # Use specified view
                view = current.view(self.parent.meta.view_type, ctx=ctx)
            else:
                # Default to dict view
                from redwood.tree import DictView

                view = current.view(DictView, ctx=ctx)

            # Read field through view
            if hasattr(view, "get"):
                result = view.get(self.field_name)
                return result if result is not None else Empty
            else:
                msg = f"View {type(view).__name__} doesn't support .get() operation"
                raise DSLPathError(msg)

        except (KeyError, AttributeError, IndexError):
            return Empty

    def resolve_path(self, tree: Tree, ctx: ContextType) -> tuple[str, ...]:
        """Resolve to path tuple.

        Args:
            tree: Tree instance
            ctx: Context

        Returns:
            Tuple of path segments
        """
        parent_path = self.parent.resolve_path(tree, ctx)
        return parent_path + (self.field_name,)

    def parent_path(self) -> PathTerm:
        """Get parent path.

        Returns:
            Parent PathTerm
        """
        return self.parent

    def last_segment(self) -> str:
        """Get last segment.

        Returns:
            Field name
        """
        return self.field_name


@dataclass(frozen=True)
class IndexPath(PathTerm):
    """Index access path: User.orders["AAPL"], items[User.current_index].

    Represents indexing into a container. Index can be:
    - Static: a literal value ("AAPL", 0)
    - Dynamic: a term that evaluates to an index (User.current_symbol)

    Attributes:
        parent: Parent path
        index: Index value (literal or ValueTerm)
    """

    parent: PathTerm
    index: Any  # Can be literal or ValueTerm

    def __init__(self, parent: PathTerm, index: Any) -> None:
        """Initialize index path.

        Args:
            parent: Parent path
            index: Index (literal value or ValueTerm for dynamic indices)
        """
        # Auto-convert PathTerm indices to ValueTerm via .get()
        if isinstance(index, PathTerm):
            index = index.get()

        object.__setattr__(self, "parent", parent)
        object.__setattr__(self, "index", index)

        super(PathTerm, self).__init__()

        # Determine if index is dynamic
        is_dynamic = isinstance(index, ValueTerm)

        # Compute metadata
        if (
            not is_dynamic
            and parent.meta.resolved_path is not None
            and not parent.meta.has_dynamic_components
        ):
            resolved = parent.meta.resolved_path + (str(index),)
        else:
            resolved = None

        dependencies = parent.meta.dependencies
        if isinstance(index, ValueTerm):
            dependencies = dependencies | index.meta.dependencies

        meta = TermMetadata(
            is_pure=True,
            resolved_path=resolved,
            has_dynamic_components=is_dynamic or parent.meta.has_dynamic_components,
            dependencies=dependencies,
            schema=parent.meta.schema,  # Inherit schema from parent container
        )
        object.__setattr__(self, "meta", meta)

    def __getattr__(self, name: str) -> FieldPath:
        """Enable User.orders["AAPL"].price chaining.

        Args:
            name: Field name

        Returns:
            FieldPath for nested field
        """
        # Avoid infinite recursion
        if name.startswith("_") or name in ("parent", "index", "meta"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        # Check nested schema if available
        if self.parent.meta.schema is not None:
            nested_schema = self.parent.meta.schema
            if not nested_schema.has_field(name):
                msg = f"Schema {nested_schema.__name__} has no field '{name}'"
                raise DSLPathError(msg)
            field_def = nested_schema.get_field(name)
        else:
            field_def = None

        return FieldPath(parent=self, field_name=name, field_def=field_def)

    def __getitem__(self, key: Any) -> IndexPath:
        """Enable User.orders["AAPL"]["nested"] access.

        Args:
            key: Index key

        Returns:
            IndexPath for further indexing
        """
        return IndexPath(parent=self, index=key)

    def evaluate(self, tree: Tree, ctx: ContextType) -> TermResult[Any]:
        """Evaluate index path by reading through parent view.

        Args:
            tree: Tree instance
            ctx: Context for data access

        Returns:
            Indexed value, or Empty if doesn't exist
        """
        from redwood.dsl.types import Empty, is_special

        try:
            # Resolve parent path
            parent_segments = self.parent.resolve_path(tree, ctx)

            # Navigate to parent container
            current = tree
            for segment in parent_segments:
                current = current.at(segment)

            # Resolve index (evaluate if dynamic)
            if isinstance(self.index, ValueTerm):
                resolved_index = self.index.evaluate(tree, ctx)
                if is_special(resolved_index):
                    return Empty  # Can't use special value as index
            else:
                resolved_index = self.index

            # Determine parent view type
            if self.parent.meta.view_type is not None:
                view = current.view(self.parent.meta.view_type, ctx=ctx)
            else:
                # Default to dict view
                from redwood.tree import DictView

                view = current.view(DictView, ctx=ctx)

            # Read through view
            if hasattr(view, "get"):
                result = view.get(resolved_index)
                return result if result is not None else Empty
            elif hasattr(view, "at"):
                # For ListView
                result = view.at(resolved_index).get()
                return result if result is not None else Empty
            else:
                msg = f"View {type(view).__name__} doesn't support indexing"
                raise DSLPathError(msg)

        except (KeyError, AttributeError, IndexError):
            return Empty

    def resolve_path(self, tree: Tree, ctx: ContextType) -> tuple[str, ...]:
        """Resolve to path tuple.

        Args:
            tree: Tree instance (needed for dynamic indices)
            ctx: Context (needed for dynamic indices)

        Returns:
            Tuple of path segments
        """
        parent_path = self.parent.resolve_path(tree, ctx)

        # Resolve index
        if isinstance(self.index, ValueTerm):
            from redwood.dsl.types import is_special

            resolved_index = self.index.evaluate(tree, ctx)
            if is_special(resolved_index):
                msg = "Cannot resolve path with Empty/NaN index"
                raise DSLPathError(msg)
            index_str = str(resolved_index)
        else:
            index_str = str(self.index)

        return parent_path + (index_str,)

    def parent_path(self) -> PathTerm:
        """Get parent path.

        Returns:
            Parent PathTerm
        """
        return self.parent

    def last_segment(self) -> str | ValueTerm:
        """Get last segment.

        Returns:
            Index as string (static) or ValueTerm (dynamic)
        """
        if isinstance(self.index, ValueTerm):
            return self.index
        return str(self.index)
