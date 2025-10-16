"""Schema system for DSL.

Schemas define pure structure (no domain semantics):
- Primitive fields: leaf values (int, float, str, bool, bytes, dict, list)
- Container fields: views with optional nested schemas

Schema is separate from domain types - it only describes storage structure.
"""

from __future__ import annotations

from typing import Any, ClassVar

from redwood.dsl.exceptions import DSLSchemaError


__all__ = ["Field", "Schema"]


class Field:
    """Field definition in a schema.

    A field must be either:
    - A primitive: Field(primitive=int)
    - A container: Field(view=DictView, schema=NestedSchema)  # optional schema
    - A container without schema: Field(view=DictView)

    But never both primitive and view.

    Attributes:
        primitive: Python type for primitive fields (int, float, str, bool, bytes, dict, list)
        view: View class for container fields (DictView, ListView, etc.)
        schema: Nested schema for typed containers (optional)
    """

    def __init__(
        self,
        *,
        primitive: type | None = None,
        view: type | None = None,
        schema: type[Schema] | None = None,
    ) -> None:
        """Initialize field definition.

        Args:
            primitive: Primitive type (mutually exclusive with view)
            view: View class for containers (mutually exclusive with primitive)
            schema: Nested schema (only valid with view)

        Raises:
            DSLSchemaError: If field definition is invalid
        """
        # Validate mutual exclusion
        if primitive is not None and view is not None:
            msg = "Field cannot have both primitive and view"
            raise DSLSchemaError(msg)

        if primitive is None and view is None:
            msg = "Field must have either primitive or view"
            raise DSLSchemaError(msg)

        # Validate schema only with view
        if schema is not None and view is None:
            msg = "Field schema can only be specified with view"
            raise DSLSchemaError(msg)

        # Validate primitive type
        if primitive is not None:
            allowed_primitives = (int, float, str, bool, bytes, dict, list)
            if primitive not in allowed_primitives:
                msg = f"Invalid primitive type: {primitive}. Must be one of {allowed_primitives}"
                raise DSLSchemaError(msg)

        self.primitive = primitive
        self.view = view
        self.schema = schema

    def is_primitive(self) -> bool:
        """Check if field is a primitive.

        Returns:
            True if field is primitive
        """
        return self.primitive is not None

    def is_container(self) -> bool:
        """Check if field is a container.

        Returns:
            True if field is container (has view)
        """
        return self.view is not None

    def has_schema(self) -> bool:
        """Check if container field has nested schema.

        Returns:
            True if field is container with schema
        """
        return self.schema is not None

    def __repr__(self) -> str:
        """Return string representation."""
        if self.is_primitive():
            return f"Field(primitive={self.primitive.__name__})"
        if self.has_schema():
            return f"Field(view={self.view.__name__}, schema={self.schema.__name__})"
        return f"Field(view={self.view.__name__})"


class SchemaMeta(type):
    """Metaclass for Schema to enable attribute-based field access.

    This metaclass processes Field definitions at class creation time and
    provides proper descriptor behavior for IDE type hints.
    """

    def __new__(mcs, name: str, bases: tuple[type, ...], namespace: dict[str, Any]) -> type:
        """Create new schema class.

        Args:
            name: Class name
            bases: Base classes
            namespace: Class namespace

        Returns:
            New schema class
        """
        # Extract fields from namespace
        fields: dict[str, Field] = {}
        for attr_name, attr_value in namespace.items():
            if isinstance(attr_value, Field):
                fields[attr_name] = attr_value

        # Store fields in class
        namespace["_fields"] = fields

        # Create class
        cls = super().__new__(mcs, name, bases, namespace)

        return cls


class Schema(metaclass=SchemaMeta):
    """Base class for schema definitions.

    Schemas define pure structure without domain semantics. They describe
    how data is organized (primitives, containers, nesting) but not what
    operations are valid on that data.

    Examples:
        >>> class User(Schema):
        ...     name = Field(primitive=str)
        ...     age = Field(primitive=int)
        ...     orders = Field(view=DictView, schema=Order)
        >>> # Access generates PathTerms
        >>> user_age = User.age  # PathTerm for User.age
        >>> order = User.orders["AAPL"]  # PathTerm for User.orders["AAPL"]
    """

    _fields: ClassVar[dict[str, Field]]

    def __init_subclass__(cls) -> None:
        """Hook for subclass initialization.

        Validates schema definition and sets up field descriptors.
        """
        super().__init_subclass__()

        # Fields are already processed by metaclass
        # Additional validation can go here if needed

    @classmethod
    def get_field(cls, name: str) -> Field | None:
        """Get field definition by name.

        Args:
            name: Field name

        Returns:
            Field definition, or None if not found
        """
        return cls._fields.get(name)

    @classmethod
    def get_fields(cls) -> dict[str, Field]:
        """Get all field definitions.

        Returns:
            Dictionary of field name to Field definition
        """
        return cls._fields.copy()

    @classmethod
    def has_field(cls, name: str) -> bool:
        """Check if schema has field with given name.

        Args:
            name: Field name

        Returns:
            True if field exists
        """
        return name in cls._fields

    def __class_getitem__(cls, name: str) -> Any:
        """Enable schema["key"] access for dynamic fields.

        This is used for container access where keys are not known at schema
        definition time.

        Args:
            name: Key name

        Returns:
            PathTerm for indexed access
        """
        # Import here to avoid circular dependency
        from redwood.dsl.paths import IndexPath, RootPath

        root = RootPath(cls.__name__, schema=cls)
        return IndexPath(root, name)

    def __repr__(self) -> str:
        """Return string representation."""
        field_strs = [f"{name}={field!r}" for name, field in self._fields.items()]
        fields_repr = ", ".join(field_strs)
        return f"{self.__class__.__name__}({fields_repr})"
