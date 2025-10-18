"""Collection extension - Homogeneous associative array (hashtable).

CollectionField: Hashtable where all values are the same type (homogeneous)
CollectionPath: Container-level path (type annotation in schema)
CollectionItemPath: Item-level path with dynamic key access

Supports ANY type:
- Primitives: Collection[int], Collection[str], Collection[float]
- Schemas: Collection[Order], Collection[Profile]
- Nested: Collection[List[Order]] (future)

Supports DYNAMIC KEYS:
- Static: Market.orders["AAPL"]
- Dynamic: Market.orders[Market.current.get()]

Example:
    class Order(Schema):
        volume: PrimitivePath[int] = PrimitiveField(int)
        price: PrimitivePath[float] = PrimitiveField(float)

    class Market(Schema):
        current: PrimitivePath[str] = PrimitiveField(str)
        orders: CollectionPath[Order] = CollectionField(Order)
        prices: CollectionPath[float] = CollectionField(float)

    # Static key
    Market.orders["AAPL"].volume.get()

    # Dynamic key
    Market.orders[Market.current.get()].volume.get()
"""

from typing import TYPE_CHECKING, TypeVar

from redwood.dsl.schema import Field
from redwood.dsl.term import PathTerm, ValueTerm


if TYPE_CHECKING:
    from redwood.dsl.operations import GetOperation, SetOperation
    from redwood.tree.context import ContextType
    from redwood.tree.tree import Tree


T = TypeVar("T")  # Item type (any type)


class CollectionField[T](Field):
    """Hashtable field with homogeneous values of ANY type.

    All values in the collection must be the same type, but that type
    can be anything: primitives, schemas, or nested structures.

    Access via dynamic keys: path["key"] or path[expr]

    Example:
        class Market(Schema):
            # Schema collection
            orders: CollectionPath[Order] = CollectionField(Order)
            # Primitive collection
            prices: CollectionPath[float] = CollectionField(float)
    """

    def __init__(self, item_type: type[T]) -> None:
        """Initialize collection field.

        Args:
            item_type: Type of items in collection (any type)
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
        """Create CollectionPath for hashtable access."""
        return CollectionPath(
            schema_class=schema_class,
            field_name=field_name,
            field_def=self,
            parent=parent,
        )


class CollectionPath[T](PathTerm):
    """Path to a collection field - supports dynamic key access.

    This is the TYPE ANNOTATION used in schemas!

    Provides __getitem__ for accessing specific keys in the collection.
    Supports both static keys (strings) and dynamic keys (expressions).

    Example:
        # In schema
        orders: CollectionPath[Order] = CollectionField(Order)

        # Static key
        Market.orders["AAPL"]  # Key known at construction

        # Dynamic key
        Market.orders[Market.current.get()]  # Key evaluated at runtime
    """

    def __init__(
        self,
        schema_class: type,
        field_name: str,
        field_def: CollectionField[T],
        parent: PathTerm | None = None,
    ) -> None:
        """Initialize collection path.

        Args:
            schema_class: Schema class this path belongs to
            field_name: Name of the collection field
            field_def: CollectionField definition
            parent: Parent path term (if nested)
        """
        super().__init__()
        self.schema_class = schema_class
        self.field_name = field_name
        self.field_def = field_def
        self.parent = parent

        # Metadata
        from redwood.tree.view import DictView

        self.meta.view_type = DictView

        if field_def.is_primitive:
            self.meta.primitive_type = field_def.item_type
        else:
            self.meta.schema = field_def.item_type

        # Path resolution
        if parent and parent.meta.resolved_path:
            self.meta.resolved_path = (*parent.meta.resolved_path, field_name)
        else:
            self.meta.resolved_path = (field_name,)

    def __getitem__(self, key: str | ValueTerm) -> T:
        """Access item in collection by key (static or dynamic).

        Args:
            key: Collection key - string (static) or ValueTerm (dynamic)

        Returns:
            CollectionItemPath for the specific key

        Example:
            # Static key
            Market.orders["AAPL"]

            # Dynamic key (evaluated at runtime)
            Market.orders[Market.current.get()]
        """
        # Wrap static keys in LiteralValue
        if isinstance(key, str):
            from redwood.dsl.values import LiteralValue

            key_expr = LiteralValue(key)
            is_static = True
        elif isinstance(key, ValueTerm):
            key_expr = key
            is_static = False
        else:
            raise TypeError(f"Collection key must be str or ValueTerm, got {type(key)}")

        return CollectionItemPath(
            collection_path=self,
            key_expr=key_expr,
            is_static_key=is_static,
            item_type=self.field_def.item_type,
            is_primitive=self.field_def.is_primitive,
        )

    def evaluate(self, tree: "Tree", ctx: "ContextType") -> "CollectionPath[T]":
        """Evaluate path - returns self (path is the location)."""
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
        """String representation."""
        if self.parent:
            return f"{self.parent}.{self.field_name}"
        return f"{self.schema_class.__name__}.{self.field_name}"


class CollectionItemPath[T](PathTerm):
    """Path to a specific item in a collection (with dynamic key).

    Supports both static and dynamic keys:
    - Static: Key known at construction (string literal)
    - Dynamic: Key evaluated at runtime (expression)

    Behavior depends on item type:
    - Primitives: Provides .get()/.set()
    - Schemas: Provides __getattribute__ for field navigation

    Example:
        # Static key + primitive
        item = Market.prices["AAPL"]  # CollectionItemPath[float]
        value = item.get().evaluate(tree, ctx)

        # Dynamic key + schema
        item = Market.orders[Market.current.get()]  # CollectionItemPath[Order]
        volume = item.volume.get().evaluate(tree, ctx)
    """

    def __init__(
        self,
        collection_path: CollectionPath[T],
        key_expr: ValueTerm,
        is_static_key: bool,
        item_type: type[T],
        is_primitive: bool,
    ) -> None:
        """Initialize collection item path.

        Args:
            collection_path: Parent CollectionPath
            key_expr: Key expression (LiteralValue for static, any ValueTerm for dynamic)
            is_static_key: Whether key is known at construction time
            item_type: Type of the item
            is_primitive: Whether item is primitive or schema
        """
        super().__init__()
        self.collection_path = collection_path
        self.key_expr = key_expr
        self.is_static_key = is_static_key
        self.item_type = item_type
        self.is_primitive = is_primitive

        # Metadata
        from redwood.tree.view import DictView

        self._parent_view_type = DictView

        if is_primitive:
            self.meta.primitive_type = item_type
        else:
            self.meta.schema = item_type

        # Mark as dynamic if key is not static
        self.meta.has_dynamic_components = not is_static_key

        # Path resolution - append key if static, otherwise defer
        if is_static_key:
            # Static key - resolve now
            from redwood.dsl.values import LiteralValue

            if isinstance(key_expr, LiteralValue):
                static_key = key_expr.value
                if collection_path.meta.resolved_path:
                    self.meta.resolved_path = (*collection_path.meta.resolved_path, static_key)
                else:
                    self.meta.resolved_path = (static_key,)
        else:
            # Dynamic key - cannot resolve statically
            self.meta.resolved_path = None

    def get(self) -> "GetOperation[T]":
        """Create read operation (primitives only).

        Raises:
            AttributeError: If item is schema (must navigate fields first)
        """
        if not self.is_primitive:
            raise AttributeError(
                f"Cannot call .get() on schema collection item. "
                f"Navigate to a field first: {self}.field_name.get()"
            )

        from redwood.dsl.operations import GetOperation

        return GetOperation(self, self._parent_view_type)

    def set(self, value: T) -> "SetOperation":
        """Create write operation (primitives only).

        Raises:
            AttributeError: If item is schema (must navigate fields first)
        """
        if not self.is_primitive:
            raise AttributeError(
                f"Cannot call .set() on schema collection item. "
                f"Navigate to a field first: {self}.field_name.set(value)"
            )

        from redwood.dsl.operations import SetOperation

        return SetOperation(self, value, self._parent_view_type)

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
            "collection_path",
            "key_expr",
            "is_static_key",
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
                f"CollectionItemPath of primitive type has no field '{name}'. "
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
            f"CollectionItemPath[{schema_type.__name__ if schema_type else '?'}] "
            f"has no field '{name}'"
        )

    def evaluate(self, tree: "Tree", ctx: "ContextType") -> "CollectionItemPath[T]":
        """Evaluate path - returns self (path is the location)."""
        return self

    def resolve_path(self, tree: "Tree", ctx: "ContextType") -> tuple[str, ...]:
        """Resolve to path segments.

        For dynamic keys, evaluates the key expression at runtime.

        Args:
            tree: Tree instance for evaluation
            ctx: Context for evaluation

        Returns:
            Tuple of path segments with evaluated key
        """
        # Evaluate key expression to get actual key
        actual_key = self.key_expr.evaluate(tree, ctx)

        # Handle special values
        from redwood.dsl.types import is_special

        if is_special(actual_key):
            raise ValueError(f"Collection key evaluated to special value: {actual_key}")

        # Convert to string
        key_str = str(actual_key)

        # Append to parent path
        parent_resolved = self.collection_path.resolve_path(tree, ctx)
        return (*parent_resolved, key_str)

    def parent_path(self) -> PathTerm | None:
        """Get parent path (the collection itself)."""
        return self.collection_path

    def last_segment(self) -> str:
        """Get last segment.

        For dynamic keys, this requires evaluation context,
        so we return a placeholder.
        """
        if self.is_static_key:
            from redwood.dsl.values import LiteralValue

            if isinstance(self.key_expr, LiteralValue):
                return str(self.key_expr.value)
        return "<dynamic_key>"

    def __repr__(self) -> str:
        """String representation."""
        if self.is_static_key:
            from redwood.dsl.values import LiteralValue

            if isinstance(self.key_expr, LiteralValue):
                return f'{self.collection_path}["{self.key_expr.value}"]'
        return f"{self.collection_path}[<dynamic>]"
