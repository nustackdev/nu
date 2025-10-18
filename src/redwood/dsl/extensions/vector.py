"""Vector extension - Ordered collection with integer indices.

VectorField: Ordered collection where items can be any type (homogeneous)
VectorPath: Container-level path (type annotation in schema)
VectorItemPath: Item-level path with dynamic index access

Supports ANY type:
- Primitives: Vector[int], Vector[str], Vector[float]
- Schemas: Vector[Order], Vector[Profile]
- Nested: Vector[Collection[Order]] (future)

Supports DYNAMIC INDICES:
- Static: User.tags[0]
- Dynamic: User.tags[User.current_idx.get()]

Includes ListView-specific operations:
- ListGetOperation: Read from ListView with integer indices
- ListSetOperation: Write to ListView with integer indices

Example:
    class Order(Schema):
        volume: PrimitivePath[int] = PrimitiveField(int)
        price: PrimitivePath[float] = PrimitiveField(float)

    class User(Schema):
        current_idx: PrimitivePath[int] = PrimitiveField(int)
        tags: VectorPath[str] = VectorField(str)
        orders: VectorPath[Order] = VectorField(Order)

    # Static index + primitive
    User.tags[0].get()

    # Dynamic index + schema
    User.orders[User.current_idx.get()].volume.get()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from redwood.dsl.schema import Field
from redwood.dsl.term import CommandTerm, PathTerm, ValueTerm
from redwood.dsl.types import Empty


if TYPE_CHECKING:
    from redwood.tree.context import ContextType
    from redwood.tree.tree import Tree


# ============================================================================
# ListView-Specific Operations (Integer Indices)
# ============================================================================


class ListGetOperation[T](ValueTerm):
    """Pure read operation from ListView - uses integer indices.

    Similar to GetOperation but:
    - Works with ListView instead of DictView
    - Keeps indices as integers (not strings)
    - Enables range selection and list-specific operations

    Example:
        op = User.tags[0].get()  # ListGetOperation
        value = op.evaluate(tree, ctx)  # Returns str
    """

    def __init__(self, path: PathTerm) -> None:
        """Initialize list get operation.

        Args:
            path: Path to read from (must resolve to integer indices)
        """
        super().__init__()
        self.path = path

        # Inherit metadata from path
        self.meta.value_type = path.meta.primitive_type
        self.meta.dependencies = path.meta.dependencies

    def evaluate(self, tree: Tree, ctx: ContextType) -> T:
        """Read value through ListView with integer indices.

        Args:
            tree: Tree instance
            ctx: Context for data access

        Returns:
            Value at path (type T), or Empty if not found
        """
        try:
            # Resolve path to segments (integers for list indices)
            path_components = self.path.resolve_path(tree, ctx)

            if not path_components:
                return Empty

            # Navigate to the list container and final index
            from redwood.tree.view import ListView

            # Handle different path depths
            if len(path_components) == 1:
                # Single segment - direct list access at root
                view = tree.view(ListView, ctx=ctx)
                index = int(path_components[0])
                result = view.get(index)
                return result if result is not None else Empty

            # Multiple segments - navigate to parent container
            parent_path = path_components[:-1]
            final_index = int(path_components[-1])

            # Navigate to parent (may be nested)
            current = tree
            for i, segment in enumerate(parent_path):
                # Try integer index first (for lists), fallback to string key (for dicts)
                current = current.at(segment)

            # Get ListView from parent and read final index
            view = current.view(ListView, ctx=ctx)
            result = view.get(final_index)

            return result if result is not None else Empty

        except (KeyError, AttributeError, IndexError, ValueError):
            # Graceful failure - return Empty
            return Empty


class ListSetOperation(CommandTerm):
    """Impure write operation to ListView - uses integer indices.

    Similar to SetOperation but:
    - Works with ListView instead of DictView
    - Keeps indices as integers (not strings)
    - Enables range operations and list-specific mutations

    Example:
        op = User.tags[0].set("python")  # ListSetOperation
        op.evaluate(tree, ctx)  # Writes to list
    """

    def __init__(self, path: PathTerm, value: Any) -> None:
        """Initialize list set operation.

        Args:
            path: Path to write to (must resolve to integer indices)
            value: Value to set
        """
        super().__init__()
        self.path = path
        self.value = value

        # Inherit metadata from path
        self.meta.dependencies = path.meta.dependencies

    def evaluate(self, tree: Tree, ctx: ContextType) -> None:
        """Write value through ListView with integer indices.

        Args:
            tree: Tree instance
            ctx: Context for data access (must support writes)

        Returns:
            None (side effect operation)
        """
        try:
            # Resolve path to segments (integers for list indices)
            path_components = self.path.resolve_path(tree, ctx)

            if not path_components:
                raise ValueError("Cannot set root path")

            from redwood.tree.view import ListView

            # Handle different path depths
            if len(path_components) == 1:
                # Single segment - direct list access at root
                view = tree.view(ListView, ctx=ctx)
                index = int(path_components[0])
                view.set(index, self.value)
                return

            # Multiple segments - navigate to parent container
            parent_path = path_components[:-1]
            final_index = int(path_components[-1])

            # Navigate to parent (may be nested)
            current = tree
            for segment in parent_path:
                # Try integer index first (for lists), fallback to string key (for dicts)
                try:
                    current = current.at(int(segment))
                except (ValueError, TypeError):
                    current = current.at(segment)

            # Get ListView from parent and write final index
            view = current.view(ListView, ctx=ctx)
            view.set(final_index, self.value)

        except (KeyError, AttributeError, IndexError, ValueError):
            # Let write errors propagate - these are real issues
            raise


# ============================================================================
# Vector Field Types
# ============================================================================


class VectorField[T](Field):
    """Ordered collection field with homogeneous values of ANY type.

    All values in the vector must be the same type, but that type
    can be anything: primitives, schemas, or nested structures.

    Access via integer indices: path[index] or path[expr]

    Example:
        class User(Schema):
            # Primitive vector
            tags: VectorPath[str] = VectorField(str)
            # Schema vector
            orders: VectorPath[Order] = VectorField(Order)
    """

    def __init__(self, item_type: type[T]) -> None:
        """Initialize vector field.

        Args:
            item_type: Type of items in vector (any type)
        """
        self.item_type = item_type

        # Detect if item_type is primitive or schema
        self.is_primitive = item_type in (int, float, str, bool, bytes, dict, list)

    def create_path_term(
        self,
        schema_class: type,
        field_name: str,
        parent: PathTerm | None = None,
    ) -> PathTerm:
        """Create VectorPath for vector access."""
        return VectorPath(
            schema_class=schema_class,
            field_name=field_name,
            field_def=self,
            parent=parent,
        )


class VectorPath[T](PathTerm):
    """Path to a vector field - supports dynamic index access.

    This is the TYPE ANNOTATION used in schemas!

    Provides __getitem__ for accessing specific indices in the vector.
    Supports both static indices (integers) and dynamic indices (expressions).

    Example:
        # In schema
        tags: VectorPath[str] = VectorField(str)

        # Static index
        User.tags[0]  # Index known at construction

        # Dynamic index
        User.tags[User.current_idx.get()]  # Index evaluated at runtime
    """

    def __init__(
        self,
        schema_class: type,
        field_name: str,
        field_def: VectorField[T],
        parent: PathTerm | None = None,
    ) -> None:
        """Initialize vector path.

        Args:
            schema_class: Schema class this path belongs to
            field_name: Name of the vector field
            field_def: VectorField definition
            parent: Parent path term (if nested)
        """
        super().__init__()
        self.schema_class = schema_class
        self.field_name = field_name
        self.field_def = field_def
        self.parent = parent

        # Metadata - Vector uses ListView
        from redwood.tree.view import ListView

        self.meta.view_type = ListView

        if field_def.is_primitive:
            self.meta.primitive_type = field_def.item_type
        else:
            self.meta.schema = field_def.item_type

        # Path resolution - handle dynamic parents
        if parent and parent.meta.has_dynamic_components:
            self.meta.has_dynamic_components = True
            self.meta.resolved_path = None
        elif parent and parent.meta.resolved_path:
            self.meta.resolved_path = (*parent.meta.resolved_path, field_name)
            self.meta.has_dynamic_components = False
        else:
            self.meta.resolved_path = (field_name,)
            self.meta.has_dynamic_components = False

    def __getitem__(self, index: int | ValueTerm) -> T:
        """Access item in vector by index (static or dynamic).

        Args:
            index: Vector index - int (static) or ValueTerm (dynamic)

        Returns:
            VectorItemPath for the specific index

        Example:
            # Static index
            User.tags[0]

            # Dynamic index (evaluated at runtime)
            User.tags[User.current_idx.get()]
        """
        # Wrap static indices in LiteralValue
        if isinstance(index, int):
            from redwood.dsl.values import LiteralValue

            index_expr = LiteralValue(index)
            is_static = True
        elif isinstance(index, ValueTerm):
            index_expr = index
            is_static = False
        else:
            raise TypeError(f"Vector index must be int or ValueTerm, got {type(index)}")

        return VectorItemPath(
            vector_path=self,
            index_expr=index_expr,
            is_static_index=is_static,
            item_type=self.field_def.item_type,
            is_primitive=self.field_def.is_primitive,
        )

    def evaluate(self, tree: Tree, ctx: ContextType) -> VectorPath[T]:
        """Evaluate path - returns self (path is the location)."""
        return self

    def resolve_path(self, tree: Tree, ctx: ContextType) -> tuple[str, ...]:
        """Resolve to path segments.

        For dynamic paths, delegates to parent for resolution.
        """
        if self.meta.has_dynamic_components:
            if self.parent:
                parent_resolved = self.parent.resolve_path(tree, ctx)
                return parent_resolved + (self.field_name,)
            return (self.field_name,)
        else:
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
        """String representation."""
        if self.parent:
            return f"{self.parent}.{self.field_name}"
        return f"{self.schema_class.__name__}.{self.field_name}"


class VectorPrimitivePath[T](PathTerm):
    """Path to a vector field - supports dynamic index access.

    This is the TYPE ANNOTATION used in schemas!

    Provides __getitem__ for accessing specific indices in the vector.
    Supports both static indices (integers) and dynamic indices (expressions).

    Example:
        # In schema
        tags: VectorPath[str] = VectorField(str)

        # Static index
        User.tags[0]  # Index known at construction

        # Dynamic index
        User.tags[User.current_idx.get()]  # Index evaluated at runtime
    """

    def __init__(
        self,
        schema_class: type,
        field_name: str,
        field_def: VectorField[T],
        parent: PathTerm | None = None,
    ) -> None:
        """Initialize vector path.

        Args:
            schema_class: Schema class this path belongs to
            field_name: Name of the vector field
            field_def: VectorField definition
            parent: Parent path term (if nested)
        """
        super().__init__()
        self.schema_class = schema_class
        self.field_name = field_name
        self.field_def = field_def
        self.parent = parent

        # Metadata - Vector uses ListView
        from redwood.tree.view import ListView

        self.meta.view_type = ListView

        if field_def.is_primitive:
            self.meta.primitive_type = field_def.item_type
        else:
            self.meta.schema = field_def.item_type

        # Path resolution - handle dynamic parents
        if parent and parent.meta.has_dynamic_components:
            self.meta.has_dynamic_components = True
            self.meta.resolved_path = None
        elif parent and parent.meta.resolved_path:
            self.meta.resolved_path = (*parent.meta.resolved_path, field_name)
            self.meta.has_dynamic_components = False
        else:
            self.meta.resolved_path = (field_name,)
            self.meta.has_dynamic_components = False

    def __getitem__(self, index: int | ValueTerm) -> VectorItemPath[T]:
        """Access item in vector by index (static or dynamic).

        Args:
            index: Vector index - int (static) or ValueTerm (dynamic)

        Returns:
            VectorItemPath for the specific index

        Example:
            # Static index
            User.tags[0]

            # Dynamic index (evaluated at runtime)
            User.tags[User.current_idx.get()]
        """
        # Wrap static indices in LiteralValue
        if isinstance(index, int):
            from redwood.dsl.values import LiteralValue

            index_expr = LiteralValue(index)
            is_static = True
        elif isinstance(index, ValueTerm):
            index_expr = index
            is_static = False
        else:
            raise TypeError(f"Vector index must be int or ValueTerm, got {type(index)}")

        return VectorItemPath(
            vector_path=self,
            index_expr=index_expr,
            is_static_index=is_static,
            item_type=self.field_def.item_type,
            is_primitive=self.field_def.is_primitive,
        )

    def evaluate(self, tree: Tree, ctx: ContextType) -> VectorPath[T]:
        """Evaluate path - returns self (path is the location)."""
        return self

    def resolve_path(self, tree: Tree, ctx: ContextType) -> tuple[str, ...]:
        """Resolve to path segments.

        For dynamic paths, delegates to parent for resolution.
        """
        if self.meta.has_dynamic_components:
            if self.parent:
                parent_resolved = self.parent.resolve_path(tree, ctx)
                return parent_resolved + (self.field_name,)
            return (self.field_name,)
        else:
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
        """String representation."""
        if self.parent:
            return f"{self.parent}.{self.field_name}"
        return f"{self.schema_class.__name__}.{self.field_name}"


class VectorItemPath[T](PathTerm):
    """Path to a specific item in a vector (with dynamic index).

    Supports both static and dynamic indices:
    - Static: Index known at construction (integer literal)
    - Dynamic: Index evaluated at runtime (expression)

    Behavior depends on item type:
    - Primitives: Provides .get()/.set()
    - Schemas: Provides __getattribute__ for field navigation

    Example:
        # Static index + primitive
        item = User.tags[0]  # VectorItemPath[str]
        value = item.get().evaluate(tree, ctx)

        # Dynamic index + schema
        item = User.orders[User.current_idx.get()]  # VectorItemPath[Order]
        volume = item.volume.get().evaluate(tree, ctx)
    """

    def __init__(
        self,
        vector_path: VectorPath[T],
        index_expr: ValueTerm,
        is_static_index: bool,
        item_type: type[T],
        is_primitive: bool,
    ) -> None:
        """Initialize vector item path.

        Args:
            vector_path: Parent VectorPath
            index_expr: Index expression (LiteralValue for static, any ValueTerm for dynamic)
            is_static_index: Whether index is known at construction time
            item_type: Type of the item
            is_primitive: Whether item is primitive or schema
        """
        super().__init__()
        self.vector_path = vector_path
        self.index_expr = index_expr
        self.is_static_index = is_static_index
        self.item_type = item_type
        self.is_primitive = is_primitive

        # Metadata
        from redwood.tree.view import ListView

        self._parent_view_type = ListView

        if is_primitive:
            self.meta.primitive_type = item_type
        else:
            self.meta.schema = item_type

        # Mark as dynamic if index is not static OR parent is dynamic
        parent_is_dynamic = vector_path.meta.has_dynamic_components
        self.meta.has_dynamic_components = not is_static_index or parent_is_dynamic

        # Path resolution - append index if static and parent is static
        if is_static_index and not parent_is_dynamic:
            # Static index with static parent - resolve now
            from redwood.dsl.values import LiteralValue

            if isinstance(index_expr, LiteralValue):
                static_index = index_expr.value
                if vector_path.meta.resolved_path:
                    self.meta.resolved_path = (*vector_path.meta.resolved_path, static_index)
                else:
                    self.meta.resolved_path = (static_index,)
        else:
            # Dynamic - cannot resolve statically
            self.meta.resolved_path = None

    def get(self) -> ListGetOperation[T]:
        """Create read operation (primitives only).

        Uses ListView-specific ListGetOperation with integer indices.

        Raises:
            AttributeError: If item is schema (must navigate fields first)
        """
        if not self.is_primitive:
            raise AttributeError(
                f"Cannot call .get() on schema vector item. "
                f"Navigate to a field first: {self}.field_name.get()"
            )

        return ListGetOperation(self)

    def set(self, value: T) -> ListSetOperation:
        """Create write operation (primitives only).

        Uses ListView-specific ListSetOperation with integer indices.

        Raises:
            AttributeError: If item is schema (must navigate fields first)
        """
        if not self.is_primitive:
            raise AttributeError(
                f"Cannot call .set() on schema vector item. "
                f"Navigate to a field first: {self}.field_name.set(value)"
            )

        return ListSetOperation(self, value)

    def __getattribute__(self, name: str) -> T:
        """Navigate to nested schema fields (schemas only).

        Args:
            name: Field name to access

        Returns:
            PathTerm for the nested field (typed as T for IDE support)

        Raises:
            AttributeError: If item is primitive or field doesn't exist
        """
        # Allow access to internal attributes
        if name in [
            "meta",
            "evaluate",
            "vector_path",
            "index_expr",
            "is_static_index",
            "item_type",
            "is_primitive",
            "resolve_path",
            "parent_path",
            "last_segment",
            "get",
            "set",
            "_parent_view_type",
        ]:
            return object.__getattribute__(self, name)

        # Check if this is a primitive item
        is_prim = object.__getattribute__(self, "is_primitive")
        if is_prim:
            raise AttributeError(
                f"VectorItemPath of primitive type has no field '{name}'. "
                f"Use .get() to read the value."
            )

        # Get nested schema
        schema_type = object.__getattribute__(self, "item_type")
        if schema_type and hasattr(schema_type, "_fields"):
            fields = schema_type._fields
            if name in fields:
                # Found field in nested schema
                field_def = fields[name]

                # Delegate to field's create_path_term for extensibility

                return field_def.create_path_term(
                    schema_class=schema_type,
                    field_name=name,
                    parent=self,
                )

        # Not a schema field
        raise AttributeError(
            f"VectorItemPath[{schema_type.__name__ if schema_type else '?'}] has no field '{name}'"
        )

    def evaluate(self, tree: Tree, ctx: ContextType) -> VectorItemPath[T]:
        """Evaluate path - returns self (path is the location)."""
        return self

    def resolve_path(self, tree: Tree, ctx: ContextType) -> tuple[str | int, ...]:
        """Resolve to path segments.

        For dynamic indices, evaluates the index expression at runtime.
        Returns indices as STRINGS (for storage key compatibility).

        Args:
            tree: Tree instance for evaluation
            ctx: Context for evaluation

        Returns:
            Tuple of path segments with evaluated index (as string)
        """
        # Evaluate index expression to get actual index
        actual_index = self.index_expr.evaluate(tree, ctx)

        # Handle special values
        from redwood.dsl.types import is_special

        if is_special(actual_index):
            raise ValueError(f"Vector index evaluated to special value: {actual_index}")

        # Convert to string for path segments (storage compatibility)
        # Operations will convert back to int when needed
        index_str = int(actual_index)

        # Append to parent path
        parent_resolved = self.vector_path.resolve_path(tree, ctx)
        return parent_resolved + (index_str,)

    def parent_path(self) -> PathTerm | None:
        """Get parent path (the vector itself)."""
        return self.vector_path

    def last_segment(self) -> str | int:
        """Get last segment.

        For dynamic indices, this requires evaluation context,
        so we return a placeholder.
        """
        if self.is_static_index:
            from redwood.dsl.values import LiteralValue

            if isinstance(self.index_expr, LiteralValue):
                return self.index_expr.value
        return "<dynamic_index>"

    def __repr__(self) -> str:
        """String representation."""
        if self.is_static_index:
            from redwood.dsl.values import LiteralValue

            if isinstance(self.index_expr, LiteralValue):
                return f"{self.vector_path}[{self.index_expr.value}]"
        return f"{self.vector_path}[<dynamic>]"
