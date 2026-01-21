"""Term system - semantic contracts for executable nodes.

This module provides the core abstractions for the execution model:

    Term                        - executable node
    ├── LValue                  - addressable location (has path)
    │   └── Ref                 - typed reference to storage location
    └── RValue                  - evaluable expression (has children)
        └── Morphism            - transformation (maps inputs to outputs)
            └── NAryMorphism    - morphism with operands and children management
                ├── UnaryMorphism   - single operand (e.g., -x, abs(x))
                ├── BinaryMorphism  - two operands (e.g., x + y, x > y)
                └── TernaryMorphism - three operands (e.g., if a then b else c)

Purity mixins (orthogonal to arity):
    - Operation: pure computation (no side effects)
    - Command: impure mutation (has side effects)

Protocols:
    - Gettable[T]: objects that support value extraction via get()
"""

from __future__ import annotations

from .context import Context
from .morphism import (
    BinaryMorphism,
    Command,
    Morphism,
    NAryMorphism,
    Operation,
    TernaryMorphism,
    UnaryMorphism,
)
from .ref import Gettable, Ref
from .shape import Shape, ShapeMeta, Slot, SlotDescriptor
from .term import (
    LValue,
    RValue,
    Term,
)


__all__ = [  # noqa: RUF022
    # Term hierarchy
    "Term",
    "LValue",
    "RValue",
    # References
    "Ref",
    # Morphisms
    "Morphism",
    "NAryMorphism",
    "UnaryMorphism",
    "BinaryMorphism",
    "TernaryMorphism",
    # Purity mixins
    "Operation",
    "Command",
    # Protocols
    "Gettable",
    # Context
    "Context",
    # Shapes
    "Shape",
    "ShapeMeta",
    "Slot",
    "SlotDescriptor",
]
