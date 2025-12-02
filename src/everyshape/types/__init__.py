"""EveryShape ABC (Abstract Base Classes) module.

This module defines the abstract base classes (ABCs).
These ABCs provide a common types, interfaces and set of behaviors for various components within the framework.
"""

from __future__ import annotations

from .capabilities import (
    Appendable,
    Assignable,
    Clearable,
    Containable,
    Convertible,
    Deletable,
    Initializable,
    Nestable,
    Sizeable,
    Subscriptable,
    is_appendable,
    is_assignable,
    is_clearable,
    is_containable,
    is_convertible,
    is_deletable,
    is_initializable,
    is_nestable,
    is_sizeable,
    is_subscriptable,
)
from .collections import (
    Collection,
    Container,
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Sequence,
    Set,
)
from .primitive import (
    CompositeValue,
    IterableValues,
    PrimitiveValue,
    Value,
    cast_value,
)
from .special import (
    EMPTY,
    NAN,
    Empty,
    NaN,
    SpecialValue,
    is_empty,
    is_nan,
    is_special,
    propagate_special,
)


__all__ = [  # noqa: RUF022
    # Base types
    "CompositeValue",
    "PrimitiveValue",
    "Value",
    "IterableValues",
    "cast_value",
    # Special sentinels
    "EMPTY",
    "NAN",
    "Empty",
    "NaN",
    "SpecialValue",
    "is_empty",
    "is_nan",
    "is_special",
    "propagate_special",
    # Capabilities
    "Appendable",
    "Assignable",
    "Clearable",
    "Containable",
    "Convertible",
    "Deletable",
    "Initializable",
    "Nestable",
    "Sizeable",
    "Subscriptable",
    "is_appendable",
    "is_assignable",
    "is_clearable",
    "is_containable",
    "is_convertible",
    "is_deletable",
    "is_initializable",
    "is_nestable",
    "is_sizeable",
    "is_subscriptable",
    # Collection protocols
    "Collection",
    "Container",
    "Mapping",
    "MutableMapping",
    "MutableSequence",
    "MutableSet",
    "Sequence",
    "Set",
]
