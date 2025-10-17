"""Schema system for DSL.

Defines structure of tree data using Field types and Schema classes.
Core fields: SchemaField (nested schemas), PrimitiveField (leaf values).
Extensions can define additional field types.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from redwood.dsl.exceptions import DSLSchemaError


if TYPE_CHECKING:
    from redwood.dsl.term import PathTerm


T = TypeVar("T")


class Field(ABC, Generic[T]):
    """Abstract base field - defines structure and path creation.

    Each field type must implement create_path_term() to specify
    how it creates its corresponding PathTerm. This enables
    extensibility - new field types just extend Field.
    """

    @abstractmethod
    def create_path_term(
        self,
        schema_class: type,
        field_name: str,
        parent: "PathTerm | None" = None,
    ) -> "PathTerm":
        """Create PathTerm for this field.

        Args:
            schema_class: Schema class this field belongs to
            field_name: Name of this field
            parent: Parent path (for nested access)

        Returns:
            PathTerm appropriate for this field type
        """
        pass


class SchemaField(Field[T]):
    """Nested document field - embeds another schema.

    Core field type for schema composition. Uses DictView internally.

    Example:
        class User(Schema):
            profile: Profile = SchemaField(Profile)

        user.profile  # DocumentPath[Profile]
    """

    def __init__(self, schema: type[T]) -> None:
        """Initialize schema field.

        Args:
            schema: Schema class for nested structure
        """
        self.schema: type[T] = schema

    def create_path_term(
        self,
        schema_class: type,
        field_name: str,
        parent: "PathTerm | None" = None,
    ) -> "PathTerm":
        """Create DocumentPath for nested schema."""
        from redwood.dsl.paths import DocumentPath

        return DocumentPath(
            schema_class=schema_class,
            field_name=field_name,
            field_def=self,
            parent=parent,
        )


class PrimitiveField(Field[T]):
    """Primitive value field - leaf nodes.

    Core field type for primitive values (int, str, float, bool, etc.).

    Example:
        class User(Schema):
            age: int = PrimitiveField(int)

        user.age  # PrimitivePath[int]
    """

    def __init__(self, primitive_type: type[T]) -> None:
        """Initialize primitive field.

        Args:
            primitive_type: Python type (int, str, float, bool, bytes, dict, list)

        Raises:
            DSLSchemaError: If primitive_type is not a valid primitive
        """
        allowed_primitives = (int, float, str, bool, bytes, dict, list)
        if primitive_type not in allowed_primitives:
            raise DSLSchemaError(
                f"Invalid primitive type: {primitive_type}. Must be one of {allowed_primitives}"
            )

        self.primitive_type: type[T] = primitive_type

    def create_path_term(
        self,
        schema_class: type,
        field_name: str,
        parent: "PathTerm | None" = None,
    ) -> "PathTerm":
        """Create PrimitivePath for primitive value."""
        from redwood.dsl.paths import PrimitivePath

        return PrimitivePath(
            schema_class=schema_class,
            field_name=field_name,
            field_def=self,
            parent=parent,
        )


class FieldDescriptor(Generic[T]):
    """Descriptor that delegates PathTerm creation to Field.

    This is the bridge between Schema class attributes and PathTerms.
    Extensible - just calls field.create_path_term(), no hardcoded logic.
    """

    def __init__(self, name: str, field_def: Field[T]) -> None:
        """Initialize descriptor.

        Args:
            name: Field name
            field_def: Field definition
        """
        self.name: str = name
        self.field_def: Field[T] = field_def

    def __get__(
        self,
        obj: "Schema | None",
        objtype: type["Schema"] | None = None,
    ) -> "PathTerm":
        """Get PathTerm for this field.

        Delegates to field.create_path_term() for extensibility.

        Args:
            obj: Schema instance (unused - we work at class level)
            objtype: Schema class

        Returns:
            PathTerm created by the field

        Raises:
            TypeError: If accessed without schema class
        """
        if objtype is None:
            raise TypeError("FieldDescriptor requires schema class")

        # Delegate to field - no hardcoded logic!
        return self.field_def.create_path_term(
            schema_class=objtype,
            field_name=self.name,
            parent=None,
        )

    def __set__(self, obj: Any, value: Any) -> None:
        """Prevent setting field values."""
        raise AttributeError(f"Cannot set field '{self.name}' - fields are read-only")


class SchemaMeta(type):
    """Metaclass that collects Field definitions into _fields dict.

    Processes class definition at creation time:
    1. Collects fields from base classes
    2. Collects fields from current class
    3. Replaces Field instances with FieldDescriptors
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
    ) -> type:
        """Create schema class with field processing.

        Args:
            name: Class name
            bases: Base classes
            namespace: Class namespace

        Returns:
            New schema class with processed fields
        """
        fields: dict[str, Field] = {}

        # Collect fields from base classes
        for base in bases:
            if hasattr(base, "_fields"):
                fields.update(base._fields)

        # Collect fields from current class annotations
        annotations = namespace.get("__annotations__", {})
        for key in annotations:
            value = namespace.get(key)
            if isinstance(value, Field):
                fields[key] = value

        # Store fields
        namespace["_fields"] = fields

        # Create class
        cls = super().__new__(mcs, name, bases, namespace)

        # Replace Field instances with FieldDescriptors
        for key, field_def in fields.items():
            setattr(cls, key, FieldDescriptor(key, field_def))

        return cls


class Schema(metaclass=SchemaMeta):
    """Base class for schema definitions.

    Schemas define pure structure without domain semantics.
    They describe how data is organized in the tree.

    Example:
        class User(Schema):
            id: int = PrimitiveField(int)
            name: str = PrimitiveField(str)
            profile: Profile = SchemaField(Profile)
    """

    _fields: dict[str, Field] = {}

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
