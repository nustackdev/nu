"""DSL Extensions - Additional field types and paths.

Provides extended field types beyond core SchemaField and PrimitiveField:
- CollectionField: Hashtable of any type (homogeneous, uses DictView)
- VectorField: Ordered collection of any type (homogeneous, uses ListView)
- DictField: Hashtable of primitives (legacy, use CollectionField)
- ListField: Ordered list (legacy, use VectorField)

Example:
    from redwood.dsl.extensions import CollectionField, VectorField

    class Market(Schema):
        orders: CollectionPath[Order] = CollectionField(Order)

    class User(Schema):
        tags: VectorPath[str] = VectorField(str)
"""

# Collection extension (hashtable with DictView)
from redwood.dsl.extensions.collection import (
    CollectionField,
    CollectionItemPath,
    CollectionPath,
)

# Vector extension (ordered with ListView)
from redwood.dsl.extensions.vector import (
    ListGetOperation,
    ListSetOperation,
    VectorField,
    VectorItemPath,
    VectorPath,
)


__all__ = [  # noqa: RUF022
    # Collection (hashtable, DictView)
    "CollectionField",
    "CollectionItemPath",
    "CollectionPath",
    # Vector (ordered, ListView)
    "VectorField",
    "VectorItemPath",
    "VectorPath",
    "ListGetOperation",
    "ListSetOperation",
]
